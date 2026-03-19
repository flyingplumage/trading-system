FROM python:3.12-slim

WORKDIR /root/trading-worker

# 安装依赖
RUN pip install --no-cache-dir \
    torch torchvision torchaudio \
    stable-baselines3 gymnasium pandas numpy requests aiohttp

# 复制 Worker 程序
COPY worker.py .
COPY worker_config.json .

# 启动命令
CMD ["python", "worker.py"]
