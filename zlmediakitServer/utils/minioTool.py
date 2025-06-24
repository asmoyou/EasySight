from minio import Minio
from datetime import timedelta
import config
from utils import logTool
# set logger
mylogger = logTool.StandardLogger('utils.minioTool')

class MinioTool:
    def __init__(self, endpoint, access_key, secret_key):
        self.client = Minio(endpoint, access_key, secret_key, secure=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def check_event_videos_bucket(self):
        # 判断是否存在event_frames桶
        if not self.client.bucket_exists("event-videos"):
            mylogger.info("Bucket event-videos not exists, creating...")
            self.client.make_bucket("event-videos")
        else:
            mylogger.info("Bucket event-videos exists")

    def list_buckets(self):
        return self.client.list_buckets()

    def list_objects(self, bucket_name):
        return self.client.list_objects(bucket_name)

    def get_object(self, bucket_name, object_name):
        return self.client.get_object(bucket_name, object_name)

    def put_object(self, bucket_name, object_name, data, length, part_size=10*1024*1024):
        return self.client.put_object(bucket_name, object_name, data, length, part_size=part_size)

    def remove_object(self, bucket_name, object_name):
        return self.client.remove_object(bucket_name, object_name)

    def make_bucket(self, bucket_name):
        return self.client.make_bucket(bucket_name)

    def remove_bucket(self, bucket_name):
        return self.client.remove_bucket(bucket_name)

    def get_presigned_url(self, bucket_name, object_name, expiry=timedelta(days=7)):
        return self.client.presigned_get_object(bucket_name, object_name, expiry)


def minio_init():
    with MinioTool(config.minio_host, "rotanova", "RotaNova@2023") as minio_tool:
        minio_tool.check_event_videos_bucket()


def save_video(video_name, video_path):
    with MinioTool(config.minio_host, "rotanova", "RotaNova@2023") as minio_tool:
        with open(video_path, "rb") as video_file:
            minio_tool.put_object("event-videos", video_name, video_file, -1)  # 设置length为-1，表示未知长度，minio会处理整个文件流
        return minio_tool.get_presigned_url("event-videos", video_name)


if __name__ == "__main__":
    # minio_init()
    video_path = "../mediaworker/www/record/rtsp/test/2024-08-26/22-43-38-1.mp4"
    # with open(video_path, "rb") as f:
    #     video_data = f.read()
    print(save_video("test.mp4", video_path))