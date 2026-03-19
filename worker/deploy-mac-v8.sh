#!/bin/bash
# Iris Worker v8 Lite Mac 一键部署脚本
# SSE 实时推送，不刷新页面，无需额外依赖！

set -e

SERVER_IP="162.14.115.79"

echo "============================================================"
echo "🚀 Iris Worker v8 Lite 一键部署"
echo "============================================================"
echo ""
echo "🎯 核心改进："
echo "  ✅ SSE 实时推送（不刷新页面）"
echo "  ✅ 日志区域可滚动（不会重置位置）"
echo "  ✅ 无需额外依赖（只用 flask）"
echo ""

# 配置镜像加速
mkdir -p ~/.docker
cat > ~/.docker/daemon.json << 'MIRROR'
{"registry-mirrors":["https://docker.m.daocloud.io","https://docker.1panel.live","https://hub.rat.dev"]}
MIRROR

# 清理
docker rm -f iris-worker 2>/dev/null || true

# 拉取镜像
echo "📥 拉取镜像..."
docker pull docker.m.daocloud.io/library/python:3.10-slim 2>/dev/null || \
docker pull docker.1panel.live/library/python:3.10-slim 2>/dev/null || \
docker pull hub.rat.dev/library/python:3.10-slim 2>/dev/null

# 下载代码
WORK_DIR=~/iris-worker-v8
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"
curl -sSL "http://$SERVER_IP:8888/worker_v8.py" -o worker.py

# 启动
echo "🚀 启动容器..."
docker run -d \
  --name iris-worker \
  -p 8080:8080 \
  -v "$WORK_DIR:/app" \
  -w /app \
  -e SERVER_IP="$SERVER_IP" \
  -e WS_PORT="5000" \
  --restart unless-stopped \
  docker.m.daocloud.io/library/python:3.10-slim \
  sh -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask requests websockets -q && python3 worker.py"

sleep 15

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
echo "📡 WebSocket: ws://$SERVER_IP:5000/ws/worker"
echo ""
echo "🎯 v8 Lite 核心改进:"
echo "   ✅ SSE 实时推送（不刷新页面）"
echo "   ✅ 日志区域可滚动（不会重置位置）"
echo "   ✅ 无需额外依赖（只用 flask）"
echo ""

# 自动打开
open "http://localhost:8080/" 2>/dev/null || true
