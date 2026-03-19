#!/bin/bash
# Iris Worker Mac 超简单部署
# 自动安装依赖

set -e

SERVER_IP="162.14.115.79"

echo "🚀 Iris Worker 超简单部署..."
echo ""

# 配置 Docker 镜像加速
mkdir -p ~/.docker
cat > ~/.docker/daemon.json << 'MIRROR'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ]
}
MIRROR

# 清理旧容器
docker rm -f iris-worker 2>/dev/null || true

# 拉取 Python 镜像
echo "📥 拉取基础镜像..."
docker pull docker.m.daocloud.io/library/python:3.10-slim 2>/dev/null || \
docker pull docker.1panel.live/library/python:3.10-slim 2>/dev/null || \
docker pull hub.rat.dev/library/python:3.10-slim 2>/dev/null || {
    echo "❌ 无法拉取镜像"
    exit 1
}

# 创建工作目录
WORK_DIR=~/iris-worker-docker
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 下载 Worker 代码
echo "📥 下载 Worker 代码..."
curl -sSL "http://$SERVER_IP:8888/worker.py" -o worker.py

# 启动容器（先安装依赖）
echo "🚀 启动容器..."
docker run -d \
  --name iris-worker \
  -p 8080:8080 \
  -v "$WORK_DIR:/app" \
  -w /app \
  -e SERVER_IP="$SERVER_IP" \
  -e WS_PORT="5000" \
  --restart unless-stopped \
  docker.m.daocloud.io/library/python:3.10-slim \
  sh -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask requests websockets && python3 worker.py"

sleep 8

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo "📡 WebSocket: ws://$SERVER_IP:5000/ws"
echo ""

# 自动打开
open "http://localhost:8080/" 2>/dev/null || true
