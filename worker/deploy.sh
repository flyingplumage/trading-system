#!/bin/bash
set -e

echo "🚀 Iris Worker 一键部署"
echo "========================"

# 清理
docker stop iris-worker 2>/dev/null || true
docker rm iris-worker 2>/dev/null || true

# 下载代码
mkdir -p ~/iris-worker-data
curl -sSL http://162.14.115.79:5000/files/worker.py -o ~/iris-worker-data/worker.py

# 构建
cd ~/iris-worker-data
cat > Dockerfile << 'DOCKERFILE'
FROM docker.m.daocloud.io/python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask psutil websockets requests
CMD ["python", "/data/worker.py"]
DOCKERFILE

docker build -t iris-worker . 2>&1 | tail -2

# 启动
docker run -d --name iris-worker -p 8080:8080 -v ~/iris-worker-data:/data:rw --restart unless-stopped iris-worker

sleep 5

echo ""
echo "✅ 部署完成！"
echo "📊 http://localhost:8080/"
echo "💡 请 Cmd+Shift+R 强制刷新浏览器"
echo ""
docker logs iris-worker --tail 3
