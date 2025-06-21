from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from database import get_db
from models.ai_algorithm import AIAlgorithm, AIService, AIModel, AIServiceLog, AlgorithmType, ServiceStatus, ModelType
from models.user import User
from routers.auth import get_current_user

router = APIRouter()

# Pydantic models
class AIAlgorithmCreate(BaseModel):
    name: str
    algorithm_type: AlgorithmType
    version: str
    description: Optional[str] = None
    config_schema: Dict[str, Any] = {}
    input_format: Dict[str, Any] = {}
    output_format: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}
    resource_requirements: Dict[str, Any] = {}
    supported_platforms: List[str] = []
    tags: List[str] = []
    is_active: bool = True

class AIAlgorithmUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None
    input_format: Optional[Dict[str, Any]] = None
    output_format: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    resource_requirements: Optional[Dict[str, Any]] = None
    supported_platforms: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class AIAlgorithmResponse(BaseModel):
    id: int
    name: str
    algorithm_type: AlgorithmType
    version: str
    description: Optional[str]
    config_schema: Dict[str, Any]
    input_format: Dict[str, Any]
    output_format: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    resource_requirements: Dict[str, Any]
    supported_platforms: List[str]
    tags: List[str]
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

class AIServiceCreate(BaseModel):
    name: str
    algorithm_id: int
    model_id: Optional[int] = None
    endpoint_url: str
    api_key: Optional[str] = None
    config: Dict[str, Any] = {}
    max_concurrent_requests: int = 10
    timeout_seconds: int = 30
    retry_count: int = 3
    description: Optional[str] = None
    is_active: bool = True

class AIServiceUpdate(BaseModel):
    name: Optional[str] = None
    algorithm_id: Optional[int] = None
    model_id: Optional[int] = None
    endpoint_url: Optional[str] = None
    api_key: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    max_concurrent_requests: Optional[int] = None
    timeout_seconds: Optional[int] = None
    retry_count: Optional[int] = None
    status: Optional[ServiceStatus] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class AIServiceResponse(BaseModel):
    id: int
    name: str
    algorithm_id: int
    algorithm_name: str
    model_id: Optional[int]
    model_name: Optional[str]
    endpoint_url: str
    config: Dict[str, Any]
    status: ServiceStatus
    max_concurrent_requests: int
    current_requests: int
    timeout_seconds: int
    retry_count: int
    total_requests: int
    success_requests: int
    failed_requests: int
    avg_response_time: Optional[float]
    last_heartbeat: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    description: Optional[str]

class AIModelCreate(BaseModel):
    name: str
    model_type: ModelType
    algorithm_id: int
    version: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    config: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}
    training_data_info: Dict[str, Any] = {}
    description: Optional[str] = None
    is_active: bool = True

class AIModelUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    training_data_info: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class AIModelResponse(BaseModel):
    id: int
    name: str
    model_type: ModelType
    algorithm_id: int
    algorithm_name: str
    version: str
    file_path: Optional[str]
    file_size: Optional[int]
    checksum: Optional[str]
    config: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    training_data_info: Dict[str, Any]
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime
    description: Optional[str]

class AIServiceLogResponse(BaseModel):
    id: int
    service_id: int
    service_name: str
    request_id: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    status: str
    response_time: Optional[float]
    error_message: Optional[str]
    created_at: datetime

class AIStats(BaseModel):
    total_algorithms: int
    active_algorithms: int
    total_services: int
    active_services: int
    online_services: int
    total_models: int
    active_models: int
    total_requests_today: int
    success_rate: float
    avg_response_time: float
    by_algorithm_type: Dict[str, int]
    by_service_status: Dict[str, int]

