from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Generic, TypeVar
from datetime import datetime
import json
import logging

T = TypeVar('T')

from database import get_db, get_minio
from models.ai_algorithm import AIAlgorithm, AIService, AIModel, AIServiceLog, AlgorithmType, ServiceStatus, ModelType
from models.user import User
from routers.auth import get_current_user
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    page_size: int
class AIAlgorithmCreate(BaseModel):
    name: str
    code: Optional[str] = None  # 算法编码，如果不提供则自动生成
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
    code: str
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
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None

class AIServiceCreate(BaseModel):
    name: str
    algorithm_id: int
    camera_id: int
    model_id: Optional[int] = None
    endpoint_url: Optional[str] = None
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
    camera_id: Optional[int] = None
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
    camera_id: int
    camera_name: Optional[str] = None
    model_id: Optional[int]
    model_name: Optional[str]
    endpoint_url: Optional[str]
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
    tags: List[str] = []

class AIModelCreate(BaseModel):
    name: str
    model_type: ModelType
    algorithm_id: int
    version: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    config: Dict[str, Any] = {}
    input_format: Dict[str, Any] = {}
    output_format: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}
    training_data_info: Dict[str, Any] = {}
    tags: List[str] = []
    description: Optional[str] = None
    is_active: bool = True

class AIModelUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    input_format: Optional[Dict[str, Any]] = None
    output_format: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    training_data_info: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class AIModelResponse(BaseModel):
    id: int
    name: str
    model_type: ModelType
    algorithm_id: int
    algorithm_name: str
    algorithm_type: Optional[str] = None
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
    tags: List[str] = []

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
    # 前端期望的字段名
    total_count: int
    online_count: int
    processing_count: int

