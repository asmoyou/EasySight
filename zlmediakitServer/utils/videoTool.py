import cv2
import os
import asyncio

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|udp|timeout;5000"


async def check_rtsp_available(rtsp_url):
    loop = asyncio.get_running_loop()

    def open_rtsp():
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            return True
        else:
            return False

    future = loop.run_in_executor(None, open_rtsp)
    avaliable_flag = await future
    return avaliable_flag