# AI算法管理
@router.get("/algorithms/", response_model=List[AIAlgorithmResponse])
async def get_algorithms(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    algorithm_type: Optional[AlgorithmType] = Query(None, description="算法类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取AI算法列表"""
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                AIAlgorithm.name.ilike(search_pattern),
                AIAlgorithm.description.ilike(search_pattern)
            )
        )
    
    if algorithm_type:
        conditions.append(AIAlgorithm.algorithm_type == algorithm_type)
    
    if is_active is not None:
        conditions.append(AIAlgorithm.is_active == is_active)
    
    query = select(AIAlgorithm).order_by(AIAlgorithm.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    algorithms = result.scalars().all()
    
    return [AIAlgorithmResponse(
        id=algorithm.id,
        name=algorithm.name,
        algorithm_type=algorithm.algorithm_type,
        version=algorithm.version,
        description=algorithm.description,
        config_schema=algorithm.config_schema,
        input_format=algorithm.input_format,
        output_format=algorithm.output_format,
        performance_metrics=algorithm.performance_metrics,
        resource_requirements=algorithm.resource_requirements,
        supported_platforms=algorithm.supported_platforms,
        tags=algorithm.tags,
        is_active=algorithm.is_active,
        usage_count=algorithm.usage_count,
        created_at=algorithm.created_at,
        updated_at=algorithm.updated_at
    ) for algorithm in algorithms]

@router.post("/algorithms/", response_model=AIAlgorithmResponse)
async def create_algorithm(
    algorithm_data: AIAlgorithmCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建AI算法"""
    # 检查算法名称和版本是否已存在
    result = await db.execute(
        select(AIAlgorithm).where(
            and_(
                AIAlgorithm.name == algorithm_data.name,
                AIAlgorithm.version == algorithm_data.version
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该名称和版本的算法已存在"
        )
    
    algorithm = AIAlgorithm(**algorithm_data.dict())
    db.add(algorithm)
    await db.commit()
    await db.refresh(algorithm)
    
    return AIAlgorithmResponse(
        id=algorithm.id,
        name=algorithm.name,
        algorithm_type=algorithm.algorithm_type,
        version=algorithm.version,
        description=algorithm.description,
        config_schema=algorithm.config_schema,
        input_format=algorithm.input_format,
        output_format=algorithm.output_format,
        performance_metrics=algorithm.performance_metrics,
        resource_requirements=algorithm.resource_requirements,
        supported_platforms=algorithm.supported_platforms,
        tags=algorithm.tags,
        is_active=algorithm.is_active,
        usage_count=algorithm.usage_count,
        created_at=algorithm.created_at,
        updated_at=algorithm.updated_at
    )

@router.get("/algorithms/{algorithm_id}", response_model=AIAlgorithmResponse)
async def get_algorithm(
    algorithm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取AI算法详情"""
    result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id == algorithm_id))
    algorithm = result.scalar_one_or_none()
    
    if not algorithm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="算法不存在"
        )
    
    return AIAlgorithmResponse(
        id=algorithm.id,
        name=algorithm.name,
        algorithm_type=algorithm.algorithm_type,
        version=algorithm.version,
        description=algorithm.description,
        config_schema=algorithm.config_schema,
        input_format=algorithm.input_format,
        output_format=algorithm.output_format,
        performance_metrics=algorithm.performance_metrics,
        resource_requirements=algorithm.resource_requirements,
        supported_platforms=algorithm.supported_platforms,
        tags=algorithm.tags,
        is_active=algorithm.is_active,
        usage_count=algorithm.usage_count,
        created_at=algorithm.created_at,
        updated_at=algorithm.updated_at
    )

@router.put("/algorithms/{algorithm_id}", response_model=AIAlgorithmResponse)
async def update_algorithm(
    algorithm_id: int,
    algorithm_data: AIAlgorithmUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新AI算法"""
    result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id == algorithm_id))
    algorithm = result.scalar_one_or_none()
    
    if not algorithm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="算法不存在"
        )
    
    update_data = algorithm_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(algorithm, field, value)
    
    await db.commit()
    await db.refresh(algorithm)
    
    return AIAlgorithmResponse(
        id=algorithm.id,
        name=algorithm.name,
        algorithm_type=algorithm.algorithm_type,
        version=algorithm.version,
        description=algorithm.description,
        config_schema=algorithm.config_schema,
        input_format=algorithm.input_format,
        output_format=algorithm.output_format,
        performance_metrics=algorithm.performance_metrics,
        resource_requirements=algorithm.resource_requirements,
        supported_platforms=algorithm.supported_platforms,
        tags=algorithm.tags,
        is_active=algorithm.is_active,
        usage_count=algorithm.usage_count,
        created_at=algorithm.created_at,
        updated_at=algorithm.updated_at
    )

@router.delete("/algorithms/{algorithm_id}")
async def delete_algorithm(
    algorithm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除AI算法"""
    result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id == algorithm_id))
    algorithm = result.scalar_one_or_none()
    
    if not algorithm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="算法不存在"
        )
    
    # 检查是否有关联的服务
    service_result = await db.execute(select(AIService).where(AIService.algorithm_id == algorithm_id))
    if service_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该算法下还有关联的服务，无法删除"
        )
    
    await db.delete(algorithm)
    await db.commit()
    
    return {"message": "算法删除成功"}

