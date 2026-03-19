#!/bin/bash
# Iris Worker Mac 真正一键部署
# 不需要任何手动操作！

set -e

SERVER_IP="162.14.115.79"
WORK_DIR=~/iris-worker-docker

echo "🚀 Iris Worker 一键部署..."
echo ""

# 配置 Docker 镜像加速
mkdir -p ~/.docker
cat > ~/.docker/daemon.json << 'MIRROR'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev",
    "https://dockerhub.icu",
    "https://registry.docker-cn.com"
  ]
}
MIRROR

# 创建工作目录
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 下载文件
echo "📥 下载部署文件..."
curl -sSL "http://$SERVER_IP:8888/Dockerfile" -o Dockerfile
curl -sSL "http://$SERVER_IP:8888/worker.py" -o worker.py

# 构建镜像（自动重试）
echo "🔨 构建镜像..."
for i in 1 2 3; do
    if docker build -t iris-worker:latest . 2>&1 | tee /tmp/docker_build.log | grep -q "Successfully built"; then
        echo "✅ 镜像构建成功"
        break
    fi
    if [ $i -eq 3 ]; then
        echo "❌ 构建失败，请检查网络"
        exit 1
    fi
    echo "⚠️  第 $i 次尝试失败，重试..."
    sleep 5
done

# 清理旧容器
docker rm -f iris-worker 2>/dev/null || true

# 启动容器
echo "🚀 启动容器..."
docker run -d \
  --name iris-worker \
  -p 8080:8080 \
  -e SERVER_IP="$SERVER_IP" \
  -e WS_PORT="5000" \
  --restart unless-stopped \
  iris-worker:latest

# 等待启动
sleep 8

# 验证
echo ""
echo "📊 验证服务..."
if curl -s "http://localhost:8080/health" | grep -q "healthy"; then
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
echo "📡 WebSocket: ws://$SERVER_IP:5000/ws"
echo ""

# 自动打开监控面板
if command -v open &> /dev/null; then
    open "http://localhost:8080/"
fi
