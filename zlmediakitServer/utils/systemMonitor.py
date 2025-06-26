#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控工具模块
用于收集系统资源使用情况，包括CPU、内存、磁盘、网络等
"""

import psutil
import time
import asyncio
from typing import Dict, Optional
from utils.logTool import StandardLogger

# 设置日志
logger = StandardLogger('utils.systemMonitor')

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.last_network_stats = None
        self.last_check_time = None
    
    def get_cpu_usage(self, interval: float = 1.0) -> float:
        """获取CPU使用率
        
        Args:
            interval: 采样间隔时间（秒）
            
        Returns:
            CPU使用率百分比
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=interval)
            logger.debug(f"CPU usage: {cpu_percent}%")
            return cpu_percent
        except Exception as e:
            logger.error(f"Failed to get CPU usage: {e}")
            return 0.0
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况
        
        Returns:
            包含内存使用信息的字典
        """
        try:
            memory = psutil.virtual_memory()
            memory_info = {
                'total': memory.total / (1024**3),  # GB
                'available': memory.available / (1024**3),  # GB
                'used': memory.used / (1024**3),  # GB
                'percent': memory.percent
            }
            logger.debug(f"Memory usage: {memory_info['percent']}% ({memory_info['used']:.2f}GB/{memory_info['total']:.2f}GB)")
            return memory_info
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {'total': 0, 'available': 0, 'used': 0, 'percent': 0}
    
    def get_disk_usage(self, path: str = '/') -> Dict[str, float]:
        """获取磁盘使用情况
        
        Args:
            path: 磁盘路径
            
        Returns:
            包含磁盘使用信息的字典
        """
        try:
            # Windows系统使用C盘
            if psutil.WINDOWS:
                path = 'C:\\'
            
            disk = psutil.disk_usage(path)
            disk_info = {
                'total': disk.total / (1024**3),  # GB
                'used': disk.used / (1024**3),  # GB
                'free': disk.free / (1024**3),  # GB
                'percent': (disk.used / disk.total) * 100
            }
            logger.debug(f"Disk usage: {disk_info['percent']:.2f}% ({disk_info['used']:.2f}GB/{disk_info['total']:.2f}GB)")
            return disk_info
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}
    
    def get_network_usage(self) -> Dict[str, float]:
        """获取网络使用情况
        
        Returns:
            包含网络使用信息的字典
        """
        try:
            current_stats = psutil.net_io_counters()
            current_time = time.time()
            
            network_info = {
                'bytes_sent': current_stats.bytes_sent / (1024**2),  # MB
                'bytes_recv': current_stats.bytes_recv / (1024**2),  # MB
                'packets_sent': current_stats.packets_sent,
                'packets_recv': current_stats.packets_recv,
                'send_rate': 0.0,  # MB/s
                'recv_rate': 0.0   # MB/s
            }
            
            # 计算网络速率（需要两次采样）
            if self.last_network_stats and self.last_check_time:
                time_diff = current_time - self.last_check_time
                if time_diff > 0:
                    send_diff = (current_stats.bytes_sent - self.last_network_stats.bytes_sent) / (1024**2)
                    recv_diff = (current_stats.bytes_recv - self.last_network_stats.bytes_recv) / (1024**2)
                    network_info['send_rate'] = send_diff / time_diff
                    network_info['recv_rate'] = recv_diff / time_diff
            
            # 更新上次统计数据
            self.last_network_stats = current_stats
            self.last_check_time = current_time
            
            logger.debug(f"Network usage - Send: {network_info['send_rate']:.2f}MB/s, Recv: {network_info['recv_rate']:.2f}MB/s")
            return network_info
        except Exception as e:
            logger.error(f"Failed to get network usage: {e}")
            return {'bytes_sent': 0, 'bytes_recv': 0, 'packets_sent': 0, 'packets_recv': 0, 'send_rate': 0, 'recv_rate': 0}
    
    def get_process_count(self) -> int:
        """获取当前进程数量
        
        Returns:
            进程数量
        """
        try:
            process_count = len(psutil.pids())
            logger.debug(f"Process count: {process_count}")
            return process_count
        except Exception as e:
            logger.error(f"Failed to get process count: {e}")
            return 0
    
    def get_system_info(self) -> Dict[str, any]:
        """获取系统基本信息
        
        Returns:
            包含系统信息的字典
        """
        try:
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            system_info = {
                'platform': psutil.WINDOWS and 'Windows' or psutil.LINUX and 'Linux' or 'Unknown',
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'boot_time': boot_time,
                'uptime_hours': uptime / 3600,
                'process_count': self.get_process_count()
            }
            
            logger.debug(f"System info: {system_info['platform']}, CPU: {system_info['cpu_count']}/{system_info['cpu_count_logical']}, Uptime: {system_info['uptime_hours']:.2f}h")
            return system_info
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {'platform': 'Unknown', 'cpu_count': 0, 'cpu_count_logical': 0, 'boot_time': 0, 'uptime_hours': 0, 'process_count': 0}
    
    async def get_all_metrics(self) -> Dict[str, any]:
        """异步获取所有系统指标
        
        Returns:
            包含所有系统指标的字典
        """
        try:
            # 在线程池中执行CPU监控（因为需要阻塞等待）
            loop = asyncio.get_event_loop()
            cpu_usage = await loop.run_in_executor(None, self.get_cpu_usage, 0.5)
            
            # 其他指标可以同步获取
            memory_info = self.get_memory_usage()
            disk_info = self.get_disk_usage()
            network_info = self.get_network_usage()
            system_info = self.get_system_info()
            
            metrics = {
                'timestamp': time.time(),
                'cpu': {
                    'usage_percent': cpu_usage,
                    'count': system_info['cpu_count'],
                    'count_logical': system_info['cpu_count_logical']
                },
                'memory': memory_info,
                'disk': disk_info,
                'network': network_info,
                'system': system_info
            }
            
            logger.info(f"System metrics collected - CPU: {cpu_usage:.1f}%, Memory: {memory_info['percent']:.1f}%, Disk: {disk_info['percent']:.1f}%")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}
    
    def get_bandwidth_usage(self) -> float:
        """获取带宽使用率（简化版本，返回网络总速率）
        
        Returns:
            带宽使用率（MB/s）
        """
        try:
            network_info = self.get_network_usage()
            bandwidth_usage = network_info['send_rate'] + network_info['recv_rate']
            logger.debug(f"Bandwidth usage: {bandwidth_usage:.2f}MB/s")
            return bandwidth_usage
        except Exception as e:
            logger.error(f"Failed to get bandwidth usage: {e}")
            return 0.0

# 创建全局系统监控实例
system_monitor = SystemMonitor()

# 便捷函数
async def get_system_metrics() -> Dict[str, any]:
    """获取系统指标的便捷函数"""
    return await system_monitor.get_all_metrics()

def get_cpu_usage() -> float:
    """获取CPU使用率的便捷函数"""
    return system_monitor.get_cpu_usage(interval=0.1)

def get_memory_usage() -> float:
    """获取内存使用率的便捷函数"""
    memory_info = system_monitor.get_memory_usage()
    return memory_info['percent']

def get_bandwidth_usage() -> float:
    """获取带宽使用率的便捷函数"""
    return system_monitor.get_bandwidth_usage()

# 创建全局系统监控实例
system_monitor = SystemMonitor()