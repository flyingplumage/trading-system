#!/bin/bash
# Iris Worker v29 一键部署脚本

set -e

SERVER_IP="${SERVER_IP:-162.14.115.79}"
WS_PORT="${WS_PORT:-5000}"
WORK_DIR=~/iris-worker-v29

echo "============================================================"
echo "🚀 Iris Worker v29 一键部署"
echo "============================================================"
echo ""
echo "架构：WebSocket 信令 + HTTP 文件传输"
echo "服务器：$SERVER_IP:$WS_PORT"
echo ""

# 1. 清理旧容器
echo "[1/5] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true

# 2. 创建工作目录
echo ""
echo "[2/5] 创建工作目录..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 3. 创建 Dockerfile
echo ""
echo "[3/5] 创建 Dockerfile..."
cat > Dockerfile << 'DOCKERFILE'
FROM python:3.10-slim
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir flask requests websockets psutil
WORKDIR /app
COPY worker.py .
RUN mkdir -p /app/models
ENV SERVER_IP=162.14.115.79
ENV WS_PORT=5000
ENV WORKER_PORT=8080
CMD ["python3", "worker.py"]
DOCKERFILE

# 4. 下载 Worker 代码
echo ""
echo "[4/5] 下载 Worker v29 代码..."
curl -sSL "http://$SERVER_IP:$WS_PORT/files/worker.py" -o worker.py

if [ ! -s worker.py ]; then
    echo "❌ 下载失败"
    exit 1
fi
echo "✅ Worker 代码已下载"

# 5. 构建并启动
echo ""
echo "[5/5] 构建并启动..."
docker build -t iris-worker:v29 . 2>&1 | tail -5

docker run -d \
  --name iris-worker \
  -e SERVER_IP="$SERVER_IP" \
  -e WS_PORT="$WS_PORT" \
  -p 8080:8080 \
  --restart unless-stopped \
  iris-worker:v29

sleep 15

# 验证
echo ""
echo "📊 验证..."
if curl -s "http://localhost:8080/health" 2>/dev/null | grep -q "healthy"; then
    echo "✅ Worker 已启动"
else
    echo "⚠️  服务启动中..."
fi

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo ""
echo "📋 常用命令:"
echo "   查看日志：docker logs -f iris-worker"
echo "   查看状态：curl http://localhost:8080/health"
echo ""

# 自动打开
sleep 3
open "http://localhost:8080/" 2>/dev/null || true
