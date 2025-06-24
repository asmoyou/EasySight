import os
import time
import shutil
import config
from utils import logTool
# set logger
mylogger = logTool.StandardLogger('utils.videoClean')


def clear_video_last_hour(video_path):
    try:
        for file in os.listdir(video_path):
            if os.path.isdir(os.path.join(video_path, file)):  # 如果是文件夹
                # 判断文件名是否为时间格式YYYY-MM-DD
                if len(file) == 10 and file[4] == '-' and file[7] == '-':
                    # 清除2天前的文件夹
                    if time.time() - time.mktime(time.strptime(file, '%Y-%m-%d')) > 172800:
                        shutil.rmtree(os.path.join(video_path, file))
                        continue  # 跳过后续操作
                clear_video_last_hour(os.path.join(video_path, file))
            if file.endswith('.mp4'):
                if file.startswith('.'):  # 跳过隐藏和正在写入的文件
                    continue
                # 查看文件时间
                file_path = os.path.join(video_path, file)
                modify_time = os.path.getmtime(file_path)
                # 如果文件时间超过3小时，则删除
                if modify_time < time.time() - 10800:
                    os.remove(file_path)
    except Exception as e:
        mylogger.error(f"Clear video failed: {e}")


if __name__ == "__main__":
    clear_video_last_hour('../mediaworker/www/record')