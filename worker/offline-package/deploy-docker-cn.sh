#!/bin/bash
# Iris Worker Docker 部署 - Mac 本地构建（使用国内镜像源）

set -e

SERVER_IP="162.14.115.79"
INSTRUCTION_PORT="8888"
WORK_DIR=~/iris-worker-docker
WORKER_PORT="8080"
IMAGE_NAME="iris-worker:latest"

echo "============================================================"
echo "🚀 Iris Worker Docker 部署 (国内镜像源)"
echo "============================================================"
echo ""

# 1. 配置 Docker 镜像加速
echo "[1/5] 配置 Docker 镜像加速..."
cat > ~/.docker/daemon.json << EOF
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev",
    "https://dhub.kubesre.xyz"
  ]
}
EOF
echo "✅ Docker 镜像加速已配置"

# 重启 Docker（Mac 上需要手动重启 Docker Desktop）
echo "⚠️  请重启 Docker Desktop 使配置生效"
echo "   重启后重新运行此脚本"
echo ""

# 2. 清理旧容器
echo "[2/5] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true
echo "✅ 清理完成"
echo ""

# 3. 创建工作目录并下载文件
echo "[3/5] 下载部署文件..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

curl -sSL "http://$SERVER_IP:$INSTRUCTION_PORT/Dockerfile" -o Dockerfile
curl -sSL "http://$SERVER_IP:$INSTRUCTION_PORT/worker.py" -o worker.py

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
    -v iris_models:/tmp/iris_models \
    -e SERVER_IP="$SERVER_IP" \
    -e INSTRUCTION_PORT="$INSTRUCTION_PORT" \
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

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 访问地址:"
echo "   监控面板：http://localhost:$WORKER_PORT/"
echo "   健康检查：http://localhost:$WORKER_PORT/health"
echo ""
echo "📡 指令获取:"
echo "   指令文件：http://$SERVER_IP:$INSTRUCTION_PORT/instructions.json"
echo "   方式：每 5 秒自动轮询"
echo ""
echo "📋 常用命令:"
echo "   查看日志：docker logs -f iris-worker"
echo "   查看状态：curl http://localhost:$WORKER_PORT/status"
echo "   停止服务：docker stop iris-worker"
echo ""
echo "============================================================"
