import aiohttp
import json
import asyncio
import time
import requests
import os
import subprocess
from utils import logTool
import config
# set logger
mylogger = logTool.StandardLogger('utils.zlmediaServer')

vhost='__defaultVhost__'
# vhost = '192.168.2.177'

class ZLMediaRestfulApi:
    def __init__(self, host, port, secret):
        self.host = host
        self.port = port
        self.secret = secret
        self.headers = {
            'Content-Type': 'application/json'
        }

    def get_media_list(self):
        url = f'http://{self.host}:{self.port}/index/api/getMediaList?secret={self.secret}'
        response = requests.post(url, headers=self.headers)
        return response.json()

    def add_stream(self, stream_id: str, media_url: str):
        url = (f'http://{self.host}:{self.port}/index/api/addStreamProxy?secret={self.secret}&'
               f'vhost={vhost}&app=rtsp&stream={stream_id}&url={media_url}&auto_close=0&rtp_type=0&timeout_sec=30&'
               f'enable_mp4=1&mp4_max_second=1&enable_hls=0&enable_rtsp=0&enable_ts=0&enable_audio=0')
        response = requests.post(url, headers=self.headers)
        return response.json()

    def del_stream(self, key):
        url = f'http://{self.host}:{self.port}/index/api/delStreamProxy?secret={self.secret}&key={key}'
        response = requests.post(url, headers=self.headers)
        return response.json()

    async def add_ffmpeg_stream(self, stream_id: str, media_url: str):
        url = (f'http://{self.host}:{self.port}/index/api/addFFmpegSource?secret={self.secret}&'
               f'src_url={media_url}&dst_url=rtmp://127.0.0.1:1935/rtsp/{stream_id}&timeout_ms=10000&'
               f'enable_hls=0&enable_mp4=1&ffmpeg_cmd_key=ffmpeg.cmd')
        # response = requests.post(url, headers=self.headers)
        # return response.json()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers) as response:
                return await response.json()

    async def del_ffmpeg_stream(self, stream_id: str):
        url = (f'http://{self.host}:{self.port}/index/api/delFFmpegSource?secret={self.secret}&'
               f'key={stream_id}')
        response = requests.post(url, headers=self.headers)
        return response.json()

    def get_snap(self, media_url):
        url = (f'http://{self.host}:{self.port}/index/api/getSnap?secret={self.secret}&url={media_url}&'
               f'timeout_sec=5&expire_sec=5')
        response = requests.post(url, headers=self.headers)
        return response.content

    def get_record_file(self, stream_id, period):
        url = (f'http://{self.host}:{self.port}/index/api/getMp4RecordFile?secret={self.secret}&'
               f'vhost={vhost}&app=rtsp&stream={stream_id}&period={period}')
        response = requests.post(url, headers=self.headers)
        return response.json()


def merge_videos(video_list, output_path):
    # 通过ffmpeg concat合并视频
    ffmpeg_exec = "ffmpeg"
    file_list_path = output_path.replace('.mp4', '.txt')
    with open(file_list_path, 'w') as f:
        for video in video_list:
            concat_video1_path = os.path.basename(video['file'])
            f.write(f'file ../{concat_video1_path}\n')
    command = [ffmpeg_exec, '-f', 'concat', '-safe', '0', '-i', file_list_path, '-c:v', 'copy', '-an',
            output_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_video_clip_by_time(video_path, start_time):
    start_time_stamp = time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
    merge_video_path = os.path.join(video_path, 'merge')
    if not os.path.exists(merge_video_path):
        os.makedirs(merge_video_path)
    # 找到2个距离start_time最近的文件
    target_list = []
    for file in os.listdir(video_path):
        if file.startswith('.'):  # 忽略隐藏文件
            continue
        if file.endswith('.mp4'):
            file_create_time = os.path.getctime(os.path.join(video_path, file))
            if start_time_stamp-15 <= file_create_time <= start_time_stamp+5:
                target_list.append({'file': os.path.join(video_path, file), 'create_time': file_create_time})
    if len(target_list) < 5:
        return None
    target_list.sort(key=lambda x: x['create_time'])
    # 选择时间差最小的2个文件
    try:
        final_file_path = os.path.join(merge_video_path, '{}.mp4'.format(start_time_stamp))
        # 判断final_file_path是否存在
        if not os.path.exists(final_file_path):
            merge_videos(target_list, final_file_path)
        return [final_file_path]
    except Exception as e:
        mylogger.error('Merge video failed: {}'.format(e))
        return [target_list[-1]['file']]


if __name__ == '__main__':
    pass
    # result = get_video_clip_by_time('../mediaworker/www/record/rtsp/35000000071329010002/2024-08-27', '2024-08-27 02:07:12')
    # print(result)
    zlmedia = ZLMediaRestfulApi('192.168.2.177', 8060, 'yC7agWK36NtD6hdJIuvK9pCn60Nu39Ww')
    # print(zlmedia.add_stream('test', 'rtsp://admin:HTcf@2022!@35.46.9.130:554/unicast/c1/s0/live'))
    # print(zlmedia.del_stream(f'{vhost}/rtsp/test'))
    # start_time = time.time()
    img_data =zlmedia.get_snap('rtsp://admin:HTcf@2022!@35.46.9.130:554/unicast/c1/s1/live')
    # with open('snap.jpg', 'wb') as f:
    #     f.write(img_data)
    # print("time: ", time.time()-start_time)
    # time.sleep(1)
    # results = zlmedia.get_media_list()
    # record_list = results.get('data', [])
    # for record in record_list:
    #     print(record)
    # # print(zlmedia.get_record_file('test', '2024-08-26'))