# AI算法管理
@router.get("/algorithms/", response_model=PaginatedResponse[AIAlgorithmResponse])
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
    
    # 构建基础查询
    base_query = select(AIAlgorithm)
    if conditions:
        base_query = base_query.where(and_(*conditions))
    
    # 获取总数
    count_query = select(func.count(AIAlgorithm.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 获取分页数据
    query = base_query.order_by(AIAlgorithm.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    algorithms = result.scalars().all()
    
    algorithm_responses = [AIAlgorithmResponse(
        id=algorithm.id,
        name=algorithm.name,
        code=algorithm.code,
        algorithm_type=algorithm.algorithm_type,
        version=algorithm.version,
        description=algorithm.description,
        file_path=algorithm.file_path,
        file_size=algorithm.file_size,
        file_hash=algorithm.file_hash,
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
    
    return PaginatedResponse(
        data=algorithm_responses,
        total=total,
        page=page,
        page_size=page_size
    )

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
    
    # 生成算法编码
    algorithm_dict = algorithm_data.dict()
    if not algorithm_dict.get('code'):
        # 基于名称和版本生成编码
        import re
        import hashlib
        
        # 清理名称，只保留字母数字和连字符
        clean_name = re.sub(r'[^a-zA-Z0-9\-_]', '', algorithm_data.name.lower().replace(' ', '-'))
        clean_version = re.sub(r'[^a-zA-Z0-9\-_.]', '', algorithm_data.version)
        
        # 生成基础编码
        base_code = f"{clean_name}-{clean_version}"
        
        # 检查编码是否已存在，如果存在则添加哈希后缀
        code_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.code == base_code))
        if code_result.scalar_one_or_none():
            # 生成唯一后缀
            hash_input = f"{algorithm_data.name}-{algorithm_data.version}-{datetime.now().isoformat()}"
            hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            base_code = f"{base_code}-{hash_suffix}"
        
        algorithm_dict['code'] = base_code
    else:
        # 检查用户提供的编码是否已存在
        code_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.code == algorithm_dict['code']))
        if code_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该算法编码已存在"
            )
    
    algorithm = AIAlgorithm(**algorithm_dict)
    db.add(algorithm)
    await db.commit()
    await db.refresh(algorithm)
    
    return AIAlgorithmResponse(
        id=algorithm.id,
        name=algorithm.name,
        code=algorithm.code,
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
        code=algorithm.code,
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
        code=algorithm.code,
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
    
    # 删除MinIO中的文件
    if algorithm.file_path:
        try:
            minio_client = get_minio()
            # 从文件路径中提取对象名称
            object_name = algorithm.file_path.replace("/api/v1/files/", "")
            minio_client.remove_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=object_name
            )
            logger.info(f"已删除MinIO文件: {object_name}")
        except Exception as e:
            logger.warning(f"删除MinIO文件失败: {e}")
            # 继续删除数据库记录，即使文件删除失败
    
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
    
    # 获取摄像头信息
    camera_map = {}
    if services:
        from models.camera import Camera
        camera_ids = [s.camera_id for s in services if s.camera_id]
        if camera_ids:
            camera_result = await db.execute(select(Camera).where(Camera.id.in_(camera_ids)))
            cameras = camera_result.scalars().all()
            camera_map = {c.id: c.name for c in cameras}
    
    return [AIServiceResponse(
        id=service.id,
        name=service.name,
        algorithm_id=service.algorithm_id,
        algorithm_name=algorithm_map.get(service.algorithm_id, ""),
        camera_id=service.camera_id,
        camera_name=camera_map.get(service.camera_id, ""),
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
    
    # 验证摄像头是否存在
    from models.camera import Camera
    camera_result = await db.execute(select(Camera).where(Camera.id == service_data.camera_id))
    camera = camera_result.scalar_one_or_none()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的摄像头不存在"
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
        camera_id=service.camera_id,
        camera_name=camera.name,
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
@router.get("/models/", response_model=PaginatedResponse[AIModelResponse])
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
    
    # 构建基础查询
    base_query = select(AIModel)
    if conditions:
        base_query = base_query.where(and_(*conditions))
    
    # 获取总数
    count_query = select(func.count(AIModel.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 获取分页数据
    query = base_query.order_by(AIModel.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    # 获取算法信息
    algorithm_map = {}
    algorithm_type_map = {}
    if models:
        algorithm_ids = [m.algorithm_id for m in models if m.algorithm_id]
        if algorithm_ids:
            algorithm_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id.in_(algorithm_ids)))
            algorithms = algorithm_result.scalars().all()
            algorithm_map = {a.id: a.name for a in algorithms}
            algorithm_type_map = {a.id: a.algorithm_type for a in algorithms}
    
    model_responses = [AIModelResponse(
        id=model.id,
        name=model.name,
        model_type=ModelType(model.model_format) if model.model_format else ModelType.CUSTOM,
        algorithm_id=model.algorithm_id,
        algorithm_name=algorithm_map.get(model.algorithm_id, ""),
        algorithm_type=algorithm_type_map.get(model.algorithm_id, ""),
        version=model.version or "1.0.0",  # 使用模型的实际版本
        file_path=model.model_path,  # 使用正确的字段名
        file_size=model.model_size,  # 使用正确的字段名
        checksum="",  # 数据库中没有checksum字段，使用空字符串
        config={
            'input_shape': model.input_shape or {},
            'output_shape': model.output_shape or {},
            'class_names': model.class_names or []
        },
        performance_metrics={
            'accuracy': model.training_accuracy or 0.0,
            'validation_accuracy': model.validation_accuracy or 0.0,
            'inference_time': model.inference_time or 0.0
        },
        training_data_info={
            'dataset': model.training_dataset or '',
            'epochs': model.training_epochs or 0
        },
        is_active=model.is_active,
        usage_count=0,  # 数据库中没有usage_count字段，使用默认值
        created_at=model.created_at,
        updated_at=model.updated_at,
        description=model.description or "",
        tags=model.tags or []
    ) for model in models]
    
    return PaginatedResponse(
        data=model_responses,
        total=total,
        page=page,
        page_size=page_size
    )

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
    
    # 创建模型，映射字段名
    model = AIModel(
        name=model_data.name,
        algorithm_id=model_data.algorithm_id,
        model_path=model_data.file_path,  # API中的file_path映射到数据库的model_path
        model_size=model_data.file_size,  # API中的file_size映射到数据库的model_size
        model_format=model_data.model_type.value,  # API中的model_type映射到数据库的model_format
        input_shape=model_data.input_format or model_data.config.get('input_shape', {}),
        output_shape=model_data.output_format or model_data.config.get('output_shape', {}),
        class_names=model_data.config.get('class_names', []),
        training_dataset=model_data.training_data_info.get('dataset', ''),
        training_epochs=model_data.training_data_info.get('epochs', 0),
        training_accuracy=model_data.performance_metrics.get('accuracy', 0.0),
        validation_accuracy=model_data.performance_metrics.get('validation_accuracy', 0.0),
        is_active=model_data.is_active
    )
    
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    return AIModelResponse(
        id=model.id,
        name=model.name,
        model_type=ModelType(model.model_format) if model.model_format else ModelType.CUSTOM,
        algorithm_id=model.algorithm_id,
        algorithm_name=algorithm.name,
        version=model_data.version or "1.0.0",
        file_path=model.model_path,
        file_size=model.model_size,
        checksum=model_data.checksum,
        config={
            'input_shape': model.input_shape or {},
            'output_shape': model.output_shape or {},
            'class_names': model.class_names or []
        },
        input_format=model_data.input_format,
        output_format=model_data.output_format,
        performance_metrics={
            'accuracy': model.training_accuracy or 0.0,
            'validation_accuracy': model.validation_accuracy or 0.0,
            'inference_time': model.inference_time or 0.0
        },
        training_data_info={
            'dataset': model.training_dataset or '',
            'epochs': model.training_epochs or 0
        },
        tags=model_data.tags or [],
        is_active=model.is_active,
        usage_count=0,  # 新创建的模型使用次数为0
        created_at=model.created_at,
        updated_at=model.updated_at,
        description=model_data.description
    )

# 获取单个算法详情
@router.get("/algorithms/{algorithm_id}", response_model=AIAlgorithmResponse)
async def get_algorithm(
    algorithm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取算法详情"""
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
        file_path=algorithm.file_path,
        file_size=algorithm.file_size,
        checksum=algorithm.checksum,
        config=algorithm.config,
        performance_metrics=algorithm.performance_metrics,
        status=algorithm.status,
        is_active=algorithm.is_active,
        usage_count=algorithm.usage_count,
        created_at=algorithm.created_at,
        updated_at=algorithm.updated_at,
        description=algorithm.description
    )

# 更新算法
@router.put("/algorithms/{algorithm_id}", response_model=AIAlgorithmResponse)
async def update_algorithm(
    algorithm_id: int,
    algorithm_data: AIAlgorithmUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新算法"""
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
        file_path=algorithm.file_path,
        file_size=algorithm.file_size,
        checksum=algorithm.checksum,
        config=algorithm.config,
        performance_metrics=algorithm.performance_metrics,
        status=algorithm.status,
        is_active=algorithm.is_active,
        usage_count=algorithm.usage_count,
        created_at=algorithm.created_at,
        updated_at=algorithm.updated_at,
        description=algorithm.description
    )

# 删除算法
@router.delete("/algorithms/{algorithm_id}")
async def delete_algorithm(
    algorithm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除算法"""
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
            detail="无法删除算法，存在关联的服务"
        )
    
    # 删除MinIO中的文件
    if algorithm.file_path:
        try:
            minio_client = get_minio()
            # 从file_path中提取bucket和object_name
            # file_path格式: /bucket/object_name
            path_parts = algorithm.file_path.strip('/').split('/', 1)
            if len(path_parts) == 2:
                bucket_name, object_name = path_parts
                minio_client.remove_object(bucket_name, object_name)
                logger.info(f"已删除MinIO文件: {algorithm.file_path}")
            else:
                logger.warning(f"无效的文件路径格式: {algorithm.file_path}")
        except Exception as e:
            logger.error(f"删除MinIO文件失败: {algorithm.file_path}, 错误: {str(e)}")
            # 继续删除数据库记录，即使文件删除失败
    
    await db.delete(algorithm)
    await db.commit()
    
    return {"message": "算法删除成功"}

# 下载算法包
@router.get("/algorithms/{algorithm_id}/download")
async def download_algorithm(
    algorithm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载算法包文件"""
    from fastapi.responses import FileResponse
    import os
    
    result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id == algorithm_id))
    algorithm = result.scalar_one_or_none()
    if not algorithm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="算法不存在"
        )
    
    if not algorithm.file_path or not os.path.exists(algorithm.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="算法包文件不存在"
        )
    
    # 返回文件下载响应
    filename = f"{algorithm.code}_{algorithm.version}.zip"
    return FileResponse(
        path=algorithm.file_path,
        filename=filename,
        media_type='application/zip'
    )

# 获取单个服务详情
@router.get("/services/{service_id}", response_model=AIServiceResponse)
async def get_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取服务详情"""
    result = await db.execute(select(AIService).where(AIService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务不存在"
        )
    
    # 获取算法信息
    algorithm_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id == service.algorithm_id))
    algorithm = algorithm_result.scalar_one_or_none()
    algorithm_name = algorithm.name if algorithm else ""
    
    # 获取摄像头信息
    from models.camera import Camera
    camera_result = await db.execute(select(Camera).where(Camera.id == service.camera_id))
    camera = camera_result.scalar_one_or_none()
    camera_name = camera.name if camera else ""
    
    # 获取模型信息
    model_name = None
    if service.model_id:
        model_result = await db.execute(select(AIModel).where(AIModel.id == service.model_id))
        model = model_result.scalar_one_or_none()
        model_name = model.name if model else None
    
    return AIServiceResponse(
        id=service.id,
        name=service.name,
        algorithm_id=service.algorithm_id,
        algorithm_name=algorithm_name,
        camera_id=service.camera_id,
        camera_name=camera_name,
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
    
    online_services_result = await db.execute(select(func.count(AIService.id)).where(AIService.status == ServiceStatus.RUNNING))
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
    
    # 计算处理中的服务数量
    processing_services_result = await db.execute(
        select(func.count(AIService.id)).where(
            or_(
                AIService.status == ServiceStatus.STARTING,
                AIService.status == ServiceStatus.STOPPING
            )
        )
    )
    processing_services = processing_services_result.scalar()
    
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
        by_service_status=by_service_status,
        # 前端期望的字段名
        total_count=total_services,
        online_count=online_services,
        processing_count=processing_services
    )

# 更新服务
@router.put("/services/{service_id}", response_model=AIServiceResponse)
async def update_service(
    service_id: int,
    service_data: AIServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新服务"""
    result = await db.execute(select(AIService).where(AIService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务不存在"
        )
    
    update_data = service_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)
    
    await db.commit()
    await db.refresh(service)
    
    # 获取算法和模型信息
    algorithm_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id == service.algorithm_id))
    algorithm = algorithm_result.scalar_one_or_none()
    algorithm_name = algorithm.name if algorithm else ""
    
    model_name = None
    if service.model_id:
        model_result = await db.execute(select(AIModel).where(AIModel.id == service.model_id))
        model = model_result.scalar_one_or_none()
        model_name = model.name if model else None
    
    return AIServiceResponse(
        id=service.id,
        name=service.name,
        algorithm_id=service.algorithm_id,
        algorithm_name=algorithm_name,
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

# 删除服务
@router.delete("/services/{service_id}")
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除服务"""
    result = await db.execute(select(AIService).where(AIService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务不存在"
        )
    
    await db.delete(service)
    await db.commit()
    
    return {"message": "服务删除成功"}

# 启动服务
@router.post("/services/{service_id}/start")
async def start_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动服务"""
    result = await db.execute(select(AIService).where(AIService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务不存在"
        )
    
    # 检查服务是否已经在运行
    if service.status == ServiceStatus.RUNNING:
        return {"message": "服务已在运行中"}
    
    try:
        # 更新服务状态为启动中
        service.status = ServiceStatus.STARTING
        service.is_active = True
        await db.commit()
        
        # 通过AI服务监控器启动服务
        from main import ai_service_monitor
        success = await ai_service_monitor.start_service(service_id)
        
        if success:
            service.status = ServiceStatus.RUNNING
            service.is_running = True
        else:
            service.status = ServiceStatus.ERROR
            service.is_running = False
            
        await db.commit()
        
        return {"message": "服务启动成功" if success else "服务启动失败"}
        
    except Exception as e:
        logger.error(f"启动服务失败: {e}")
        service.status = ServiceStatus.ERROR
        service.is_running = False
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务启动失败: {str(e)}"
        )

# 停止服务
@router.post("/services/{service_id}/stop")
async def stop_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """停止服务"""
    result = await db.execute(select(AIService).where(AIService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务不存在"
        )
    
    # 检查服务是否已经停止
    if service.status == ServiceStatus.STOPPED:
        return {"message": "服务已停止"}
    
    try:
        # 更新服务状态为停止中
        service.status = ServiceStatus.STOPPING
        await db.commit()
        
        # 通过AI服务监控器停止服务
        from main import ai_service_monitor
        success = await ai_service_monitor.stop_service(service_id)
        
        if success:
            service.status = ServiceStatus.STOPPED
            service.is_active = False
            service.is_running = False
        else:
            service.status = ServiceStatus.ERROR
            
        await db.commit()
        
        return {"message": "服务停止成功" if success else "服务停止失败"}
        
    except Exception as e:
        logger.error(f"停止服务失败: {e}")
        service.status = ServiceStatus.ERROR
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务停止失败: {str(e)}"
        )

# 获取单个模型详情
@router.get("/models/{model_id}", response_model=AIModelResponse)
async def get_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模型详情"""
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 获取算法信息
    algorithm_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id == model.algorithm_id))
    algorithm = algorithm_result.scalar_one_or_none()
    algorithm_name = algorithm.name if algorithm else ""
    
    return AIModelResponse(
        id=model.id,
        name=model.name,
        model_type=ModelType(model.model_format) if model.model_format else ModelType.CUSTOM,
        algorithm_id=model.algorithm_id,
        algorithm_name=algorithm_name,
        version=model.version or "1.0.0",  # 使用模型的实际版本
        file_path=model.model_path,  # 使用正确的字段名
        file_size=model.model_size,  # 使用正确的字段名
        checksum="",  # 数据库中没有checksum字段，使用空字符串
        config={
            'input_shape': model.input_shape or {},
            'output_shape': model.output_shape or {},
            'class_names': model.class_names or []
        },
        performance_metrics={
            'accuracy': model.training_accuracy or 0.0,
            'validation_accuracy': model.validation_accuracy or 0.0,
            'inference_time': model.inference_time or 0.0
        },
        training_data_info={
            'dataset': model.training_dataset or '',
            'epochs': model.training_epochs or 0
        },
        is_active=model.is_active,
        usage_count=0,  # 数据库中没有usage_count字段，使用默认值
        created_at=model.created_at,
        updated_at=model.updated_at,
        description=model.description or "",
        tags=model.tags or []
    )

# 更新模型
@router.put("/models/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: int,
    model_data: AIModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新模型"""
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    update_data = model_data.dict(exclude_unset=True)
    
    # 处理性能指标字段映射
    if 'performance_metrics' in update_data:
        performance_metrics = update_data.pop('performance_metrics')
        if performance_metrics:
            if 'accuracy' in performance_metrics:
                model.training_accuracy = performance_metrics['accuracy']
            if 'validation_accuracy' in performance_metrics:
                model.validation_accuracy = performance_metrics['validation_accuracy']
            if 'inference_time' in performance_metrics:
                model.inference_time = performance_metrics['inference_time']
    
    # version字段现在已经添加到数据库模型中，可以正常更新
    
    # 更新其他字段
    for field, value in update_data.items():
        if hasattr(model, field):
            setattr(model, field, value)
    
    await db.commit()
    await db.refresh(model)
    
    # 获取算法信息
    algorithm_result = await db.execute(select(AIAlgorithm).where(AIAlgorithm.id == model.algorithm_id))
    algorithm = algorithm_result.scalar_one_or_none()
    algorithm_name = algorithm.name if algorithm else ""
    
    return AIModelResponse(
        id=model.id,
        name=model.name,
        model_type=ModelType(model.model_format) if model.model_format else ModelType.CUSTOM,
        algorithm_id=model.algorithm_id,
        algorithm_name=algorithm_name,
        version=model.version or "1.0.0",  # 使用模型的实际版本
        file_path=model.model_path,  # 使用正确的字段名
        file_size=model.model_size,  # 使用正确的字段名
        checksum="",  # 数据库中没有checksum字段，使用空字符串
        config={
            'input_shape': model.input_shape or {},
            'output_shape': model.output_shape or {},
            'class_names': model.class_names or []
        },
        performance_metrics={
            'accuracy': model.training_accuracy or 0.0,
            'validation_accuracy': model.validation_accuracy or 0.0
        },
        training_data_info={
            'dataset': model.training_dataset or '',
            'epochs': model.training_epochs or 0
        },
        is_active=model.is_active,
        usage_count=0,  # 数据库中没有usage_count字段，使用默认值
        created_at=model.created_at,
        updated_at=model.updated_at,
        description="",  # 数据库中没有description字段，使用空字符串
        tags=model.tags or []
    )

# 删除模型
@router.delete("/models/{model_id}")
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模型"""
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 检查是否有关联的服务
    service_result = await db.execute(select(AIService).where(AIService.model_id == model_id))
    if service_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除模型，存在关联的服务"
        )
    
    # 删除MinIO中的文件
    if model.model_path:
        try:
            minio_client = get_minio()
            # 从文件路径中提取对象名称
            object_name = model.model_path.replace("/api/v1/files/", "")
            minio_client.remove_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=object_name
            )
            logger.info(f"已删除MinIO文件: {object_name}")
        except Exception as e:
            logger.warning(f"删除MinIO文件失败: {e}")
            # 继续删除数据库记录，即使文件删除失败
    
    await db.delete(model)
    await db.commit()
    
    return {"message": "模型删除成功"}


@router.get("/worker/algorithms/", response_model=PaginatedResponse[AIAlgorithmResponse])
async def get_algorithms_for_worker(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(True, description="是否启用"),
    db: AsyncSession = Depends(get_db)
):
    """获取AI算法列表 - Worker节点专用（无需认证）"""
    conditions = []
    
    # 默认只返回激活的算法包
    if is_active is not None:
        conditions.append(AIAlgorithm.is_active == is_active)
    
    # 构建基础查询
    base_query = select(AIAlgorithm)
    if conditions:
        base_query = base_query.where(and_(*conditions))
    
    # 添加排序
    base_query = base_query.order_by(AIAlgorithm.created_at.desc())
    
    # 获取总数
    count_query = select(func.count(AIAlgorithm.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    offset = (page - 1) * page_size
    paginated_query = base_query.offset(offset).limit(page_size)
    
    result = await db.execute(paginated_query)
    algorithms = result.scalars().all()
    
    algorithm_responses = [AIAlgorithmResponse(
        id=algorithm.id,
        name=algorithm.name,
        code=algorithm.code,
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
        updated_at=algorithm.updated_at,
        file_path=algorithm.file_path,
        file_size=algorithm.file_size,
        file_hash=algorithm.file_hash
    ) for algorithm in algorithms]
    
    return PaginatedResponse(
        data=algorithm_responses,
        total=total,
        page=page,
        page_size=page_size
    )