import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, Any

# 日志配置类
class LoggingConfig:
    """日志配置管理类"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # 从环境变量读取配置
        self.enable_db_logging = os.getenv("ENABLE_DB_LOGGING", "true").lower() == "true"
        self.enable_detailed_logging = os.getenv("ENABLE_DETAILED_LOGGING", "false").lower() == "true"
        self.enable_performance_monitoring = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.max_log_file_size = int(os.getenv("MAX_LOG_FILE_SIZE", "10485760"))  # 10MB
        self.max_log_files = int(os.getenv("MAX_LOG_FILES", "5"))
        
        # 性能阈值配置
        self.slow_request_threshold = float(os.getenv("SLOW_REQUEST_THRESHOLD", "1000"))  # 毫秒
        self.very_slow_request_threshold = float(os.getenv("VERY_SLOW_REQUEST_THRESHOLD", "5000"))  # 毫秒
        
        # 排除路径配置
        self.excluded_paths = [
            "/docs", "/redoc", "/openapi.json", "/favicon.ico",
            "/static", "/health", "/metrics", "/ping"
        ]
        
        # 敏感信息过滤
        self.sensitive_headers = [
            "authorization", "cookie", "x-api-key", "x-auth-token"
        ]
        
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 设置根日志级别
        logging.getLogger().setLevel(getattr(logging, self.log_level))
        
        # 设置文件日志处理器（带轮转）
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "middleware.log",
            maxBytes=self.max_log_file_size,
            backupCount=self.max_log_files
        )
        file_handler.setFormatter(formatter)
        
        # 设置性能日志处理器
        if self.enable_performance_monitoring:
            perf_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "performance.log",
                maxBytes=self.max_log_file_size,
                backupCount=self.max_log_files
            )
            perf_handler.setFormatter(formatter)
            
            # 创建性能日志记录器
            perf_logger = logging.getLogger("middleware.performance")
            perf_logger.addHandler(perf_handler)
            perf_logger.setLevel(logging.INFO)
    
    def should_log_request(self, path: str, method: str) -> bool:
        """判断是否应该记录请求"""
        # 检查排除路径
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return False
        
        # 排除OPTIONS请求
        if method == "OPTIONS":
            return False
        
        return True
    
    def filter_sensitive_data(self, headers: Dict[str, str]) -> Dict[str, str]:
        """过滤敏感信息"""
        filtered_headers = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                filtered_headers[key] = "***FILTERED***"
            else:
                filtered_headers[key] = value
        return filtered_headers
    
    def get_performance_level(self, response_time: float) -> str:
        """根据响应时间获取性能级别"""
        if response_time >= self.very_slow_request_threshold:
            return "CRITICAL"
        elif response_time >= self.slow_request_threshold:
            return "WARNING"
        else:
            return "NORMAL"
    
    def to_dict(self) -> Dict[str, Any]:
        """返回配置字典"""
        return {
            "enable_db_logging": self.enable_db_logging,
            "enable_detailed_logging": self.enable_detailed_logging,
            "enable_performance_monitoring": self.enable_performance_monitoring,
            "log_level": self.log_level,
            "slow_request_threshold": self.slow_request_threshold,
            "very_slow_request_threshold": self.very_slow_request_threshold,
            "excluded_paths": self.excluded_paths
        }

# 全局配置实例
logging_config = LoggingConfig()