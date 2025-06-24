FROM ubuntu:22.04

WORKDIR /rotanova_media_server

MAINTAINER QILIN "qilinyou@rotanovaiot.com"

RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN apt-get install -y python3-pip tzdata
RUN apt-get install -y ffmpeg
RUN apt-get install -y vim
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*
RUN pip install fastapi
RUN pip install requests
RUN pip install uvicorn
RUN pip install minio
RUN pip install mysql-connector-python
RUN pip install aiohttp
RUN pip install opencv-python

COPY main.py /rotanova_media_server
COPY config.py /rotanova_media_server
COPY utils/ /rotanova_media_server/utils

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Expose the port the app runs on
EXPOSE 18080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "18080"]
#CMD ["python3", "main.py"]