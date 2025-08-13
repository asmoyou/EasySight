import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models.event_task import EventTask, EventTaskStatus
from models.ai_algorithm import AIAlgorithm, AIService
from models.camera import Camera
import cv2
import numpy as np
from io import BytesIO
import base64
import importlib
import importlib.util
from pathlib import Path

logger = logging.getLogger(__name__)

class EventTaskExecutor:
    """事件任务执行器"""
    
    def __init__(self):
        self.algorithms_dir = Path(__file__).parent / "algorithms"
        self.algorithms_dir.mkdir(exist_ok=True)
    
    async def execute_event_task(self, task_id: int, task_data: Dict, db: AsyncSession) -> Dict[str, Any]:
        """执行事件检测任务"""
        try:
            logger.info(f"开始执行事件任务 {task_id}")
            
            # 获取任务详情
            result = await db.execute(
                select(EventTask).where(EventTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                raise Exception(f"事件任务 {task_id} 不存在")
            
            # 更新任务状态为执行中
            await db.execute(
                update(EventTask)
                .where(EventTask.id == task_id)
                .values(
                    status=EventTaskStatus.RUNNING,
                    started_at=datetime.now(timezone.utc)
                )
            )
            await db.commit()
            
            # 获取算法信息
            algorithm_result = await db.execute(
                select(AIAlgorithm).where(AIAlgorithm.id == task.algorithm_id)
            )
            algorithm = algorithm_result.scalar_one_or_none()
            
            if not algorithm:
                raise Exception(f"算法 {task.algorithm_id} 不存在")
            
            # 获取摄像头信息
            camera_result = await db.execute(
                select(Camera).where(Camera.id == task.camera_id)
            )
            camera = camera_result.scalar_one_or_none()
            
            if not camera:
                raise Exception(f"摄像头 {task.camera_id} 不存在")
            
            # 获取图像数据
            image_data = task_data.get('image_data')
            if not image_data:
                raise Exception("缺少图像数据")
            
            # 解码图像
            image = self._decode_image(image_data)
            
            # 执行算法
            detection_result = await self._execute_algorithm(algorithm, image, task_data)
            
            # 更新任务状态为完成
            await db.execute(
                update(EventTask)
                .where(EventTask.id == task_id)
                .values(
                    status=EventTaskStatus.COMPLETED,
                    completed_at=datetime.now(timezone.utc),
                    result_data=detection_result
                )
            )
            await db.commit()
            
            logger.info(f"事件任务 {task_id} 执行完成")
            
            return {
                'success': True,
                'task_id': task_id,
                'result': detection_result,
                'execution_time': (datetime.now(timezone.utc) - task.started_at).total_seconds() * 1000
            }
            
        except Exception as e:
            logger.error(f"事件任务 {task_id} 执行失败: {str(e)}")
            
            # 更新任务状态为失败
            try:
                await db.execute(
                    update(EventTask)
                    .where(EventTask.id == task_id)
                    .values(
                        status=EventTaskStatus.FAILED,
                        completed_at=datetime.now(timezone.utc),
                        error_message=str(e)
                    )
                )
                await db.commit()
            except Exception as update_error:
                logger.error(f"更新任务状态失败: {str(update_error)}")
            
            return {
                'success': False,
                'task_id': task_id,
                'error': str(e)
            }
    
    def _decode_image(self, image_data: str) -> np.ndarray:
        """解码base64图像数据"""
        try:
            # 移除data URL前缀（如果存在）
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # 解码base64
            image_bytes = base64.b64decode(image_data)
            
            # 转换为numpy数组
            nparr = np.frombuffer(image_bytes, np.uint8)
            
            # 解码图像
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise Exception("无法解码图像数据")
            
            return image
            
        except Exception as e:
            logger.error(f"图像解码失败: {str(e)}")
            raise Exception(f"图像解码失败: {str(e)}")
    
    async def _execute_algorithm(self, algorithm: AIAlgorithm, image: np.ndarray, task_data: Dict) -> Dict[str, Any]:
        """执行AI算法"""
        try:
            logger.info(f"执行算法: {algorithm.code} v{algorithm.version}")
            
            # 获取算法模块
            algorithm_module = self._get_algorithm_module(algorithm.code, algorithm.version)
            
            if not algorithm_module:
                raise Exception(f"算法模块 {algorithm.code} v{algorithm.version} 未找到")
            
            # 执行算法
            if hasattr(algorithm_module, 'detect'):
                result = algorithm_module.detect(image, algorithm.config or {})
            elif hasattr(algorithm_module, 'process'):
                result = algorithm_module.process(image, algorithm.config or {})
            else:
                raise Exception(f"算法模块 {algorithm.code} 缺少detect或process方法")
            
            logger.info(f"算法执行完成: {algorithm.code}")
            return result
            
        except Exception as e:
            logger.error(f"算法执行失败: {str(e)}")
            raise Exception(f"算法执行失败: {str(e)}")
    
    def _get_algorithm_module(self, algorithm_code: str, version: str):
        """获取算法模块"""
        try:
            algorithm_path = self.algorithms_dir / algorithm_code / version
            
            if not algorithm_path.exists():
                logger.warning(f"算法路径不存在: {algorithm_path}")
                return None
            
            # 动态导入算法模块
            module_path = algorithm_path / "__init__.py"
            if not module_path.exists():
                logger.warning(f"算法模块文件不存在: {module_path}")
                return None
            
            spec = importlib.util.spec_from_file_location(
                f"{algorithm_code}_{version}", 
                module_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            logger.error(f"加载算法模块失败: {str(e)}")
            return None