from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from database import get_db
from models.diagnosis import DiagnosisTask, TaskStatus, DiagnosisTemplate, DiagnosisResult, DiagnosisStatus, DiagnosisAlarm
from models.worker import Worker, WorkerStatus
from schemas.diagnosis import (
    DiagnosisTaskCreate, DiagnosisTaskResponse, DiagnosisTaskUpdate,
    DiagnosisTaskListResponse, WorkerResponse, WorkerListResponse,
    TaskSubmitResponse, WorkerTaskFetchRequest, WorkerTaskFetchResponse,
    WorkerHeartbeatRequest, WorkerRegistrationRequest, WorkerRegistrationResponse
)
from routers.auth import get_current_user
from models.user import User
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import json
from task_queue_manager import TaskQueueManager
from diagnosis.rabbitmq_scheduler import RabbitMQTaskScheduler
from sqlalchemy import func, desc

# 创建路由器
router = APIRouter()
no_auth_router = APIRouter()  # 无认证路由，用于Worker API

# 全局RabbitMQ组件实例（在main_rabbitmq.py中初始化）
task_queue_manager: TaskQueueManager = None
rabbitmq_scheduler: RabbitMQTaskScheduler = None

def set_rabbitmq_components(queue_manager: TaskQueueManager, scheduler: RabbitMQTaskScheduler):
    """设置RabbitMQ组件实例"""
    global task_queue_manager, rabbitmq_scheduler
    task_queue_manager = queue_manager
    rabbitmq_scheduler = scheduler