# AI服务管理
@router.get("/services/", response_model=List[AIServiceResponse])
async def get_services(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    algorithm_id: Optional[int] = Query(None, description="算法ID筛选"),
    status: Optional[ServiceStatus] = Query(None, description="状态筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取AI服务列表"""
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                AIService.name.ilike(search_pattern),
                AIService.description.ilike(search_pattern)
            )
        )
    
    if algorithm_id:
        conditions.append(AIService.algorithm_id == algorithm_id)
    
    if status:
        conditions.append(AIService.status == status)
    
    if is_active is not None:
        conditions.append(AIService.is_active == is_active)
    
    query = select(AIService).order_by(AIService.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    services = result.scalars().all()
    
    # 获取算法和模型信息
    algorithm_map = {}
    model_map = {}
    
    if services:
        algorithm_ids = [s.algorithm_id for s in services]
        algorithm_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id.in_(algorithm_ids)))
        algorithms = algorithm_result.scalars().all()
        algorithm_map = {a.id: a.name for a in algorithms}
        
        model_ids = [s.model_id for s in services if s.model_id]
        if model_ids:
            model_result = await db.execute(select(AIModel).where(AIModel.id.in_(model_ids)))
            models = model_result.scalars().all()
            model_map = {m.id: m.name for m in models}
    
    return [AIServiceResponse(
        id=service.id,
        name=service.name,
        algorithm_id=service.algorithm_id,
        algorithm_name=algorithm_map.get(service.algorithm_id, ""),
        model_id=service.model_id,
        model_name=model_map.get(service.model_id) if service.model_id else None,
        endpoint_url=service.endpoint_url,
        config=service.config,
        status=service.status,
        max_concurrent_requests=service.max_concurrent_requests,
        current_requests=service.current_requests,
        timeout_seconds=service.timeout_seconds,
        retry_count=service.retry_count,
        total_requests=service.total_requests,
        success_requests=service.success_requests,
        failed_requests=service.failed_requests,
        avg_response_time=service.avg_response_time,
        last_heartbeat=service.last_heartbeat,
        is_active=service.is_active,
        created_at=service.created_at,
        updated_at=service.updated_at,
        description=service.description
    ) for service in services]

@router.post("/services/", response_model=AIServiceResponse)
async def create_service(
    service_data: AIServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建AI服务"""
    # 验证算法是否存在
    algorithm_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id == service_data.algorithm_id))
    algorithm = algorithm_result.scalar_one_or_none()
    if not algorithm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的算法不存在"
        )
    
    # 验证模型是否存在（如果指定了模型）
    model_name = None
    if service_data.model_id:
        model_result = await db.execute(select(AIModel).where(AIModel.id == service_data.model_id))
        model = model_result.scalar_one_or_none()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的模型不存在"
            )
        model_name = model.name
    
    service = AIService(**service_data.dict())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    
    return AIServiceResponse(
        id=service.id,
        name=service.name,
        algorithm_id=service.algorithm_id,
        algorithm_name=algorithm.name,
        model_id=service.model_id,
        model_name=model_name,
        endpoint_url=service.endpoint_url,
        config=service.config,
        status=service.status,
        max_concurrent_requests=service.max_concurrent_requests,
        current_requests=service.current_requests,
        timeout_seconds=service.timeout_seconds,
        retry_count=service.retry_count,
        total_requests=service.total_requests,
        success_requests=service.success_requests,
        failed_requests=service.failed_requests,
        avg_response_time=service.avg_response_time,
        last_heartbeat=service.last_heartbeat,
        is_active=service.is_active,
        created_at=service.created_at,
        updated_at=service.updated_at,
        description=service.description
    )

# AI模型管理
@router.get("/models/", response_model=List[AIModelResponse])
async def get_models(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    algorithm_id: Optional[int] = Query(None, description="算法ID筛选"),
    model_type: Optional[ModelType] = Query(None, description="模型类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取AI模型列表"""
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                AIModel.name.ilike(search_pattern),
                AIModel.description.ilike(search_pattern)
            )
        )
    
    if algorithm_id:
        conditions.append(AIModel.algorithm_id == algorithm_id)
    
    if model_type:
        conditions.append(AIModel.model_type == model_type)
    
    if is_active is not None:
        conditions.append(AIModel.is_active == is_active)
    
    query = select(AIModel).order_by(AIModel.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    # 获取算法信息
    algorithm_map = {}
    if models:
        algorithm_ids = [m.algorithm_id for m in models]
        algorithm_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id.in_(algorithm_ids)))
        algorithms = algorithm_result.scalars().all()
        algorithm_map = {a.id: a.name for a in algorithms}
    
    return [AIModelResponse(
        id=model.id,
        name=model.name,
        model_type=model.model_type,
        algorithm_id=model.algorithm_id,
        algorithm_name=algorithm_map.get(model.algorithm_id, ""),
        version=model.version,
        file_path=model.file_path,
        file_size=model.file_size,
        checksum=model.checksum,
        config=model.config,
        performance_metrics=model.performance_metrics,
        training_data_info=model.training_data_info,
        is_active=model.is_active,
        usage_count=model.usage_count,
        created_at=model.created_at,
        updated_at=model.updated_at,
        description=model.description
    ) for model in models]

