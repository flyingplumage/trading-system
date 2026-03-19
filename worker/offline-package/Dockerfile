# Iris Worker - 国内镜像源版本
# 使用官方镜像 + 国内加速

FROM python:3.10-slim

# 设置国内 pip 源
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV DEBIAN_FRONTEND=noninteractive

# 使用国内 apt 源
RUN echo "deb http://mirrors.tencentyun.com/ubuntu/ jammy main restricted universe multiverse" > /etc/apt/sources.list && \
    echo "deb http://mirrors.tencentyun.com/ubuntu/ jammy-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.tencentyun.com/ubuntu/ jammy-backports main restricted universe multiverse" >> /etc/apt/sources.list

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 安装依赖
RUN pip install --no-cache-dir flask requests

WORKDIR /app

COPY worker.py .

RUN mkdir -p /tmp/iris_models

EXPOSE 8080

CMD ["python3", "worker.py"]
