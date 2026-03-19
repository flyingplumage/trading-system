#!/bin/bash
# Iris Worker 一键部署 - 简化版
# 只部署 Iris Worker，LLaMA-Factory 可选

set -e

# 请修改为您的服务器 IP
SERVER_IP="${SERVER_IP:-YOUR_SERVER_IP}"
WORK_DIR="${WORK_DIR:-/tmp/iris-worker}"
WORKER_PORT="${WORKER_PORT:-8080}"

echo "============================================================"
echo "🚀 Iris Worker 一键部署 (简化版)"
echo "============================================================"
echo ""
echo "服务器：$SERVER_IP"
echo "工作目录：$WORK_DIR"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi
echo "✅ Docker 已安装：$(docker --version)"
echo ""

# 创建工作目录
echo "📁 创建工作目录..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 下载 Worker 代码
echo "📥 下载 Worker 代码..."
curl -sSL "http://$SERVER_IP:8888/worker.py" -o worker.py
if [ ! -f worker.py ]; then
    echo "❌ 下载失败"
    exit 1
fi
echo "✅ Worker 代码已下载"
echo ""

# 创建 Dockerfile
echo "📝 创建 Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.10-slim
WORKDIR /app
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir flask requests
RUN curl -sSL http://${SERVER_IP}:8888/worker.py -o worker.py
EXPOSE 8080
CMD ["python3", "worker.py"]
EOF
echo "✅ Dockerfile 已创建"
echo ""

# 创建 docker-compose.yml
echo "📝 创建 docker-compose.yml..."
cat > docker-compose.yml << EOF
version: '3.8'
services:
  iris-worker:
    build: .
    container_name: iris-worker
    ports:
      - "$WORKER_PORT:8080"
    environment:
      - SERVER_IP=$SERVER_IP
      - WORKER_PORT=$WORKER_PORT
    volumes:
      - ./output:/tmp/iris_models
    restart: unless-stopped
volumes:
  output:
    driver: local
EOF
echo "✅ docker-compose.yml 已创建"
echo ""

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p output
echo "✅ 数据目录已创建"
echo ""

# 构建并启动
echo "🐳 构建 Docker 镜像（首次约 3-5 分钟）..."
docker-compose up -d --build

echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 检查状态
echo ""
echo "📊 检查服务状态..."
if docker ps | grep -q iris-worker; then
    echo "✅ Iris Worker 已启动"
else
    echo "❌ Iris Worker 启动失败"
    docker logs iris-worker 2>&1 | tail -20
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 访问地址："
echo ""
echo "  Iris Worker 监控面板（任务队列、进度查看）"
echo "  http://localhost:$WORKER_PORT/"
echo ""
echo "📋 常用命令："
echo ""
echo "  查看日志：docker logs -f iris-worker"
echo "  重启服务：docker-compose restart"
echo "  停止服务：docker-compose down"
echo ""
echo "============================================================"
