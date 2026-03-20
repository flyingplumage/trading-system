#!/bin/bash
# Iris Worker v49 一键部署脚本 - 支持持久化
# Docker Desktop 版本

set -e

SERVER_IP="${SERVER_IP:-162.14.115.79}"
WS_PORT="${WS_PORT:-5000}"
WORK_DIR=~/iris-worker-data

echo "============================================================"
echo "🚀 Iris Worker v49 一键部署"
echo "============================================================"
echo ""
echo "服务器：$SERVER_IP:$WS_PORT"
echo "数据目录：$WORK_DIR"
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
echo "✅ 数据目录：$WORK_DIR"

# 3. 下载 Worker 代码
echo ""
echo "[3/5] 下载 Worker 代码..."
curl -sSL "http://$SERVER_IP:$WS_PORT/files/worker.py" -o "$WORK_DIR/worker.py"

if [ ! -s "$WORK_DIR/worker.py" ]; then
    echo "❌ 下载失败，请检查服务器 5000 端口是否开放"
    exit 1
fi

# 验证版本
VERSION=$(grep "worker_version.*v" "$WORK_DIR/worker.py" | head -1 | grep -o "v[0-9]*" || echo "unknown")
echo "✅ Worker 代码已下载 ($VERSION)"

# 4. 构建 Docker 镜像
echo ""
echo "[4/5] 构建 Docker 镜像..."
cat > "$WORK_DIR/Dockerfile" << 'DOCKERFILE'
FROM python:3.12-slim

WORKDIR /app

# 安装依赖
RUN pip install --no-cache-dir flask psutil websockets requests

# 复制 worker 代码（从卷挂载）
# CMD 会动态加载

EXPOSE 8080

CMD ["python", "/data/worker.py"]
DOCKERFILE

cd "$WORK_DIR"
docker build -t iris-worker:v49 . 2>&1 | tail -5
echo "✅ 镜像构建完成 (iris-worker:v49)"

# 5. 启动容器（挂载持久化卷）
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
  iris-worker:v49

echo "✅ 容器已启动"

# 6. 验证
echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo "📁 数据目录：$WORK_DIR"
echo "🐳 容器名称：iris-worker"
echo ""
echo "💡 后续升级："
echo "   curl http://localhost:8080/upgrade?v49 | bash"
echo "   或重新运行此脚本"
echo ""

# 显示容器日志
echo "📋 容器日志:"
docker logs iris-worker --tail 10
