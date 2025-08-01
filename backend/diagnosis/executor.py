import asyncio
import time
import logging
import os
import uuid
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import cv2
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.diagnosis import (
    DiagnosisTask, DiagnosisResult, DiagnosisAlarm,
    DiagnosisType, DiagnosisStatus, TaskStatus
)
from models.camera import Camera, CameraStatus
from utils.minio_client import MinioClient
from diagnosis.algorithms import get_algorithm
from database import get_db

logger = logging.getLogger(__name__)

class DiagnosisExecutor:
    """诊断任务执行器"""
    
    def __init__(self):
        self.running_tasks = set()
        
    async def execute_task(self, task_id: int, db: AsyncSession) -> Dict[str, Any]:
        """执行诊断任务"""
        if task_id in self.running_tasks:
            return {"error": "任务已在运行中"}
            
        self.running_tasks.add(task_id)
        
        try:
            # 获取任务信息
            result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == task_id))
            task = result.scalar_one_or_none()
            
            if not task:
                return {"error": "任务不存在"}
                
            if not task.is_active:
                return {"error": "任务未启用"}
                
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.last_run_time = datetime.utcnow()
            task.total_runs += 1
            await db.commit()
            
            logger.info(f"开始执行诊断任务: {task.name} (ID: {task_id})")
            
            # 获取摄像头列表
            cameras = await self._get_task_cameras(task, db)
            
            if not cameras:
                await self._update_task_status(task, TaskStatus.FAILED, "没有找到可用的摄像头", db)
                return {"error": "没有找到可用的摄像头"}
                
            # 执行诊断
            results = []
            success_count = 0
            error_count = 0
            
            for camera in cameras:
                try:
                    camera_results = await self._diagnose_camera(task, camera, db)
                    results.extend(camera_results)
                    
                    # 统计结果
                    for result in camera_results:
                        if result.get('status') == DiagnosisStatus.NORMAL:
                            success_count += 1
                        else:
                            error_count += 1
                            
                except Exception as e:
                    logger.error(f"摄像头 {camera.name} 诊断失败: {str(e)}")
                    error_count += 1
                    
            # 更新任务统计
            task.success_runs += success_count
            if error_count > 0:
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.COMPLETED
                
            await db.commit()
            
            logger.info(f"诊断任务完成: {task.name}, 成功: {success_count}, 失败: {error_count}")
            
            return {
                "success": True,
                "results_count": len(results),
                "success_count": success_count,
                "error_count": error_count
            }
            
        except Exception as e:
            logger.error(f"执行诊断任务失败: {str(e)}\n{traceback.format_exc()}")
            
            # 更新任务状态为失败
            try:
                result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == task_id))
                task = result.scalar_one_or_none()
                if task:
                    await self._update_task_status(task, TaskStatus.FAILED, str(e), db)
            except Exception:
                pass
                
            return {"error": str(e)}
            
        finally:
            self.running_tasks.discard(task_id)
            
    async def _get_task_cameras(self, task: DiagnosisTask, db: AsyncSession) -> List[Camera]:
        """获取任务关联的摄像头"""
        cameras = []
        
        # 根据摄像头ID获取
        if task.camera_ids:
            result = await db.execute(
                select(Camera).where(
                    Camera.id.in_(task.camera_ids),
                    Camera.is_active == True
                )
            )
            cameras.extend(result.scalars().all())
            
        # 根据摄像头组获取（如果有组功能的话）
        if task.camera_groups:
            # 这里可以扩展组功能
            pass
            
        return cameras
        
    async def _diagnose_camera(self, task: DiagnosisTask, camera: Camera, db: AsyncSession) -> List[Dict[str, Any]]:
        """对单个摄像头执行诊断"""
        results = []
        
        try:
            # 获取摄像头图像
            image = await self._capture_camera_image(camera)
            
            if image is None:
                # 创建错误结果，说明具体原因
                error_msg = self._get_image_error_message(camera)
                result = await self._create_diagnosis_result(
                    task, camera, None, DiagnosisStatus.ERROR,
                    error_message=error_msg, db=db
                )
                results.append(result)
                return results
                
            # 保存图像（如果成功获取）
            image_url, thumbnail_url = None, None
            if image is not None:
                # 使用第一个诊断类型作为图像保存的类型标识
                first_diagnosis_type = task.diagnosis_types[0] if task.diagnosis_types else "unknown"
                image_url, thumbnail_url = await self._save_image(image, camera, first_diagnosis_type)
            
            # 执行各种诊断类型
            for diagnosis_type_str in task.diagnosis_types:
                try:
                    diagnosis_type = DiagnosisType(diagnosis_type_str)
                    
                    # 获取算法配置
                    algorithm_config = task.diagnosis_config.get(diagnosis_type_str, {})
                    
                    # 合并阈值配置到算法配置中
                    if task.threshold_config:
                        # 将threshold_config中的配置合并到algorithm_config的thresholds字段中
                        if 'thresholds' not in algorithm_config:
                            algorithm_config['thresholds'] = {}
                        
                        # 合并通用阈值配置
                        algorithm_config['thresholds'].update(task.threshold_config)
                        
                        # 特殊处理：将前端的threshold配置映射到算法期望的参数名
                        if 'threshold' in task.threshold_config:
                            threshold_value = task.threshold_config['threshold']
                            # 根据诊断类型映射到对应的算法参数
                            if diagnosis_type_str == 'clarity':
                                # 前端threshold是0-1的小数，需要转换为算法期望的数值
                                # 假设前端0.8对应算法的80（基于100的比例）
                                algorithm_config['thresholds']['clarity_min'] = threshold_value * 100
                            elif diagnosis_type_str == 'brightness':
                                algorithm_config['thresholds']['brightness_min'] = threshold_value
                            elif diagnosis_type_str == 'contrast':
                                algorithm_config['thresholds']['contrast_min'] = threshold_value
                            elif diagnosis_type_str == 'noise':
                                algorithm_config['thresholds']['noise_max'] = threshold_value
                        
                        # 如果有特定诊断类型的阈值配置，也进行合并
                        type_specific_config = task.threshold_config.get(diagnosis_type_str, {})
                        if type_specific_config:
                            algorithm_config['thresholds'].update(type_specific_config)
                    
                    # 执行诊断
                    algorithm = get_algorithm(diagnosis_type, algorithm_config)
                    diagnosis_result = algorithm.diagnose(image)
                    
                    # 创建诊断结果记录
                    result = await self._create_diagnosis_result(
                        task, camera, diagnosis_type_str, diagnosis_result['status'],
                        score=diagnosis_result.get('score'),
                        threshold=diagnosis_result.get('threshold'),
                        processing_time=diagnosis_result.get('processing_time'),
                        metrics=diagnosis_result.get('metrics', {}),
                        suggestions=[diagnosis_result.get('message', '')],
                        image_url=image_url,
                        thumbnail_url=thumbnail_url,
                        db=db
                    )
                    
                    results.append(result)
                    
                    # 检查是否需要创建告警
                    if diagnosis_result['status'] in [DiagnosisStatus.WARNING, DiagnosisStatus.ERROR, DiagnosisStatus.CRITICAL]:
                        await self._create_alarm(result, diagnosis_result, task, db)
                        
                except Exception as e:
                    logger.error(f"诊断类型 {diagnosis_type_str} 执行失败: {str(e)}")
                    
                    # 创建错误结果
                    result = await self._create_diagnosis_result(
                        task, camera, diagnosis_type_str, DiagnosisStatus.ERROR,
                        error_message=str(e), 
                        image_url=image_url,
                        thumbnail_url=thumbnail_url,
                        db=db
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"摄像头 {camera.name} 诊断过程失败: {str(e)}")
            raise
            
        return results
        
    async def _capture_camera_image(self, camera: Camera) -> Optional[np.ndarray]:
        """获取摄像头图像"""
        try:
            # 检查摄像头状态
            if camera.status == CameraStatus.OFFLINE:
                logger.warning(f"摄像头 {camera.name} 处于离线状态，无法获取图像")
                return None
                
            if not camera.is_active:
                logger.warning(f"摄像头 {camera.name} 未启用，无法获取图像")
                return None
            
            if not camera.stream_url:
                logger.warning(f"摄像头 {camera.name} 未配置流地址，无法获取图像")
                return None
            
            # 尝试从流URL获取图像
            cap = cv2.VideoCapture(camera.stream_url)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    logger.info(f"成功获取摄像头 {camera.name} 的图像")
                    return frame
                else:
                    logger.warning(f"摄像头 {camera.name} 流连接正常但无法读取帧数据")
            else:
                logger.warning(f"无法连接到摄像头 {camera.name} 的流地址: {camera.stream_url}")
                        
            # 如果无法获取真实图像，返回None而不是创建测试图像
            # 这样可以确保诊断结果的真实性
            logger.error(f"摄像头 {camera.name} 无法获取有效图像")
            return None
            
        except Exception as e:
            logger.error(f"获取摄像头 {camera.name} 图像失败: {str(e)}")
            return None
            
    def _get_image_error_message(self, camera: Camera) -> str:
        """根据摄像头状态生成详细的错误消息"""
        if camera.status == CameraStatus.OFFLINE:
            return f"摄像头 '{camera.name}' 处于离线状态，无法进行诊断"
        elif not camera.is_active:
            return f"摄像头 '{camera.name}' 未启用，请先启用摄像头"
        elif not camera.stream_url:
            return f"摄像头 '{camera.name}' 未配置视频流地址，无法获取图像"
        else:
            return f"摄像头 '{camera.name}' 无法获取有效图像，请检查网络连接和流地址配置"
            
    async def _save_image(self, image: np.ndarray, camera: Camera, diagnosis_type: str) -> tuple[Optional[str], Optional[str]]:
        """保存诊断图像到MinIO并返回URL"""
        try:
            # 从环境变量或配置文件获取MinIO配置
            from config import settings
            
            # 初始化MinIO客户端
            minio_client = MinioClient(
                endpoint=getattr(settings, 'MINIO_ENDPOINT', 'localhost:9000'),
                access_key=getattr(settings, 'MINIO_ACCESS_KEY', 'minioadmin'),
                secret_key=getattr(settings, 'MINIO_SECRET_KEY', 'minioadmin')
            )
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{camera.id}_{diagnosis_type}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
            thumbnail_filename = f"thumb_{filename}"
            
            # 将图像编码为字节
            _, buffer = cv2.imencode('.jpg', image)
            image_bytes = buffer.tobytes()
            
            # 创建缩略图
            height, width = image.shape[:2]
            if width > 200 or height > 150:
                scale = min(200/width, 150/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                thumbnail = cv2.resize(image, (new_width, new_height))
            else:
                thumbnail = image.copy()
                
            _, thumb_buffer = cv2.imencode('.jpg', thumbnail)
            thumbnail_bytes = thumb_buffer.tobytes()
            
            # 上传到MinIO
            bucket_name = "diagnosis-images"
            
            # 确保桶存在
            minio_client.ensure_bucket_exists(bucket_name)
            
            # 上传原图
            image_object_name = f"images/{filename}"
            from io import BytesIO
            image_stream = BytesIO(image_bytes)
            upload_success = minio_client.put_object(
                bucket_name=bucket_name,
                object_name=image_object_name,
                data=image_stream,
                length=len(image_bytes)
            )
            
            if not upload_success:
                raise Exception("原图上传失败")
            
            # 上传缩略图
            thumbnail_object_name = f"thumbnails/{thumbnail_filename}"
            thumbnail_stream = BytesIO(thumbnail_bytes)
            thumb_upload_success = minio_client.put_object(
                bucket_name=bucket_name,
                object_name=thumbnail_object_name,
                data=thumbnail_stream,
                length=len(thumbnail_bytes)
            )
            
            if not thumb_upload_success:
                raise Exception("缩略图上传失败")
            
            # 生成预签名URL（7天有效期）
            image_url = minio_client.get_presigned_url(
                bucket_name=bucket_name,
                object_name=image_object_name,
                expiry=timedelta(days=7)
            )
            
            thumbnail_url = minio_client.get_presigned_url(
                bucket_name=bucket_name,
                object_name=thumbnail_object_name,
                expiry=timedelta(days=7)
            )
            
            logger.info(f"成功保存诊断图像到MinIO: {image_object_name}")
            return image_url, thumbnail_url
            
        except Exception as e:
            logger.error(f"保存诊断图像到MinIO失败: {str(e)}")
            # 如果MinIO失败，回退到本地存储
            return await self._save_image_local(image, camera, diagnosis_type)
            
    async def _save_image_local(self, image: np.ndarray, camera: Camera, diagnosis_type: str) -> tuple[Optional[str], Optional[str]]:
        """本地保存诊断图像（备用方案）"""
        try:
            # 创建保存目录
            base_dir = "static/diagnosis_images"
            date_dir = datetime.now().strftime("%Y/%m/%d")
            save_dir = os.path.join(base_dir, date_dir)
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{camera.id}_{diagnosis_type}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            # 保存原图
            cv2.imwrite(filepath, image)
            
            # 生成缩略图
            thumbnail_filename = f"thumb_{filename}"
            thumbnail_filepath = os.path.join(save_dir, thumbnail_filename)
            
            # 创建缩略图 (200x150)
            height, width = image.shape[:2]
            if width > 200 or height > 150:
                scale = min(200/width, 150/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                thumbnail = cv2.resize(image, (new_width, new_height))
            else:
                thumbnail = image.copy()
                
            cv2.imwrite(thumbnail_filepath, thumbnail)
            
            # 返回相对URL路径
            image_url = f"/static/diagnosis_images/{date_dir}/{filename}"
            thumbnail_url = f"/static/diagnosis_images/{date_dir}/{thumbnail_filename}"
            
            logger.info(f"使用本地存储保存诊断图像: {filepath}")
            return image_url, thumbnail_url
            
        except Exception as e:
            logger.error(f"本地保存诊断图像失败: {str(e)}")
            return None, None
            
    async def _create_diagnosis_result(
        self, task: DiagnosisTask, camera: Camera, diagnosis_type: Optional[str],
        status: DiagnosisStatus, score: Optional[float] = None,
        threshold: Optional[float] = None, processing_time: Optional[float] = None,
        metrics: Optional[Dict] = None, suggestions: Optional[List[str]] = None,
        error_message: Optional[str] = None, image_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None, db: AsyncSession = None
    ) -> Dict[str, Any]:
        """创建诊断结果记录"""
        
        # 处理threshold参数 - 如果是字典类型，转换为单一数值或None
        db_threshold = None
        original_threshold = threshold
        if isinstance(threshold, dict):
            # 对于亮度等有min/max的情况，可以取平均值或者设为None
            # 这里设为None，完整的阈值信息保存在result_data中
            db_threshold = None
        elif isinstance(threshold, (int, float)):
            db_threshold = float(threshold)
        
        result = DiagnosisResult(
            task_id=task.id,
            camera_id=camera.id,
            camera_name=camera.name,
            diagnosis_type=diagnosis_type,
            diagnosis_status=status,
            score=score,
            threshold=db_threshold,
            is_abnormal=status != DiagnosisStatus.NORMAL,
            processing_time=processing_time,
            error_message=error_message,
            suggestions=suggestions or [],
            metrics=metrics or {},
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            result_data={
                'camera_info': {
                    'id': camera.id,
                    'name': camera.name,
                    'location': camera.location
                },
                'diagnosis_info': {
                    'type': diagnosis_type,
                    'status': status.value if status else None,
                    'score': score,
                    'threshold': original_threshold  # 保存原始threshold信息
                }
            }
        )
        
        if db:
            db.add(result)
            await db.commit()
            await db.refresh(result)
            
        return {
            'id': result.id,
            'status': status,
            'score': score,
            'message': error_message or suggestions[0] if suggestions else None
        }
        
    async def _create_alarm(
        self, result_data: Dict[str, Any], diagnosis_result: Dict[str, Any],
        task: DiagnosisTask, db: AsyncSession
    ):
        """创建诊断告警"""
        try:
            alarm = DiagnosisAlarm(
                result_id=result_data['id'],
                alarm_type=diagnosis_result.get('type', 'unknown'),
                severity=self._get_alarm_severity(diagnosis_result['status']),
                title=f"摄像头诊断异常: {diagnosis_result.get('message', '未知错误')}",
                description=f"任务: {task.name}\n" +
                           f"状态: {diagnosis_result['status'].value}\n" +
                           f"分数: {diagnosis_result.get('score', 'N/A')}\n" +
                           f"阈值: {diagnosis_result.get('threshold', 'N/A')}",
                threshold_config={
                    'threshold': diagnosis_result.get('threshold'),
                    'operator': 'lt' if diagnosis_result['status'] == DiagnosisStatus.WARNING else 'gt'
                },
                current_value=diagnosis_result.get('score'),
                threshold_value=diagnosis_result.get('threshold')
            )
            
            db.add(alarm)
            await db.commit()
            
        except Exception as e:
            logger.error(f"创建告警失败: {str(e)}")
            
    def _get_alarm_severity(self, status: DiagnosisStatus) -> str:
        """根据诊断状态获取告警严重程度"""
        severity_map = {
            DiagnosisStatus.WARNING: "warning",
            DiagnosisStatus.ERROR: "error",
            DiagnosisStatus.CRITICAL: "critical"
        }
        return severity_map.get(status, "warning")
        
    async def _update_task_status(
        self, task: DiagnosisTask, status: TaskStatus,
        error_message: Optional[str] = None, db: AsyncSession = None
    ):
        """更新任务状态"""
        task.status = status
        if error_message:
            # 可以添加错误日志字段
            pass
        if db:
            await db.commit()

# 全局执行器实例
diagnosis_executor = DiagnosisExecutor()