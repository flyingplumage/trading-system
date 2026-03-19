# Iris Worker Docker 镜像
# Worker 代码直接打包进镜像，不需要 HTTP 服务

FROM python:3.10-slim

# 设置国内 pip 源
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV DEBIAN_FRONTEND=noninteractive

# 安装依赖
RUN pip install --no-cache-dir \
    flask \
    requests \
    websockets \
    psutil

# 创建工作目录
WORKDIR /app

# 复制 Worker 代码（启动时会被覆盖）
COPY worker.py .

# 创建模型目录
RUN mkdir -p /app/models

# 环境变量
ENV SERVER_IP=162.14.115.79
ENV WS_PORT=5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# 启动命令
CMD ["python3", "worker.py"]
