# EasySight 流媒体服务端口配置说明

## 端口架构概览

EasySight 流媒体服务采用双层架构，包含两个主要服务和多个协议端口：

### 主要服务端口

| 服务 | 端口 | 用途 | 配置文件 |
|------|------|------|----------|
| **EasySight 主服务 HTTP API** | 8000 | EasySight 智能安防平台的主要API接口 | `config.py` |
| **ZLMediaKit HTTP API** | 8060 | 底层媒体服务器管理接口 | `mediaworker/config.ini` |

### 流媒体协议端口

| 协议 | 端口 | 用途 | 说明 |
|------|------|------|------|
| **RTSP** | 554 | 接收摄像头视频流 | 摄像头推流的标准端口 |
| **RTMP** | 1935 | RTMP推流和播放 | 支持直播推流 |
| **RTP代理** | 10000 | RTP流代理 | 用于RTP流转发 |
| **WebRTC** | 8000 | WebRTC通信 | 实时音视频通信 |
| **SRT** | 9000 | SRT流传输 | 低延迟流传输协议 |

## 服务架构说明

```
用户/前端应用
      ↓
EasySight 主服务 (8000)
      ↓
ZLMediaKit 流媒体服务 (18080)
      ↓
ZLMediaKit 媒体服务器 (8060)
      ↓
摄像头设备 (RTSP/RTMP)
```

### 数据流向
1. **前端请求**: 用户通过前端应用访问 `8000` 端口的 EasySight 主服务
2. **流媒体管理**: 主服务通过 `18080` 端口与流媒体服务通信
3. **媒体服务**: 流媒体服务通过 `8060` 端口与 ZLMediaKit 媒体服务器通信
4. **媒体处理**: ZLMediaKit 处理来自摄像头的 RTSP/RTMP 流
5. **流分发**: 处理后的媒体流通过各协议端口分发给客户端

### 1. 流媒体服务 (端口 18080)
- **作用**: 提供摄像头管理、流媒体代理等高级功能
- **技术**: FastAPI + Python
- **主要功能**:
  - 摄像头CRUD操作
  - 流媒体节点管理
  - 系统监控和状态上报
  - 与后端系统的接口对接

### 2. ZLMediaKit 服务 (端口 8060)
- **作用**: 底层媒体服务器，负责视频流的接收、转码和分发
- **技术**: C++ 媒体服务器
- **主要功能**:
  - 视频流接收和处理
  - 多协议支持 (RTSP/RTMP/HTTP-FLV/HLS等)
  - 实时转码和格式转换
  - 流媒体分发

## 视频流处理流程

### 1. 摄像头接入
```
摄像头 → RTSP(554) → ZLMediaKit(8060) → 流媒体服务(18080) → EasySight主服务(8000) → 前端
```

### 2. 流媒体转换
- **输入**: RTSP 流 (端口 554)
- **处理**: ZLMediaKit 进行协议转换和编码优化
- **管理**: 流媒体服务 (18080) 负责流的添加、删除和监控
- **接口**: EasySight 主服务 (8000) 提供统一的 API 接口
- **输出**: HTTP-FLV, WebRTC, HLS 等多种格式
- **分发**: 通过不同端口提供给客户端

## 环境变量配置

所有端口都支持通过环境变量进行配置：

```bash
# 流媒体服务端口
export MEDIA_NODE_PORT=18080

# ZLMediaKit端口
export zlm_port=8060

# 其他配置
export zlm_host=127.0.0.1
export zlm_secret=your-secret-key
```

## 防火墙配置建议

### 生产环境必须开放的端口
- **18080**: 流媒体服务API (对内网开放)
- **8060**: ZLMediaKit API (仅本地访问)
- **554**: RTSP协议 (对摄像头网段开放)

### 可选端口 (根据需求开放)
- **1935**: RTMP推流 (如需支持RTMP推流)
- **8000**: WebRTC (如需支持WebRTC)
- **9000**: SRT (如需支持SRT协议)

## 健康检查

### 检查服务状态
```bash
# 检查 EasySight 主服务
curl http://localhost:8000/health

# 检查流媒体服务
curl http://localhost:18080/health

# 检查 ZLMediaKit
curl http://localhost:8060/index/api/getServerConfig
```

### 使用健康检查脚本
```bash
# 运行自动化健康检查
python health_check.py
```

## 故障排查

### 常见问题
1. **端口冲突**: 检查端口是否被其他服务占用
2. **防火墙阻塞**: 确认相关端口已正确开放
3. **配置不一致**: 检查配置文件中的端口设置
4. **服务未启动**: 确认两个服务都已正常启动

### 日志查看
- 流媒体服务日志: `logs/mediaworker.log`
- ZLMediaKit日志: 控制台输出

## 性能优化建议

1. **端口绑定**: 在多网卡环境下，明确指定服务绑定的IP地址
2. **连接数限制**: 根据硬件配置调整 `MEDIA_NODE_MAX_CONNECTIONS`
3. **缓冲区大小**: 根据网络环境调整各协议的缓冲区设置
4. **编码参数**: 根据带宽和质量要求调整视频编码参数