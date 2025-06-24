import logging
import config
from datetime import datetime
import os


class StandardLogger(logging.Logger):
    def __init__(self, name, level=logging.INFO):
        super(StandardLogger, self).__init__(name, level)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)
        
        # 添加文件处理器（可选）
        if hasattr(config, 'LOG_FILE') and config.LOG_FILE:
            # 确保日志目录存在
            log_dir = os.path.dirname(config.LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)
        
        # 设置日志级别
        if config.LOG_DEBUG:
            self.setLevel(logging.DEBUG)
        else:
            self.setLevel(logging.INFO)

    def info(self, msg, *args, **kwargs):
        super(StandardLogger, self).info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        super(StandardLogger, self).error(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        super(StandardLogger, self).warning(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        super(StandardLogger, self).critical(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        super(StandardLogger, self).debug(msg, *args, **kwargs)


# 为了保持向后兼容性，创建一个别名
logstashLogger = StandardLogger


def get_logger(name):
    """获取标准日志记录器的便捷函数"""
    return StandardLogger(name)


if __name__ == "__main__":
    logger = StandardLogger("test")
    logger.critical("this is a custom log message")
    logger.info("this is an info message")
    logger.debug("this is a debug message")