import os
def get_bool_from_env(var_name, default=False):
    """从环境变量中获取布尔值。
    :param var_name: 环境变量的名称
    :param default: 如果环境变量不存在，返回的默认值
    :return: 环境变量的布尔值
    """
    value = os.getenv(var_name, str(default)).strip().lower()
    true_values = {'true', '1', 't', 'y', 'yes'}
    return value in true_values


def get_int_from_env(var_name, default):
    """从环境变量中获取整数值。
    :param var_name: 环境变量的名称
    :param default: 如果环境变量不存在，返回的默认值
    :return: 环境变量的整数值
    """
    value = os.getenv(var_name, str(default)).strip()
    return int(value)


# MinIO配置
minio_host = os.getenv('minio_host', '127.0.0.1:9000')
minio_access_key = os.getenv('minio_access_key', 'rotanova')
minio_secret_key = os.getenv('minio_secret_key', 'RotaNova@2025')
minio_bucket_name = os.getenv('minio_bucket_name', 'easysight')
minio_secure = get_bool_from_env('minio_secure', False)

# PostgreSQL数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://rotanova:RotaNova%402025@127.0.0.1:5432/easysight')

# ZLMediaKit配置
# ZLMediaKit是底层媒体服务器，负责视频流的接收、转码和分发
zlm_host = os.getenv('zlm_host', '127.0.0.1')  # ZLMediaKit服务器地址
zlm_port = get_int_from_env('zlm_port', 8060)  # ZLMediaKit HTTP API端口，用于媒体流处理和管理
zlm_secret = os.getenv('zlm_secret', '035c73f7-bb6b-4889-a715-d9eb2d1925cc')  # ZLMediaKit API密钥

# 媒体节点配置
# 媒体节点是流媒体服务的HTTP API服务，提供摄像头管理和流媒体代理功能
MEDIA_NODE_NAME = os.getenv('MEDIA_NODE_NAME', 'meida-node-default')  # 媒体节点名称
MEDIA_NODE_IP = os.getenv('MEDIA_NODE_IP', '192.168.2.177')  # 媒体节点IP地址
MEDIA_NODE_PORT = get_int_from_env('MEDIA_NODE_PORT', 18080)  # 媒体节点HTTP API端口，对外提供流媒体服务接口
MEDIA_NODE_SECRET = os.getenv('MEDIA_NODE_SECRET', 'yC7agWK36NtD6hdJIuvK9pCn60Nu39Ww')  # 媒体节点认证密钥
MEDIA_NODE_MAX_CONNECTIONS = get_int_from_env('MEDIA_NODE_MAX_CONNECTIONS', 300)  # 最大连接数限制

# 系统监控配置
SYSTEM_MONITOR_INTERVAL = get_int_from_env('SYSTEM_MONITOR_INTERVAL', 30)  # 系统监控上报间隔（秒）
SYSTEM_MONITOR_ENABLED = get_bool_from_env('SYSTEM_MONITOR_ENABLED', True)  # 是否启用系统监控

# 日志配置
LOG_DEBUG = get_bool_from_env("LOG_DEBUG", True)
LOG_FILE = os.getenv('LOG_FILE', 'logs/mediaworker.log')