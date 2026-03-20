#!/bin/bash
# Iris Worker v55 一键部署脚本 - 使用已有镜像

set -e

SERVER_IP="${SERVER_IP:-162.14.115.79}"
WS_PORT="${WS_PORT:-5000}"
WORK_DIR=~/iris-worker-data

echo "============================================================"
echo "🚀 Iris Worker v55 一键部署"
echo "============================================================"
echo ""

# 1. 停止旧容器
echo "[1/5] 停止旧容器..."
docker stop iris-worker 2>/dev/null || true
docker rm iris-worker 2>/dev/null || true
echo "✅ 旧容器已清理"

# 2. 创建数据目录
echo ""
echo "[2/5] 创建数据目录..."
mkdir -p "$WORK_DIR"

# 3. 下载 Worker 代码
echo ""
echo "[3/5] 下载 Worker 代码..."
curl -sSL "http://$SERVER_IP:$WS_PORT/files/worker.py" -o "$WORK_DIR/worker.py"
VERSION=$(grep "Iris Worker v" "$WORK_DIR/worker.py" | head -1 | grep -o "v[0-9]*" || echo "unknown")
echo "✅ Worker 代码已下载 ($VERSION)"

# 4. 构建镜像（使用已有 python 镜像）
echo ""
echo "[4/5] 构建 Docker 镜像..."

# 检查是否有 python 镜像
if docker images | grep -q python; then
    PYTHON_IMAGE=$(docker images | grep python | head -1 | awk '{print $1":"$2}')
    echo "✅ 使用已有镜像：$PYTHON_IMAGE"
else
    # 尝试拉取
    echo "⚠️ 尝试拉取 python 镜像..."
    docker pull python:3.12-slim || {
        echo "❌ 无法拉取镜像，请手动执行：docker pull python:3.12-slim"
        exit 1
    }
    PYTHON_IMAGE="python:3.12-slim"
fi

cat > "$WORK_DIR/Dockerfile" << DOCKERFILE
FROM $PYTHON_IMAGE
WORKDIR /app
RUN pip install --no-cache-dir flask psutil websockets requests
EXPOSE 8080
CMD ["python", "/data/worker.py"]
DOCKERFILE

cd "$WORK_DIR"
docker build -t iris-worker:v55 . 2>&1 | tail -5
echo "✅ 镜像构建完成"

# 5. 启动容器
echo ""
echo "[5/5] 启动容器..."
docker run -d \
  --name iris-worker \
  -p 8080:8080 \
  -v "$WORK_DIR:/data:rw" \
  -e SERVER_IP="$SERVER_IP" \
  -e WS_PORT="$WS_PORT" \
  -e WORKER_PORT="8080" \
  --restart unless-stopped \
  iris-worker:v55

sleep 5

# 验证
echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo "📁 数据目录：$WORK_DIR"
echo "🐳 容器：iris-worker"
echo ""
docker logs iris-worker --tail 5
