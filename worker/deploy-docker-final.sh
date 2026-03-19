#!/bin/bash
# Iris Worker Docker 最终部署脚本 - 纯 WebSocket 版本
# 使用国内镜像源

set -e

SERVER_IP="162.14.115.79"
WS_PORT="5000"
WORK_DIR=~/iris-worker-docker
WORKER_PORT="8080"
IMAGE_NAME="iris-worker:latest"

echo "============================================================"
echo "🚀 Iris Worker Docker 部署 (纯 WebSocket 版本)"
echo "============================================================"
echo ""
echo "WebSocket 服务器：ws://$SERVER_IP:$WS_PORT/ws"
echo ""

# 1. 配置 Docker 镜像加速
echo "[1/5] 配置 Docker 镜像加速..."
mkdir -p ~/.docker
cat > ~/.docker/daemon.json << 'MIRROR'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev",
    "https://dockerhub.icu"
  ]
}
MIRROR
echo "✅ Docker 镜像加速已配置"
echo ""
echo "⚠️  请重启 Docker Desktop 使配置生效"
echo "   重启后重新运行此脚本"
echo ""
read -p "   完成后按回车继续..."

# 2. 清理旧容器
echo "[2/5] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true
echo "✅ 清理完成"
echo ""

# 3. 下载部署文件
echo "[3/5] 下载部署文件..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

curl -sSL "http://$SERVER_IP:8888/Dockerfile" -o Dockerfile
curl -sSL "http://$SERVER_IP:8888/worker.py" -o worker.py

if [ ! -f Dockerfile ] || [ ! -f worker.py ]; then
    echo "❌ 下载失败"
    exit 1
fi
echo "✅ 文件已下载"
echo ""

# 4. 构建镜像
echo "[4/5] 构建 Docker 镜像 (首次约 3-5 分钟)..."
docker build -t "$IMAGE_NAME" . 2>&1 | tail -20
echo "✅ 镜像构建完成"
echo ""

# 5. 启动容器
echo "[5/5] 启动容器..."
docker run -d \
    --name iris-worker \
    -p "$WORKER_PORT:8080" \
    -e SERVER_IP="$SERVER_IP" \
    -e WS_PORT="$WS_PORT" \
    -e WORKER_PORT="$WORKER_PORT" \
    --restart unless-stopped \
    "$IMAGE_NAME"

sleep 8

# 验证
echo ""
echo "📊 验证服务..."
for i in {1..10}; do
    if curl -s "http://localhost:$WORKER_PORT/health" > /dev/null 2>&1; then
        echo "✅ Worker 已启动"
        break
    fi
    sleep 2
done

HEALTH=$(curl -s "http://localhost:$WORKER_PORT/health" 2>/dev/null)
echo ""
echo "健康状态：$HEALTH"

if echo "$HEALTH" | grep -q '"websocket":true'; then
    echo "✅ WebSocket: 已连接"
else
    echo "⏳ WebSocket: 连接中..."
fi

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 访问地址:"
echo "   监控面板：http://localhost:$WORKER_PORT/"
echo "   健康检查：http://localhost:$WORKER_PORT/health"
echo ""
echo "📡 WebSocket 连接:"
echo "   服务器：ws://$SERVER_IP:$WS_PORT/ws"
echo "   状态：自动连接，断开自动重连"
echo ""
echo "📋 常用命令:"
echo "   查看日志：docker logs -f iris-worker"
echo "   查看状态：curl http://localhost:$WORKER_PORT/status"
echo "   停止服务：docker stop iris-worker"
echo ""
echo "============================================================"

# 显示日志
echo ""
echo "📋 实时日志（前 15 秒）:"
sleep 15
docker logs iris-worker --tail 30