@router.post("/tasks", response_model=DiagnosisTaskResponse)
async def create_diagnosis_task(
    task: DiagnosisTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建诊断任务"""
    try:
        # 转换前端数据为数据库格式
        task_data = task.to_db_dict()
        
        # 创建任务记录
        db_task = DiagnosisTask(
            name=task_data['name'],
            description=task_data.get('description'),
            template_id=task_data.get('template_id'),
            camera_ids=task_data.get('camera_ids', []),
            camera_groups=task_data.get('camera_groups', []),
            diagnosis_types=task_data.get('diagnosis_types', []),
            diagnosis_config=task_data.get('diagnosis_config', {}),
            schedule_type=task_data.get('schedule_type'),
            schedule_config=task_data.get('schedule_config', {}),
            cron_expression=task_data.get('cron_expression'),
            interval_minutes=task_data.get('interval_minutes'),
            threshold_config=task_data.get('threshold_config', {}),
            status=TaskStatus.PENDING,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        
        # 立即将任务发布到RabbitMQ队列
        if task_queue_manager and rabbitmq_scheduler:
            try:
                await rabbitmq_scheduler.schedule_immediate_task(db_task.id)
                print(f"任务 {db_task.id} 已发布到RabbitMQ队列")
            except Exception as e:
                print(f"发布任务到RabbitMQ失败: {e}")
                # 不抛出异常，任务仍然会被定期调度器处理
        
        return DiagnosisTaskResponse.from_orm(db_task)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

@router.get("/tasks", response_model=DiagnosisTaskListResponse)
async def get_diagnosis_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TaskStatus] = None,
    camera_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断任务列表"""
    try:
        # 构建查询条件
        conditions = []
        if status:
            conditions.append(DiagnosisTask.status == status)
        if camera_id:
            conditions.append(DiagnosisTask.camera_id == camera_id)
        
        # 联查用户表获取用户名 - created_by存储的是用户ID的字符串形式
        from sqlalchemy.orm import joinedload
        from sqlalchemy import cast, Integer
        if conditions:
            query = select(DiagnosisTask, User.username).outerjoin(User, cast(DiagnosisTask.created_by, Integer) == User.id).where(and_(*conditions)).order_by(DiagnosisTask.created_at.desc()).offset(skip).limit(limit)
        else:
            query = select(DiagnosisTask, User.username).outerjoin(User, cast(DiagnosisTask.created_by, Integer) == User.id).order_by(DiagnosisTask.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        task_rows = result.all()
        
        # 查询总数
        from sqlalchemy import func
        if conditions:
            count_query = select(func.count(DiagnosisTask.id)).where(and_(*conditions))
        else:
            count_query = select(func.count(DiagnosisTask.id))
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 构建响应数据
        tasks = []
        for task, username in task_rows:
            # 为任务对象添加用户名属性
            task.created_by_name = username
            tasks.append(DiagnosisTaskResponse.from_orm(task))
        
        return DiagnosisTaskListResponse(
            tasks=tasks,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.get("/tasks/{task_id}", response_model=DiagnosisTaskResponse)
async def get_diagnosis_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个诊断任务"""
    try:
        query = select(DiagnosisTask).where(DiagnosisTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return DiagnosisTaskResponse.from_orm(task)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")

@router.put("/tasks/{task_id}", response_model=DiagnosisTaskResponse)
async def update_diagnosis_task(
    task_id: int,
    task_update: DiagnosisTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新诊断任务"""
    try:
        # 查询任务
        query = select(DiagnosisTask).where(DiagnosisTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 转换前端数据为数据库格式
        update_data = task_update.to_db_dict()
        if update_data:
            # 不需要手动设置updated_at，数据库会自动更新
            update_query = (
                update(DiagnosisTask)
                .where(DiagnosisTask.id == task_id)
                .values(**update_data)
            )
            await db.execute(update_query)
            await db.commit()
            
            # 重新查询更新后的任务
            result = await db.execute(query)
            task = result.scalar_one()
        
        return DiagnosisTaskResponse.from_orm(task)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新任务失败: {str(e)}")

@router.delete("/tasks/{task_id}")
async def delete_diagnosis_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除诊断任务"""
    try:
        # 查询任务
        query = select(DiagnosisTask).where(DiagnosisTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 删除任务
        await db.delete(task)
        await db.commit()
        
        return {"message": "任务删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

@router.post("/tasks/{task_id}/submit", response_model=TaskSubmitResponse)
async def submit_task_to_queue(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """将任务提交到RabbitMQ队列"""
    try:
        # 验证任务是否存在
        query = select(DiagnosisTask).where(DiagnosisTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if not task_queue_manager or not rabbitmq_scheduler:
            raise HTTPException(status_code=503, detail="RabbitMQ服务不可用")
        
        # 立即调度任务
        success = await rabbitmq_scheduler.schedule_immediate_task(task_id)
        
        if success:
            return TaskSubmitResponse(
                task_id=task_id,
                status="submitted",
                message="任务已成功提交到RabbitMQ队列"
            )
        else:
            raise HTTPException(status_code=500, detail="任务提交失败")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")

@router.get("/workers", response_model=WorkerListResponse)
async def get_workers(
    skip: int = 0,
    limit: int = 100,
    status: Optional[WorkerStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取Worker列表"""
    try:
        from datetime import datetime, timezone, timedelta
        from worker_config import worker_config
        
        # 首先更新超时的worker状态
        timeout_threshold = datetime.now(timezone.utc) - timedelta(seconds=worker_config.heartbeat_timeout)
        
        # 将超时的在线worker标记为离线
        update_query = (
            update(Worker)
            .where(
                and_(
                    Worker.status == WorkerStatus.ONLINE,
                    Worker.last_heartbeat < timeout_threshold
                )
            )
            .values(status=WorkerStatus.OFFLINE)
        )
        await db.execute(update_query)
        await db.commit()
        
        # 构建查询条件
        conditions = []
        if status:
            conditions.append(Worker.status == status)
        
        # 查询Workers
        if conditions:
            query = select(Worker).where(and_(*conditions)).offset(skip).limit(limit)
        else:
            query = select(Worker).offset(skip).limit(limit)
        
        result = await db.execute(query)
        workers = result.scalars().all()
        
        # 查询总数
        if conditions:
            count_query = select(Worker).where(and_(*conditions))
        else:
            count_query = select(Worker)
        
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return WorkerListResponse(
            workers=[WorkerResponse.from_orm(worker) for worker in workers],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Worker列表失败: {str(e)}")

@router.get("/workers/distributed")
async def get_distributed_workers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有分布式Worker节点状态"""
    try:
        # 从数据库获取Worker信息
        query = select(Worker)
        result = await db.execute(query)
        workers = result.scalars().all()
        
        # 统计在线节点
        online_workers = [w for w in workers if w.status == WorkerStatus.ONLINE]
        
        # 格式化节点信息
        nodes = []
        for worker in workers:
            # 检查心跳是否超时（超过5分钟认为离线）
            is_online = worker.status == WorkerStatus.ONLINE
            if worker.last_heartbeat:
                # 使用当前UTC时间进行比较
                from datetime import timezone
                current_utc = datetime.now(timezone.utc)
                
                # 确保心跳时间也是UTC时区
                if worker.last_heartbeat.tzinfo is None:
                    # 如果没有时区信息，假设是UTC
                    heartbeat_utc = worker.last_heartbeat.replace(tzinfo=timezone.utc)
                else:
                    # 如果有时区信息，确保是UTC
                    heartbeat_utc = worker.last_heartbeat.astimezone(timezone.utc)
                
                heartbeat_age = current_utc - heartbeat_utc
                is_online = is_online and heartbeat_age.total_seconds() < 300
            
            nodes.append({
                "node_id": worker.worker_id,  # 前端期望的字段名
                "node_name": worker.worker_id,  # 使用worker_id作为节点名称
                "worker_id": worker.worker_id,  # 保留原字段以兼容
                "host": worker.host,
                "port": worker.port,
                "status": "online" if is_online else "offline",
                "worker_pool_size": worker.max_concurrent_tasks,  # 前端期望的字段名
                "max_concurrent_tasks": worker.max_concurrent_tasks,
                "current_tasks": worker.current_tasks,
                "total_tasks_executed": worker.total_tasks_processed,  # 前端期望的字段名
                "capabilities": worker.capabilities,
                "last_heartbeat": worker.last_heartbeat.isoformat() if worker.last_heartbeat else None,
                "registered_at": worker.created_at.isoformat() if worker.created_at else None,  # 前端期望的字段名
                "total_tasks_processed": worker.total_tasks_processed,
                "successful_tasks": worker.successful_tasks,
                "failed_tasks": worker.failed_tasks,
                "created_at": worker.created_at.isoformat() if worker.created_at else None,
                "worker_status": {  # 前端期望的字段
                    "total_tasks": worker.total_tasks_processed,
                    "successful_tasks": worker.successful_tasks,
                    "failed_tasks": worker.failed_tasks
                }
            })
        
        return {
            "total_nodes": len(workers),
            "online_nodes": len([n for n in nodes if n["status"] == "online"]),
            "nodes": nodes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分布式Worker状态失败: {str(e)}")

@router.get("/workers/stats")
async def get_worker_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取Worker统计信息"""
    try:
        from datetime import datetime, timezone, timedelta
        from worker_config import worker_config
        
        # 首先更新超时的worker状态
        timeout_threshold = datetime.now(timezone.utc) - timedelta(seconds=worker_config.heartbeat_timeout)
        
        # 将超时的在线worker标记为离线
        update_query = (
            update(Worker)
            .where(
                and_(
                    Worker.status == WorkerStatus.ONLINE,
                    Worker.last_heartbeat < timeout_threshold
                )
            )
            .values(status=WorkerStatus.OFFLINE)
        )
        await db.execute(update_query)
        await db.commit()
        
        # 统计各状态的worker数量
        total_query = select(func.count(Worker.id))
        total_result = await db.execute(total_query)
        total_workers = total_result.scalar() or 0
        
        online_query = select(func.count(Worker.id)).where(Worker.status == WorkerStatus.ONLINE)
        online_result = await db.execute(online_query)
        online_workers = online_result.scalar() or 0
        
        busy_query = select(func.count(Worker.id)).where(Worker.status == WorkerStatus.BUSY)
        busy_result = await db.execute(busy_query)
        busy_workers = busy_result.scalar() or 0
        
        # 空闲worker = 在线worker - 忙碌worker
        idle_workers = max(0, online_workers - busy_workers)
        
        return {
            "total_workers": total_workers,
            "online_workers": online_workers,
            "busy_workers": busy_workers,
            "idle_workers": idle_workers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Worker统计信息失败: {str(e)}")

@router.get("/queue/status")
async def get_queue_status(
    current_user: User = Depends(get_current_user)
):
    """获取RabbitMQ队列状态"""
    try:
        if not task_queue_manager:
            raise HTTPException(status_code=503, detail="RabbitMQ服务不可用")
        
        queue_stats = await task_queue_manager.get_queue_info('diagnosis_tasks')
        return {
            "status": "connected" if task_queue_manager.is_connected() else "disconnected",
            "queue_stats": queue_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取队列状态失败: {str(e)}")

# Worker无认证API路由
@no_auth_router.post("/register", response_model=WorkerRegistrationResponse)
async def register_worker(
    registration: WorkerRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Worker注册"""
    try:
        # 检查Worker是否已存在
        query = select(Worker).where(Worker.worker_id == registration.worker_id)
        result = await db.execute(query)
        existing_worker = result.scalar_one_or_none()
        
        if existing_worker:
            # 更新现有Worker信息
            from datetime import timezone
            current_utc = datetime.now(timezone.utc)
            update_query = (
                update(Worker)
                .where(Worker.worker_id == registration.worker_id)
                .values(
                    host=registration.host,
                    port=registration.port,
                    max_concurrent_tasks=registration.max_concurrent_tasks,
                    capabilities=registration.capabilities,
                    status=WorkerStatus.ONLINE,
                    last_heartbeat=current_utc,
                    updated_at=current_utc
                )
            )
            await db.execute(update_query)
        else:
            # 创建新Worker
            from datetime import timezone
            current_utc = datetime.now(timezone.utc)
            worker = Worker(
                worker_id=registration.worker_id,
                host=registration.host,
                port=registration.port,
                max_concurrent_tasks=registration.max_concurrent_tasks,
                current_tasks=0,
                capabilities=registration.capabilities,
                status=WorkerStatus.ONLINE,
                last_heartbeat=current_utc,
                created_at=current_utc
            )
            db.add(worker)
        
        await db.commit()
        
        return WorkerRegistrationResponse(
            success=True,
            message="Worker注册成功",
            worker_id=registration.worker_id
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Worker注册失败: {str(e)}")

@no_auth_router.post("/heartbeat")
async def worker_heartbeat(
    heartbeat: WorkerHeartbeatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Worker心跳"""
    try:
        # 更新Worker心跳时间和状态
        from datetime import timezone
        current_utc = datetime.now(timezone.utc)
        update_query = (
            update(Worker)
            .where(Worker.worker_id == heartbeat.worker_id)
            .values(
                current_tasks=heartbeat.current_tasks,
                status=heartbeat.status,
                last_heartbeat=current_utc,
                updated_at=current_utc
            )
        )
        
        result = await db.execute(update_query)
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Worker不存在，请先注册")
        
        await db.commit()
        
        # 发送心跳到RabbitMQ（可选）
        if task_queue_manager:
            try:
                await task_queue_manager.publish_heartbeat(heartbeat.worker_id, {
                    "worker_id": heartbeat.worker_id,
                    "current_tasks": heartbeat.current_tasks,
                    "status": heartbeat.status.value,
                    "timestamp": current_utc.isoformat()
                })
            except Exception as e:
                print(f"发送心跳到RabbitMQ失败: {e}")
        
        return {"message": "心跳更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"心跳更新失败: {str(e)}")

@no_auth_router.post("/{node_id}/heartbeat")
async def worker_heartbeat_with_node_id(
    node_id: str,
    heartbeat_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Worker心跳 - 带node_id参数的版本"""
    try:
        # 更新Worker心跳时间和状态
        from datetime import timezone
        current_utc = datetime.now(timezone.utc)
        current_tasks = heartbeat_data.get('current_tasks', 0)
        status = WorkerStatus.ONLINE  # 默认为在线状态
        
        update_query = (
            update(Worker)
            .where(Worker.worker_id == node_id)
            .values(
                current_tasks=current_tasks,
                status=status,
                last_heartbeat=current_utc,
                updated_at=current_utc
            )
        )
        
        result = await db.execute(update_query)
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Worker不存在，请先注册")
        
        await db.commit()
        
        # 发送心跳到RabbitMQ（可选）
        if task_queue_manager:
            try:
                await task_queue_manager.publish_heartbeat(node_id, {
                    "worker_id": node_id,
                    "current_tasks": current_tasks,
                    "status": status.value,
                    "timestamp": current_utc.isoformat()
                })
            except Exception as e:
                print(f"发送心跳到RabbitMQ失败: {e}")
        
        return {"message": "心跳更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"心跳更新失败: {str(e)}")

@no_auth_router.post("/tasks/fetch", response_model=WorkerTaskFetchResponse)
async def fetch_tasks_for_worker(
    fetch_request: WorkerTaskFetchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Worker获取任务（兼容性接口，实际任务通过RabbitMQ分发）"""
    try:
        # 验证Worker是否存在
        query = select(Worker).where(Worker.worker_id == fetch_request.worker_id)
        result = await db.execute(query)
        worker = result.scalar_one_or_none()
        
        if not worker:
            raise HTTPException(status_code=404, detail="Worker不存在，请先注册")
        
        # 在RabbitMQ模式下，任务通过消息队列分发，这里返回空列表
        # 但保留接口以确保向后兼容性
        return WorkerTaskFetchResponse(
            tasks=[],
            total_available=0,
            message="任务通过RabbitMQ队列分发，请监听队列消息"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")

@no_auth_router.post("/unregister")
async def unregister_worker(
    worker_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Worker注销"""
    try:
        # 更新Worker状态为离线
        update_query = (
            update(Worker)
            .where(Worker.worker_id == worker_id)
            .values(
                status=WorkerStatus.OFFLINE,
                updated_at=datetime.utcnow()
            )
        )
        
        result = await db.execute(update_query)
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Worker不存在")
        
        await db.commit()
        
        return {"message": "Worker注销成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Worker注销失败: {str(e)}")

# Results API endpoints
@router.get("/results")
async def get_diagnosis_results(
    page: int = 1,
    page_size: int = 20,
    task_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断结果列表"""
    try:
        # 构建查询条件
        conditions = []
        if task_id:
            conditions.append(DiagnosisResult.task_id == task_id)
        if status:
            conditions.append(DiagnosisResult.diagnosis_status == status)
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                conditions.append(DiagnosisResult.created_at >= start_dt)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                conditions.append(DiagnosisResult.created_at <= end_dt)
            except ValueError:
                pass
        
        # 构建查询
        query = select(DiagnosisResult)
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序和分页
        query = query.order_by(desc(DiagnosisResult.created_at))
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        results = result.scalars().all()
        
        # 获取总数
        count_query = select(func.count(DiagnosisResult.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 转换结果格式以匹配前端期望
        formatted_results = []
        for result_item in results:
            # 从result_data中提取issues_found信息
            result_data = result_item.result_data or {}
            issues_found = result_data.get('issues', result_data.get('issues_found', []))
            
            # 如果issues_found不是列表，尝试从其他字段推断
            if not isinstance(issues_found, list):
                issues_found = []
                # 如果状态不是NORMAL，可以根据诊断类型和分数生成问题信息
                if result_item.diagnosis_status and result_item.diagnosis_status.value != 'normal':
                    issue = {
                        'type': result_item.diagnosis_type or 'unknown',
                        'severity': result_item.diagnosis_status.value,
                        'score': result_item.score,
                        'threshold': result_item.threshold,
                        'description': f"{result_item.diagnosis_type or '未知'}问题检测"
                    }
                    issues_found.append(issue)
            
            formatted_result = {
                "id": result_item.id,
                "task_id": result_item.task_id,
                "task_name": f"任务{result_item.task_id}",  # 可以后续优化为实际任务名
                "camera_name": result_item.camera_name,
                "diagnosis_type": result_item.diagnosis_type,
                "status": result_item.diagnosis_status.value if result_item.diagnosis_status else "unknown",
                "score": result_item.score,
                "threshold": result_item.threshold,
                "result_data": result_data,
                "issues_found": issues_found,
                "recommendations": result_item.suggestions or [],
                "processing_time": result_item.processing_time,
                "execution_time": result_item.processing_time,  # 前端期望的字段名
                "error_message": result_item.error_message,
                "image_url": result_item.image_url,
                "thumbnail_url": result_item.thumbnail_url,
                "created_at": result_item.created_at.isoformat() if result_item.created_at else None
            }
            formatted_results.append(formatted_result)
        
        return {
            "results": formatted_results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取诊断结果失败: {str(e)}")

@router.get("/results/{result_id}")
async def get_diagnosis_result(
    result_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个诊断结果详情"""
    try:
        query = select(DiagnosisResult).where(DiagnosisResult.id == result_id)
        result = await db.execute(query)
        diagnosis_result = result.scalar_one_or_none()
        
        if not diagnosis_result:
            raise HTTPException(status_code=404, detail="诊断结果不存在")
        
        # 从result_data中提取issues_found信息
        result_data = diagnosis_result.result_data or {}
        issues_found = result_data.get('issues', result_data.get('issues_found', []))
        
        # 如果issues_found不是列表，尝试从其他字段推断
        if not isinstance(issues_found, list):
            issues_found = []
            # 如果状态不是NORMAL，可以根据诊断类型和分数生成问题信息
            if diagnosis_result.diagnosis_status and diagnosis_result.diagnosis_status.value != 'normal':
                issue = {
                    'type': diagnosis_result.diagnosis_type or 'unknown',
                    'severity': diagnosis_result.diagnosis_status.value,
                    'score': diagnosis_result.score,
                    'threshold': diagnosis_result.threshold,
                    'description': f"{diagnosis_result.diagnosis_type or '未知'}问题检测"
                }
                issues_found.append(issue)
        
        # 转换结果格式以匹配前端期望
        formatted_result = {
            "id": diagnosis_result.id,
            "task_id": diagnosis_result.task_id,
            "task_name": f"任务{diagnosis_result.task_id}",  # 可以后续优化为实际任务名
            "camera_name": diagnosis_result.camera_name,
            "diagnosis_type": diagnosis_result.diagnosis_type,
            "status": diagnosis_result.diagnosis_status.value if diagnosis_result.diagnosis_status else "unknown",
            "score": diagnosis_result.score,
            "threshold": diagnosis_result.threshold,
            "result_data": result_data,
            "issues_found": issues_found,
            "recommendations": diagnosis_result.suggestions or [],
            "processing_time": diagnosis_result.processing_time,
            "execution_time": diagnosis_result.processing_time,  # 前端期望的字段名
            "error_message": diagnosis_result.error_message,
            "image_url": diagnosis_result.image_url,
            "thumbnail_url": diagnosis_result.thumbnail_url,
            "created_at": diagnosis_result.created_at.isoformat() if diagnosis_result.created_at else None,
            "metrics": diagnosis_result.metrics or {}
        }
        
        return formatted_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取诊断结果详情失败: {str(e)}")

# Templates API endpoints
@router.get("/templates")
async def get_templates(
    page: int = 1,
    page_size: int = 20,
    diagnosis_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_public: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断模板列表"""
    try:
        # 构建查询条件
        conditions = []
        if diagnosis_type:
            conditions.append(DiagnosisTemplate.diagnosis_types.contains([diagnosis_type]))
        if is_active is not None:
            conditions.append(DiagnosisTemplate.is_active == is_active)
        
        # 构建查询
        query = select(DiagnosisTemplate)
        if conditions:
            query = query.where(and_(*conditions))
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        # 获取总数
        count_query = select(DiagnosisTemplate)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return {
            "items": templates,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")

@router.get("/templates/{template_id}")
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板详情"""
    try:
        query = select(DiagnosisTemplate).where(DiagnosisTemplate.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {str(e)}")

@router.post("/templates")
async def create_template(
    template_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建诊断模板"""
    try:
        # 创建模板
        template = DiagnosisTemplate(
            name=template_data.get("name"),
            description=template_data.get("description"),
            diagnosis_types=[template_data.get("diagnosis_type")] if template_data.get("diagnosis_type") else [],
            default_config=template_data.get("config_template", {}),
            default_schedule=template_data.get("default_schedule", {}),
            threshold_config=template_data.get("threshold_config", {}),
            is_active=True,
            is_system=False,
            created_by=current_user.username
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        return template
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")

@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    template_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新诊断模板"""
    try:
        # 查找模板
        query = select(DiagnosisTemplate).where(DiagnosisTemplate.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 更新字段
        if "name" in template_data:
            template.name = template_data["name"]
        if "description" in template_data:
            template.description = template_data["description"]
        if "diagnosis_type" in template_data:
            template.diagnosis_types = [template_data["diagnosis_type"]]
        if "config_template" in template_data:
            template.default_config = template_data["config_template"]
        if "default_schedule" in template_data:
            template.default_schedule = template_data["default_schedule"]
        if "threshold_config" in template_data:
            template.threshold_config = template_data["threshold_config"]
        if "is_active" in template_data:
            template.is_active = template_data["is_active"]
        
        await db.commit()
        await db.refresh(template)
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新模板失败: {str(e)}")

@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除诊断模板"""
    try:
        # 查找模板
        query = select(DiagnosisTemplate).where(DiagnosisTemplate.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 删除模板
        await db.delete(template)
        await db.commit()
        
        return {"message": "模板删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除模板失败: {str(e)}")

@router.get("/workers/{worker_id}/tasks")
async def get_worker_tasks(
    worker_id: str,
    skip: int = 0,
    limit: int = 100,
    status: Optional[TaskStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取特定Worker的任务列表"""
    try:
        # 验证Worker是否存在
        worker_query = select(Worker).where(Worker.worker_id == worker_id)
        worker_result = await db.execute(worker_query)
        worker = worker_result.scalar_one_or_none()
        
        if not worker:
            raise HTTPException(status_code=404, detail="Worker不存在")
        
        # 构建查询条件
        conditions = [DiagnosisTask.assigned_worker == worker_id]
        if status:
            conditions.append(DiagnosisTask.status == status)
        
        # 查询任务
        query = (
            select(DiagnosisTask)
            .where(and_(*conditions))
            .order_by(desc(DiagnosisTask.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 查询总数
        count_query = select(func.count(DiagnosisTask.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 前端期望直接返回任务数组，而不是包装对象
        return [DiagnosisTaskResponse.from_orm(task) for task in tasks]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Worker任务失败: {str(e)}")

@router.delete("/workers/{node_id}")
async def unregister_worker_by_node_id(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """通过节点ID注销Worker - 前端调用的API"""
    try:
        # 查找要删除的Worker
        query = select(Worker).where(Worker.worker_id == node_id)
        result = await db.execute(query)
        worker = result.scalar_one_or_none()
        
        if not worker:
            raise HTTPException(status_code=404, detail="Worker不存在")
        
        # 删除Worker记录
        await db.delete(worker)
        await db.commit()
        
        return {"message": "Worker注销成功"}
        
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Worker注销失败: {str(e)}")

@no_auth_router.post("/tasks/{task_id}/status")
async def update_task_status(
    task_id: int,
    status_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """更新任务状态（Worker专用）"""
    try:
        # 查找任务
        result = await db.execute(
            select(DiagnosisTask).where(DiagnosisTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 更新任务状态
        task.status = TaskStatus(status_data.get('status'))
        task.assigned_worker = status_data.get('worker_id')
        task.updated_at = datetime.utcnow()
        
        # 如果有结果数据，更新结果
        if 'result' in status_data:
            task.result = status_data['result']
        
        await db.commit()
        
        return {"message": "任务状态更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新任务状态失败: {str(e)}")

@router.get("/alarms")
async def get_diagnosis_alarms(
    page: int = 1,
    page_size: int = 20,
    severity: Optional[str] = None,
    is_acknowledged: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断告警列表"""
    try:
        # 构建查询条件
        conditions = []
        
        if severity:
            conditions.append(DiagnosisAlarm.severity == severity)
        
        if is_acknowledged is not None:
            conditions.append(DiagnosisAlarm.is_acknowledged == is_acknowledged)
        
        # 构建查询
        query = select(DiagnosisAlarm)
        if conditions:
            query = query.where(and_(*conditions))
        
        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(desc(DiagnosisAlarm.created_at))
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        alarms = result.scalars().all()
        
        # 查询总数
        count_query = select(func.count(DiagnosisAlarm.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 转换为响应格式，包含关联的诊断结果信息
        alarm_list = []
        for alarm in alarms:
            # 获取关联的诊断结果信息
            result_query = select(DiagnosisResult).where(DiagnosisResult.id == alarm.result_id)
            result_data = await db.execute(result_query)
            diagnosis_result = result_data.scalar_one_or_none()
            
            alarm_dict = {
                "id": alarm.id,
                "result_id": alarm.result_id,
                "alarm_type": diagnosis_result.diagnosis_type if diagnosis_result else alarm.alarm_type,
                "severity": alarm.severity,
                "title": alarm.title,
                "description": alarm.description,
                "threshold_config": alarm.threshold_config,
                "current_value": alarm.current_value,
                "threshold_value": alarm.threshold_value,
                "is_acknowledged": alarm.is_acknowledged,
                "acknowledged_by": alarm.acknowledged_by,
                "acknowledged_at": alarm.acknowledged_at,
                "created_at": alarm.created_at,
                # 添加诊断结果相关信息
                "camera_id": diagnosis_result.camera_id if diagnosis_result else None,
                "camera_name": diagnosis_result.camera_name if diagnosis_result else None,
                "diagnosis_type": diagnosis_result.diagnosis_type if diagnosis_result else None,
                "diagnosis_status": diagnosis_result.diagnosis_status.value if diagnosis_result and diagnosis_result.diagnosis_status else None,
                "score": diagnosis_result.score if diagnosis_result else None,
                "threshold": diagnosis_result.threshold if diagnosis_result else None,
                "image_url": diagnosis_result.image_url if diagnosis_result else None,
                "thumbnail_url": diagnosis_result.thumbnail_url if diagnosis_result else None,
                "image_timestamp": diagnosis_result.image_timestamp if diagnosis_result else None,
                "processing_time": diagnosis_result.processing_time if diagnosis_result else None,
                "suggestions": diagnosis_result.suggestions if diagnosis_result else [],
                "metrics": {
                    "score": diagnosis_result.score if diagnosis_result else None,
                    "threshold": diagnosis_result.threshold if diagnosis_result else None,
                    **(diagnosis_result.metrics if diagnosis_result and diagnosis_result.metrics else {})
                } if diagnosis_result else {},
                "result_data": diagnosis_result.result_data if diagnosis_result else {}
            }
            alarm_list.append(alarm_dict)
        
        return {
            "items": alarm_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警列表失败: {str(e)}")


@router.post("/alarms/{alarm_id}/acknowledge")
async def acknowledge_alarm(
    alarm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """确认告警"""
    try:
        # 查找告警
        query = select(DiagnosisAlarm).where(DiagnosisAlarm.id == alarm_id)
        result = await db.execute(query)
        alarm = result.scalar_one_or_none()
        
        if not alarm:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        # 更新确认状态
        alarm.is_acknowledged = True
        alarm.acknowledged_by = current_user.id
        alarm.acknowledged_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "告警确认成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"确认告警失败: {str(e)}")


@router.post("/alarms/batch-acknowledge")
async def batch_acknowledge_alarms(
    request_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量确认告警"""
    try:
        alarm_ids = request_data.get("alarm_ids", [])
        if not alarm_ids:
            raise HTTPException(status_code=400, detail="告警ID列表不能为空")
        
        # 查找告警
        query = select(DiagnosisAlarm).where(DiagnosisAlarm.id.in_(alarm_ids))
        result = await db.execute(query)
        alarms = result.scalars().all()
        
        if not alarms:
            raise HTTPException(status_code=404, detail="未找到指定的告警")
        
        # 批量更新确认状态
        for alarm in alarms:
            alarm.is_acknowledged = True
            alarm.acknowledged_by = current_user.id
            alarm.acknowledged_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": f"成功确认 {len(alarms)} 条告警"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"批量确认告警失败: {str(e)}")


@router.put("/alarms/{alarm_id}/status")
async def update_alarm_status(
    alarm_id: int,
    request_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新告警状态"""
    try:
        status = request_data.get("status")
        if not status:
            raise HTTPException(status_code=400, detail="状态不能为空")
        
        # 查找告警
        query = select(DiagnosisAlarm).where(DiagnosisAlarm.id == alarm_id)
        result = await db.execute(query)
        alarm = result.scalar_one_or_none()
        
        if not alarm:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        # 根据状态更新相应字段
        if status == "handled":
            alarm.is_acknowledged = True
            alarm.acknowledged_by = current_user.id
            alarm.acknowledged_at = datetime.utcnow()
        elif status == "ignored":
            alarm.is_acknowledged = True
            alarm.acknowledged_by = current_user.id
            alarm.acknowledged_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "告警状态更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新告警状态失败: {str(e)}")


@router.put("/alarms/batch-status")
async def batch_update_alarm_status(
    request_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新告警状态"""
    try:
        alarm_ids = request_data.get("alarm_ids", [])
        status = request_data.get("status")
        
        if not alarm_ids:
            raise HTTPException(status_code=400, detail="告警ID列表不能为空")
        if not status:
            raise HTTPException(status_code=400, detail="状态不能为空")
        
        # 查找告警
        query = select(DiagnosisAlarm).where(DiagnosisAlarm.id.in_(alarm_ids))
        result = await db.execute(query)
        alarms = result.scalars().all()
        
        if not alarms:
            raise HTTPException(status_code=404, detail="未找到指定的告警")
        
        # 批量更新状态
        for alarm in alarms:
            if status == "handled":
                alarm.is_acknowledged = True
                alarm.acknowledged_by = current_user.id
                alarm.acknowledged_at = datetime.utcnow()
            elif status == "ignored":
                alarm.is_acknowledged = True
                alarm.acknowledged_by = current_user.id
                alarm.acknowledged_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": f"成功更新 {len(alarms)} 条告警状态"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"批量更新告警状态失败: {str(e)}")


@router.delete("/alarms/{alarm_id}")
async def delete_alarm(
    alarm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除告警"""
    try:
        # 查找告警
        query = select(DiagnosisAlarm).where(DiagnosisAlarm.id == alarm_id)
        result = await db.execute(query)
        alarm = result.scalar_one_or_none()
        
        if not alarm:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        # 删除告警
        await db.delete(alarm)
        await db.commit()
        
        return {"message": "告警删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除告警失败: {str(e)}")


@router.delete("/alarms/clear-all")
async def clear_all_alarms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """清空所有告警"""
    try:
        # 删除所有告警
        query = delete(DiagnosisAlarm)
        await db.execute(query)
        await db.commit()
        
        return {"message": "所有告警已清空"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"清空告警失败: {str(e)}")