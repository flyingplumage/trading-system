#!/bin/bash
# 一键升级到 v25

echo "🔄 开始升级到 v25..."

# 停止旧容器
docker rm -f iris-worker 2>/dev/null || true

# 下载 v25 代码
cd ~/iris-worker
echo "📥 下载 v25 代码..."
curl -sSL http://162.14.115.79:8888/worker.py -o worker.py

# 验证下载
if [ ! -s worker.py ]; then
    echo "❌ 下载失败"
    exit 1
fi

# 检查版本
VERSION=$(grep -i "worker_version.*v25" worker.py && echo "v25" || echo "unknown")
if [ "$VERSION" != "v25" ]; then
    echo "⚠️  下载的版本不是 v25: $VERSION"
fi

# 重新构建镜像
echo "📦 重新构建镜像..."
docker build -t iris-worker:latest . 2>&1 | tail -5

# 启动容器
echo "🚀 启动容器..."
docker run -d \
  --name iris-worker \
  -e SERVER_IP=162.14.115.79 \
  -e WS_PORT=5000 \
  -p 8080:8080 \
  --restart unless-stopped \
  iris-worker:latest

sleep 10

# 验证
echo ""
echo "📊 验证..."
docker ps | grep iris-worker && echo "✅ 容器运行中" || echo "❌ 容器未运行"
docker logs iris-worker --tail 10 | grep -i "v25\|started"

echo ""
echo "✅ 升级完成！"
echo "📊 访问：http://localhost:8080/"
echo "📋 查看日志：docker logs -f iris-worker"
