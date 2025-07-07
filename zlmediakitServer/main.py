import time
import uvicorn
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from utils import zlmediaServer, minioTool, dataModel
from utils.logTool import StandardLogger
from utils.zlmediaServer import ZLMediaRestfulApi, get_video_clip_by_time
from utils.videoClean import clear_video_last_hour
from utils.minioTool import save_video
import config
from database import init_db, close_db, test_connection
from utils.dataModel import media_node_manager

# 设置日志
logger = StandardLogger('main')

check_interval = config.SYSTEM_MONITOR_INTERVAL  # 检查间隔时间，单位秒
media_worker_status = {}
stream_list = {
    "data": [],
    "update_time": time.time()-10,
}
app = FastAPI(title="ZLMediaKit Server", version="1.0.0")

# 全局变量
zlm_server = None
minio_client = None
media_node_id = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/index/hook/on_server_started")
async def handle_server_started(request: Request):
    data = await request.json()
    mylogger.info("on_server_started: {}".format(data))
    return {"code": 0, "msg": "success"}


@app.post("/index/hook/on_server_keepalive")
async def handle_keepalive(request: Request):
    data = await request.json()
    mediaServerId = data['mediaServerId']
    media_worker_status[mediaServerId] = time.time()
    await dataModel.update_media_worker_online()
    return {"code": 0, "msg": "success"}


@app.post("/index/hook/on_stream_changed")
async def handle_stream_changed(request: Request):
    data = await request.json()
    return {"code": 0, "msg": "success"}


@app.post("/index/hook/on_publish")
async def handle_publish(request: Request):
    data = await request.json()
    logger.info("on_pushlish: {}".format(data))
    return {"code": 0, "msg": "success"}


@app.post("/index/hook/on_play")
async def handle_play(request: Request):
    data = await request.json()
    return {"code": 0, "msg": "success"}


@app.post("/index/hook/on_stream_not_found")
async def handle_not_found(request: Request):
    data = await request.json()
    camera_id = data['stream']
    camera_info = await dataModel.get_camera_by_code(camera_id)
    try: 
        if camera_info and camera_info.get('media_proxy_id'):
            media_worker_info = await dataModel.media_proxy_manager.get_media_proxy_info(camera_info['media_proxy_id'])
            if media_worker_info and media_worker_info['is_online']:
                zlmediaClient = ZLMediaRestfulApi(media_worker_info['ip_address'], media_worker_info['zlm_port'], media_worker_info.get('secret_key', ''))
                # 判断 camera_info['stream_url'] 是否可访问
                # if await videoTool.check_rtsp_available(camera_info['stream_url']):
                #     data = zlmediaClient.add_stream(camera_id, camera_info['stream_url'])
                #     logger.info("add stream: {}".format(data))
                #     return {"code": 0, "msg": "success"}
                # else:
                #     logger.error("camera:{} url: {} not available".format(camera_id, camera_info['stream_url']))
                #     return {"code": 1, "msg": "rtsp url not available"}
                src_url = camera_info['stream_url'].replace("&", "%26")
                # data = zlmediaClient.add_stream(camera_id, src_url)
                loop = asyncio.get_running_loop()
                data = await loop.run_in_executor(None, zlmediaClient.add_stream, camera_id, src_url)
                logger.info("add stream: {}".format(data))
                return {"code": 0, "msg": "success"}
            else:
                return {"code": 1, "msg": "media worker offline"}
    except Exception as e:
        logger.error("on_stream_not_found error: {}".format(e))
        return {"code": 1, "msg": str(e)}


@app.post("/index/hook/on_stream_none_reader")
async def handle_none_reader(request: Request):
    data = await request.json()
    return {"code": 0, "msg": "success"}


@app.get('/get_stream_list')
async def get_stream_list():
    record_list = []
    if time.time() - stream_list['update_time'] < 10:
        record_list = stream_list['data']
    else:
        media_worker_list = await dataModel.media_proxy_manager.get_media_proxy_list()
        for media_worker_info in media_worker_list:
            if media_worker_info['is_online']:
                zlmediaClient = ZLMediaRestfulApi(media_worker_info['ip_address'], media_worker_info['zlm_port'], media_worker_info.get('secret_key', ''))
                # results = zlmediaClient.get_media_list()
                loop = asyncio.get_running_loop()
                results = await loop.run_in_executor(None, zlmediaClient.get_media_list)
                record_list.extend(results.get('data', []))
        stream_list['data'] = record_list
        stream_list['update_time'] = time.time()
    return {"code": 0, "msg": "success", "record_list": record_list}


@app.post('/delete_stream')
async def delete_stream(request: Request):
    data = await request.json()
    camera_id = data.get('camera_id', None)
    if camera_id is None:
        return {"code": 1, "msg": "Invalid request"}
    camera_info = await dataModel.get_camera_by_code(camera_id)
    try:
        if camera_info and camera_info.get('media_proxy_id'):
            media_worker_info = await dataModel.media_proxy_manager.get_media_proxy_info(camera_info['media_proxy_id'])
            if media_worker_info:
                zlmediaClient = ZLMediaRestfulApi(media_worker_info['ip_address'], media_worker_info['zlm_port'],
                                                        media_worker_info.get('secret_key', ''))
                stream_id = "__defaultVhost__/rtsp/{}".format(camera_id)
                results = zlmediaClient.del_stream(stream_id)
                if results['code'] == 0:
                    return {"code": 0, "msg": "success"}
                else:
                    return {"code": 1, "msg": results['msg']}
            else:
                return {"code": 1, "msg": "Media proxy not found"}
        else:
            return {"code": 1, "msg": "Camera not found"}
    except Exception as e:
        logger.error("delete_stream error: {}".format(e))
        return {"code": 1, "msg": str(e)}


