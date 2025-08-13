import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
import aio_pika
from aio_pika import Message, DeliveryMode
from database import get_rabbitmq_connection
from config import settings

logger = logging.getLogger(__name__)

class TaskQueueManager:
    """基于RabbitMQ的任务队列管理器"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchanges: Dict[str, aio_pika.Exchange] = {}
        self.queues: Dict[str, aio_pika.Queue] = {}
        self.consumers: Dict[str, Callable] = {}
        
    async def connect(self):
        """连接到RabbitMQ"""
        try:
            self.connection = await get_rabbitmq_connection()
            self.channel = await self.connection.channel()
            
            # 设置QoS，确保每个worker一次只处理一个任务
            await self.channel.set_qos(prefetch_count=1)
            
            # 创建交换机
            await self._create_exchanges()
            
            # 创建队列
            await self._create_queues()
            
            logger.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def _create_exchanges(self):
        """创建交换机"""
        # 任务分发交换机
        self.exchanges['tasks'] = await self.channel.declare_exchange(
            'easysight.tasks',
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        # 任务结果交换机
        self.exchanges['results'] = await self.channel.declare_exchange(
            'easysight.results',
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        # 心跳交换机
        self.exchanges['heartbeat'] = await self.channel.declare_exchange(
            'easysight.heartbeat',
            aio_pika.ExchangeType.FANOUT,
            durable=True
        )
    
    async def _create_queues(self):
        """创建队列"""
        # 诊断任务队列
        self.queues['diagnosis_tasks'] = await self.channel.declare_queue(
            'diagnosis.tasks',
            durable=True,
            arguments={
                'x-message-ttl': 3600000,  # 1小时TTL
                'x-max-priority': 10  # 支持优先级
            }
        )
        
        # 事件任务队列
        self.queues['event_tasks'] = await self.channel.declare_queue(
            'event.tasks',
            durable=True,
            arguments={
                'x-message-ttl': 3600000,
                'x-max-priority': 10
            }
        )
        
        # AI服务任务队列
        self.queues['ai_service_tasks'] = await self.channel.declare_queue(
            'ai_service.tasks',
            durable=True,
            arguments={
                'x-message-ttl': 3600000,
                'x-max-priority': 10
            }
        )
        
        # 任务结果队列
        self.queues['task_results'] = await self.channel.declare_queue(
            'task.results',
            durable=True
        )
        
        # Worker心跳队列
        self.queues['worker_heartbeat'] = await self.channel.declare_queue(
            'worker.heartbeat',
            durable=False,
            auto_delete=True
        )
        
        # 绑定队列到交换机
        await self._bind_queues()
    
    async def _bind_queues(self):
        """绑定队列到交换机"""
        # 任务队列绑定
        await self.queues['diagnosis_tasks'].bind(
            self.exchanges['tasks'], 'diagnosis'
        )
        await self.queues['event_tasks'].bind(
            self.exchanges['tasks'], 'event'
        )
        await self.queues['ai_service_tasks'].bind(
            self.exchanges['tasks'], 'ai_service'
        )
        
        # 结果队列绑定
        await self.queues['task_results'].bind(
            self.exchanges['results'], 'result'
        )
        
        # 心跳队列绑定
        await self.queues['worker_heartbeat'].bind(
            self.exchanges['heartbeat']
        )
    
    async def publish_task(self, task_type: str, task_data: Dict[str, Any], 
                          priority: int = 5, delay: int = 0) -> bool:
        """发布任务到队列"""
        try:
            message_body = {
                'task_id': task_data.get('task_id'),
                'task_type': task_type,
                'data': task_data,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'priority': priority
            }
            
            message = Message(
                json.dumps(message_body).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                priority=priority,
                timestamp=datetime.now(timezone.utc)
            )
            
            # 如果有延迟，设置延迟投递
            if delay > 0:
                message.headers = {'x-delay': delay * 1000}  # 毫秒
            
            # 根据任务类型选择路由键
            routing_key = self._get_routing_key(task_type)
            
            await self.exchanges['tasks'].publish(
                message, routing_key=routing_key
            )
            
            logger.info(f"Published {task_type} task {task_data.get('task_id')} to queue")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish task: {e}")
            return False
    
    def _get_routing_key(self, task_type: str) -> str:
        """根据任务类型获取路由键"""
        routing_map = {
            'diagnosis': 'diagnosis',
            'event': 'event',
            'ai_service': 'ai_service'
        }
        return routing_map.get(task_type, 'diagnosis')
    
    async def consume_tasks(self, task_type: str, callback: Callable):
        """消费任务队列"""
        try:
            queue_name = f"{task_type}_tasks"
            if queue_name not in self.queues:
                logger.error(f"Queue {queue_name} not found")
                return
            
            queue = self.queues[queue_name]
            
            async def process_message(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        task_data = json.loads(message.body.decode())
                        logger.info(f"Processing {task_type} task: {task_data.get('task_id')}")
                        
                        # 调用回调函数处理任务
                        result = await callback(task_data)
                        
                        # 检查是否被拒绝（worker忙碌）
                        if result and result.get('rejected', False):
                            logger.info(f"Task {task_data.get('task_id')} rejected by worker, will be retried by another worker")
                            # 延迟重新发布任务，让其他worker有机会处理
                            await asyncio.sleep(1)
                            await self.publish_task(task_type, task_data, delay=2)
                        elif result:
                            # 发布任务结果
                            await self.publish_result(task_data.get('task_id'), result)
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        # 消息会被重新投递
                        raise
            
            # 开始消费
            await queue.consume(process_message)
            logger.info(f"Started consuming {task_type} tasks")
            
        except Exception as e:
            logger.error(f"Failed to start consuming {task_type} tasks: {e}")
    
    async def publish_result(self, task_id: str, result: Dict[str, Any]):
        """发布任务结果"""
        try:
            message_body = {
                'task_id': task_id,
                'result': result,
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
            
            message = Message(
                json.dumps(message_body).encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            )
            
            await self.exchanges['results'].publish(
                message, routing_key='result'
            )
            
            logger.info(f"Published result for task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish result: {e}")
    
    async def publish_heartbeat(self, worker_id: str, worker_info: Dict[str, Any]):
        """发布Worker心跳"""
        try:
            message_body = {
                'worker_id': worker_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'info': worker_info
            }
            
            message = Message(
                json.dumps(message_body).encode(),
                delivery_mode=DeliveryMode.NOT_PERSISTENT
            )
            
            await self.exchanges['heartbeat'].publish(message, routing_key=worker_id)
            
        except Exception as e:
            logger.error(f"Failed to publish heartbeat: {e}")
    
    def is_connected(self) -> bool:
        """检查是否连接到RabbitMQ"""
        return self.connection is not None and not self.connection.is_closed
    
    async def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """获取队列信息"""
        try:
            if queue_name in self.queues:
                queue = self.queues[queue_name]
                # 获取队列状态
                return {
                    'name': queue_name,
                    'message_count': queue.declaration_result.message_count,
                    'consumer_count': queue.declaration_result.consumer_count
                }
        except Exception as e:
            logger.error(f"Failed to get queue info: {e}")
        return {}
    
    async def close(self):
        """关闭连接"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")

# 全局任务队列管理器实例
task_queue_manager = TaskQueueManager()