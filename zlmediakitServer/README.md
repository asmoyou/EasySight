# ZLMediaKit Server

这是EasySight项目的媒体服务器组件，基于ZLMediaKit提供视频流处理和管理功能。

## 功能特性

- 视频流管理和转发
- 摄像头流媒体处理
- 视频录制和回放
- 流媒体状态监控
- RESTful API接口

## 环境要求

- Python 3.8+
- MySQL 数据库
- MinIO 对象存储
- ZLMediaKit 媒体服务器

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `minio_host` | `192.168.2.177:9000` | MinIO服务器地址 |
| `mysql_host` | `192.168.2.177` | MySQL数据库地址 |
| `zlm_host` | `192.168.2.177` | ZLMediaKit服务器地址 |
| `LOG_DEBUG` | `False` | 是否启用调试日志 |
| `LOG_FILE` | `logs/mediaworker.log` | 日志文件路径 |

### 数据库配置

确保MySQL数据库中存在以下表：
- `easysight` - 摄像头信息表
- `media_worker` - 媒体工作节点表

## 运行服务

### 开发环境

```bash
python main.py
```

### 生产环境（Docker）

```bash
docker build -t zlmediakit-server .
docker run -p 18080:18080 zlmediakit-server
```

## API接口

### 钩子接口

- `POST /index/hook/on_server_started` - 服务器启动通知
- `POST /index/hook/on_server_keepalive` - 服务器心跳
- `POST /index/hook/on_stream_changed` - 流状态变化
- `POST /index/hook/on_publish` - 推流事件
- `POST /index/hook/on_play` - 播放事件
- `POST /index/hook/on_stream_not_found` - 流未找到事件
- `POST /index/hook/on_stream_none_reader` - 无观众事件

### 管理接口

- `GET /get_stream_list` - 获取流列表
- `POST /delete_stream` - 删除流
- `POST /get_snap` - 获取截图
- `POST /get_video_clip` - 获取视频片段

## 日志系统

项目已从Logstash日志系统迁移到标准Python日志系统：

- 控制台输出：所有日志级别
- 文件输出：可通过`LOG_FILE`环境变量配置
- 日志格式：`时间 - 模块名 - 级别 - 消息`

## 故障排除

### 数据库连接问题

如果出现数据库连接错误，请检查：
1. MySQL服务是否正常运行
2. 数据库连接参数是否正确
3. 数据库用户权限是否足够
4. 防火墙设置是否允许连接

### 常见错误

- `Host 'xxx' is not allowed to connect to this MySQL server`：需要在MySQL中授权客户端IP访问权限
- `Database connection is None`：数据库连接失败，检查连接参数和网络

## 开发说明

### 项目结构

```
zlmediakitServer/
├── main.py              # 主应用入口
├── config.py            # 配置文件
├── requirements.txt     # Python依赖
├── Dockerfile          # Docker构建文件
└── utils/              # 工具模块
    ├── logTool.py      # 日志工具
    ├── dataModel.py    # 数据模型
    ├── minioTool.py    # MinIO工具
    ├── videoTool.py    # 视频处理工具
    ├── videoClean.py   # 视频清理工具
    └── zlmediaServer.py # ZLMediaKit接口
```

### 代码修改记录

1. **日志系统迁移**：从Logstash改为标准Python日志
2. **错误处理增强**：添加数据库连接错误处理
3. **依赖修复**：修复缺失的模块导入
4. **配置优化**：简化配置参数，移除Logstash相关配置