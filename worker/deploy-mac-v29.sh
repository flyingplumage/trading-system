#!/bin/bash
# Iris Worker v29 一键部署脚本
# WebSocket 信令 + HTTP 文件传输

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
echo "工作目录：$WORK_DIR"
echo ""

# 1. 清理旧容器
echo "[1/6] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true
echo "✅ 清理完成"

# 2. 创建工作目录
echo ""
echo "[2/6] 创建工作目录..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"
echo "✅ 工作目录已创建"

# 3. 创建 Dockerfile
echo ""
echo "[3/6] 创建 Dockerfile..."
cat > Dockerfile << 'DOCKERFILE'
FROM python:3.10-slim

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV DEBIAN_FRONTEND=noninteractive

RUN pip install --no-cache-dir \
    flask \
    requests \
    websockets \
    psutil

WORKDIR /app
COPY worker.py .

RUN mkdir -p /app/models

ENV SERVER_IP=162.14.115.79
ENV WS_PORT=5000
ENV WORKER_PORT=8080

CMD ["python3", "worker.py"]
DOCKERFILE
echo "✅ Dockerfile 已创建"

# 4. 下载 Worker 代码
echo ""
echo "[4/6] 下载 Worker v29 代码..."
curl -sSL "http://$SERVER_IP:$WS_PORT/files/worker.py" -o worker.py

if [ ! -s worker.py ]; then
    echo "❌ 下载失败，请检查服务器 5000 端口是否开放"
    echo ""
    echo "💡 解决方案："
    echo "   1. 腾讯云开放 5000 端口"
    echo "   2. 或使用 SSH 隧道：ssh -L $WS_PORT:localhost:$WS_PORT root@$SERVER_IP -N"
    exit 1
fi

# 验证版本
VERSION=$(grep "worker_version.*v29" worker.py && echo "v29" || echo "unknown")
if [ "$VERSION" != "v29" ]; then
    echo "⚠️  警告：下载的版本可能不是 v29"
fi

echo "✅ Worker 代码已下载 ($VERSION)"

# 5. 构建镜像
echo ""
echo "[5/6] 构建 Docker 镜像..."
docker build -t iris-worker:v29 . 2>&1 | tail -10
echo "✅ 镜像构建完成"

# 6. 启动容器
echo ""
echo "[6/6] 启动容器..."
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
echo "📊 验证服务..."
for i in {1..10}; do
    if curl -s "http://localhost:8080/health" 2>/dev/null | grep -q "healthy"; then
        echo "✅ Worker 已启动"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️  服务启动中，请稍候..."
    fi
    sleep 2
done

HEALTH=$(curl -s "http://localhost:8080/health" 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo ""
    echo "健康状态：$HEALTH"
else
    echo ""
    echo "⚠️  查看日志..."
    docker logs iris-worker --tail 20
fi

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo "🔌 WebSocket: ws://$SERVER_IP:$WS_PORT/ws/worker"
echo "📁 HTTP 文件：http://$SERVER_IP:$WS_PORT/files/worker.py"
echo ""
echo "🎯 v29 架构:"
echo "   ✅ WebSocket 信令（指令/进度）"
echo "   ✅ HTTP 文件传输（代码下载）"
echo "   ✅ 单端口（5000）"
echo ""
echo "📋 常用命令:"
echo "   查看日志：docker logs -f iris-worker"
echo "   查看状态：curl http://localhost:8080/health"
echo "   重启服务：docker restart iris-worker"
echo ""
echo "💡 如果连接失败:"
echo "   1. 检查腾讯云 5000 端口是否开放"
echo "   2. 或使用 SSH 隧道：ssh -L $WS_PORT:localhost:$WS_PORT root@$SERVER_IP -N"
echo ""

# 自动打开监控面板
echo "🌐 5 秒后自动打开监控面板..."
sleep 5
open "http://localhost:8080/" 2>/dev/null || true
