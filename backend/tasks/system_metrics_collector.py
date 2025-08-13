import asyncio
import logging
import psutil
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db
from models.system import SystemMetrics

logger = logging.getLogger(__name__)

class SystemMetricsCollector:
    """系统指标收集器"""
    
    def __init__(self):
        self.is_running = False
        self.collection_interval = 60  # 每60秒收集一次
        
    async def start(self):
        """启动指标收集"""
        if self.is_running:
            logger.warning("系统指标收集器已在运行")
            return
            
        self.is_running = True
        logger.info("启动系统指标收集器")
        
        while self.is_running:
            try:
                await self.collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"收集系统指标时发生错误: {e}")
                await asyncio.sleep(self.collection_interval)
                
    async def stop(self):
        """停止指标收集"""
        self.is_running = False
        logger.info("停止系统指标收集器")
        
    async def collect_metrics(self):
        """收集系统指标"""
        try:
            async for db in get_db():
                timestamp = datetime.now(timezone.utc)
                
                # 收集CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                await self.save_metric(db, "cpu_usage", cpu_percent, "%", timestamp)
                
                # 收集内存使用率
                memory = psutil.virtual_memory()
                await self.save_metric(db, "memory_usage", memory.percent, "%", timestamp)
                await self.save_metric(db, "memory_total", memory.total / (1024**3), "GB", timestamp)
                await self.save_metric(db, "memory_available", memory.available / (1024**3), "GB", timestamp)
                
                # 收集磁盘使用率
                disk_partitions = psutil.disk_partitions()
                for partition in disk_partitions:
                    try:
                        disk_usage = psutil.disk_usage(partition.mountpoint)
                        disk_percent = (disk_usage.used / disk_usage.total) * 100
                        
                        dimensions = {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype
                        }
                        
                        await self.save_metric(
                            db, "disk_usage", disk_percent, "%", timestamp, dimensions
                        )
                        await self.save_metric(
                            db, "disk_total", disk_usage.total / (1024**3), "GB", timestamp, dimensions
                        )
                        await self.save_metric(
                            db, "disk_free", disk_usage.free / (1024**3), "GB", timestamp, dimensions
                        )
                    except (PermissionError, OSError) as e:
                        logger.warning(f"无法访问磁盘分区 {partition.device}: {e}")
                        continue
                
                # 收集网络IO
                net_io = psutil.net_io_counters()
                if net_io:
                    await self.save_metric(db, "network_bytes_sent", net_io.bytes_sent / (1024**2), "MB", timestamp)
                    await self.save_metric(db, "network_bytes_recv", net_io.bytes_recv / (1024**2), "MB", timestamp)
                
                # 收集进程数
                process_count = len(psutil.pids())
                await self.save_metric(db, "process_count", process_count, "count", timestamp)
                
                await db.commit()
                logger.debug(f"成功收集系统指标: {timestamp}")
                break
                
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            
    async def save_metric(self, db: AsyncSession, metric_name: str, metric_value: float, 
                         metric_unit: str, timestamp: datetime, dimensions: dict = None):
        """保存指标到数据库"""
        try:
            metric = SystemMetrics(
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
                dimensions=dimensions or {},
                timestamp=timestamp
            )
            
            db.add(metric)
            
        except Exception as e:
            logger.error(f"保存指标 {metric_name} 失败: {e}")
            
    async def cleanup_old_metrics(self, days: int = 30):
        """清理旧的指标数据"""
        try:
            async for db in get_db():
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                
                # 删除超过指定天数的指标数据
                result = await db.execute(
                    delete(SystemMetrics).where(SystemMetrics.timestamp < cutoff_date)
                )
                    
                await db.commit()
                logger.info(f"清理了 {result.rowcount} 条旧指标数据")
                break
                
        except Exception as e:
            logger.error(f"清理旧指标数据失败: {e}")

# 全局实例
metrics_collector = SystemMetricsCollector()

async def start_metrics_collection():
    """启动指标收集"""
    await metrics_collector.start()
    
async def stop_metrics_collection():
    """停止指标收集"""
    await metrics_collector.stop()