@router.post("/models/", response_model=AIModelResponse)
async def create_model(
    model_data: AIModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建AI模型"""
    # 验证算法是否存在
    algorithm_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id == model_data.algorithm_id))
    algorithm = algorithm_result.scalar_one_or_none()
    if not algorithm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的算法不存在"
        )
    
    model = AIModel(**model_data.dict())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    return AIModelResponse(
        id=model.id,
        name=model.name,
        model_type=model.model_type,
        algorithm_id=model.algorithm_id,
        algorithm_name=algorithm.name,
        version=model.version,
        file_path=model.file_path,
        file_size=model.file_size,
        checksum=model.checksum,
        config=model.config,
        performance_metrics=model.performance_metrics,
        training_data_info=model.training_data_info,
        is_active=model.is_active,
        usage_count=model.usage_count,
        created_at=model.created_at,
        updated_at=model.updated_at,
        description=model.description
    )

@router.get("/stats/overview", response_model=AIStats)
async def get_ai_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取AI统计信息"""
    # 算法统计
    total_algorithms_result = await db.execute(select(func.count(AIAlgorithm.id)))
    total_algorithms = total_algorithms_result.scalar()
    
    active_algorithms_result = await db.execute(select(func.count(AIAlgorithm.id)).where(AIAlgorithm.is_active == True))
    active_algorithms = active_algorithms_result.scalar()
    
    # 服务统计
    total_services_result = await db.execute(select(func.count(AIService.id)))
    total_services = total_services_result.scalar()
    
    active_services_result = await db.execute(select(func.count(AIService.id)).where(AIService.is_active == True))
    active_services = active_services_result.scalar()
    
    online_services_result = await db.execute(select(func.count(AIService.id)).where(AIService.status == ServiceStatus.ONLINE))
    online_services = online_services_result.scalar()
    
    # 模型统计
    total_models_result = await db.execute(select(func.count(AIModel.id)))
    total_models = total_models_result.scalar()
    
    active_models_result = await db.execute(select(func.count(AIModel.id)).where(AIModel.is_active == True))
    active_models = active_models_result.scalar()
    
    # 请求统计（今日）
    from datetime import date
    today = date.today()
    total_requests_result = await db.execute(
        select(func.count(AIServiceLog.id))
        .where(func.date(AIServiceLog.created_at) == today)
    )
    total_requests_today = total_requests_result.scalar()
    
    success_requests_result = await db.execute(
        select(func.count(AIServiceLog.id))
        .where(
            and_(
                func.date(AIServiceLog.created_at) == today,
                AIServiceLog.status == "success"
            )
        )
    )
    success_requests = success_requests_result.scalar()
    
    success_rate = (success_requests / total_requests_today * 100) if total_requests_today > 0 else 0
    
    # 平均响应时间
    avg_response_result = await db.execute(
        select(func.avg(AIServiceLog.response_time))
        .where(
            and_(
                func.date(AIServiceLog.created_at) == today,
                AIServiceLog.response_time.isnot(None)
            )
        )
    )
    avg_response_time = avg_response_result.scalar() or 0
    
    # 按算法类型统计
    algorithm_type_result = await db.execute(
        select(AIAlgorithm.algorithm_type, func.count(AIAlgorithm.id))
        .group_by(AIAlgorithm.algorithm_type)
    )
    by_algorithm_type = {str(row[0].value): row[1] for row in algorithm_type_result.all()}
    
    # 按服务状态统计
    service_status_result = await db.execute(
        select(AIService.status, func.count(AIService.id))
        .group_by(AIService.status)
    )
    by_service_status = {str(row[0].value): row[1] for row in service_status_result.all()}
    
    return AIStats(
        total_algorithms=total_algorithms,
        active_algorithms=active_algorithms,
        total_services=total_services,
        active_services=active_services,
        online_services=online_services,
        total_models=total_models,
        active_models=active_models,
        total_requests_today=total_requests_today,
        success_rate=success_rate,
        avg_response_time=avg_response_time,
        by_algorithm_type=by_algorithm_type,
        by_service_status=by_service_status
    )