@app.post('/get_snap')
async def get_snap(request: Request):
    data = await request.json()
    camera_id = data.get('camera_id', None)
    if camera_id is None:
        return {"code": 1, "msg": "Invalid request"}
    camera_info = await dataModel.get_camera_by_code(camera_id)
    try:
        if camera_info and camera_info.get('media_proxy_id'):
            media_worker_info = await dataModel.media_proxy_manager.get_media_proxy_info(camera_info['media_proxy_id'])
            if media_worker_info:
                zlmediaClient = ZLMediaRestfulApi(media_worker_info['ip_address'], media_worker_info['zlm_port'],
                                                        media_worker_info.get('secret_key', ''))
                snap_data = zlmediaClient.get_snap(camera_info['stream_url'])
                snap_path = '{}-snap.jpg'.format(camera_id)
                with open(snap_path, 'wb') as f:
                    f.write(snap_data)
                return FileResponse(snap_path)
            else:
                return {"code": 1, "msg": "Media proxy not found"}
        else:
            return {"code": 1, "msg": "Camera not found"}
    except Exception as e:
        logger.error("get_snap error: {}".format(e))
        return {"code": 1, "msg": str(e)}


@app.post('/get_video_clip')
async def get_video_clip(request: Request):
    data = await request.json()
    camera_id = data.get('camera_id', None)
    start_time = data.get('start_time', None)
    if camera_id is None or start_time is None:
        return {"code": 1, "msg": "Invalid request"}
    # 分布式节点下的视频文件下载, 采用分布式文件系统挂载到本地
    # 获取文件的日期
    try:
        video_path = 'mediaworker/www/record/rtsp/{}/{}'.format(camera_id, start_time[:10])
        # 获取当前绝对路径
        # current_path = os.path.abspath(os.path.dirname(__file__))
        # video_path = os.path.join(current_path, video_path)
        loop = asyncio.get_running_loop() # 异步下载
        # video_file = get_video_clip_by_time(video_path, start_time)
        video_file = await loop.run_in_executor(None, get_video_clip_by_time, video_path, start_time)
        if video_file is None:
            return {"code": 1, "msg": "No video clip found"}
        # 保存视频到minio
        formatted_time = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time.time()))
        video_list = []
        for i, file in enumerate(video_file):
            video_name = "{}-{}.mp4".format(camera_id, formatted_time)
            # video_url = save_video(video_name, file)
            video_url = await loop.run_in_executor(None, save_video, video_name, file)
            video_list.append(video_url)
        return {"code": 0, "msg": "success", "video_list": video_list}
    except Exception as e:
        logger.error("get_video_clip error: {}".format(e))
        return {"code": 1, "msg": str(e)}


async def time_job():
    """定时任务：清理过期视频和更新节点状态"""
    try:
        # 清理过期视频与文件
        import os
        current_path = os.path.abspath(os.path.dirname(__file__))
        record_path = os.path.join(current_path, 'mediaworker/www/record')
        clear_video_last_hour(record_path)
        
        # 更新媒体节点状态（包含系统监控数据）
        if config.SYSTEM_MONITOR_ENABLED:
            logger.debug("Starting system monitoring update...")
            logger.info("About to call dataModel.update_media_worker_online()")
            await dataModel.update_media_worker_online()
            logger.info("dataModel.update_media_worker_online() completed")
            logger.debug("System monitoring update completed")
        else:
            logger.debug("System monitoring is disabled")
        
        logger.debug("Time job completed")
    except Exception as e:
        logger.error(f"Time job error: {e}")
        import traceback
        logger.error(f"Time job traceback: {traceback.format_exc()}")

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global media_node_id
    
    try:
        # 初始化数据库
        await init_db()
        logger.info("Database initialized")
        
        # 测试数据库连接
        if await test_connection():
            logger.info("Database connection successful")
        else:
            logger.warning("Database connection failed, but service will continue")
        
        # 注册媒体节点
        media_node_id = await media_node_manager.register_node()
        if media_node_id:
            logger.info(f"Media node registered with ID: {media_node_id}")
        else:
            logger.warning("Failed to register media node")
        
        # 启动定时任务
        asyncio.create_task(periodic_task())
        
        logger.info("ZLMediaKit Server started successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    try:
        # 注销媒体节点
        await media_node_manager.unregister_node()
        logger.info("Media node unregistered")
        
        # 关闭数据库连接
        await close_db()
        logger.info("Database connections closed")
        
        logger.info("ZLMediaKit Server shutdown completed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

async def periodic_task():
    """周期性任务"""
    while True:
        try:
            await asyncio.sleep(check_interval)
            await time_job()
        except Exception as e:
            logger.error(f"Periodic task error: {e}")
            await asyncio.sleep(60)  # 出错时等待1分钟再重试

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=18080)