#!/bin/bash
# Iris Worker Docker 部署 - 国内镜像源版本

set -e

SERVER_IP="162.14.115.79"
INSTRUCTION_PORT="8888"
WORK_DIR="/tmp/iris-worker"
WORKER_PORT="8080"
IMAGE_NAME="iris-worker:latest"

echo "============================================================"
echo "🚀 Iris Worker Docker 部署 (国内镜像源)"
echo "============================================================"
echo ""
echo "指令服务器：http://$SERVER_IP:$INSTRUCTION_PORT/instructions.json"
echo ""

# 配置 Docker 使用国内镜像加速
echo "[1/6] 配置 Docker 镜像加速..."
cat > /etc/docker/daemon.json << EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.docker-cn.com",
    "https://docker.m.daocloud.io",
    "https://dockerhub.azk8s.cn"
  ]
}
EOF
echo "✅ Docker 镜像加速已配置"

# 重启 Docker
systemctl restart docker 2>/dev/null || sudo systemctl restart docker 2>/dev/null || echo "⚠️  无法重启 Docker，请手动重启"
echo ""

# 2. 清理旧容器
echo "[2/6] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true
echo "✅ 清理完成"
echo ""

# 3. 下载部署文件
echo "[3/6] 下载部署文件..."
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
echo "[4/6] 构建 Docker 镜像 (首次约 3-5 分钟)..."
docker build -t "$IMAGE_NAME" . 2>&1 | tail -20
echo "✅ 镜像构建完成"
echo ""

# 5. 启动容器
echo "[5/6] 启动容器..."
docker run -d \
    --name iris-worker \
    -p "$WORKER_PORT:8080" \
    -v iris_models:/tmp/iris_models \
    -e SERVER_IP="$SERVER_IP" \
    -e INSTRUCTION_PORT="$INSTRUCTION_PORT" \
    -e WORKER_PORT="$WORKER_PORT" \
    --restart unless-stopped \
    "$IMAGE_NAME"

echo ""
echo "⏳ 等待容器启动..."
sleep 8

# 6. 验证
echo "[6/6] 验证服务..."

for i in {1..10}; do
    if curl -s "http://localhost:$WORKER_PORT/health" > /dev/null 2>&1; then
        echo "✅ Worker 已启动"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️  服务启动中..."
    fi
    sleep 2
done

# 显示状态
HEALTH=$(curl -s "http://localhost:$WORKER_PORT/health" 2>/dev/null)
echo ""
echo "健康状态：$HEALTH"

# 检查轮询状态
if echo "$HEALTH" | grep -q "http_polling.*true"; then
    echo "✅ HTTP 轮询：已启用"
    echo "📡 指令检查：每 5 秒自动轮询"
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
echo "📡 指令获取:"
echo "   指令文件：http://$SERVER_IP:$INSTRUCTION_PORT/instructions.json"
echo "   方式：每 5 秒自动轮询"
echo ""
echo "📋 常用命令:"
echo "   查看日志：docker logs -f iris-worker"
echo "   查看状态：curl http://localhost:$WORKER_PORT/status"
echo "   停止服务：docker stop iris-worker"
echo "   重启服务：docker restart iris-worker"
echo ""
echo "============================================================"
