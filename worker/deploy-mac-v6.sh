#!/bin/bash
# Iris Worker v6 Mac 一键部署脚本（强制刷新版）

set -e

SERVER_IP="162.14.115.79"

echo "============================================================"
echo "🚀 Iris Worker v6 一键部署（强制刷新）"
echo "============================================================"
echo ""

# 配置镜像加速
mkdir -p ~/.docker
cat > ~/.docker/daemon.json << 'MIRROR'
{"registry-mirrors":["https://docker.m.daocloud.io","https://docker.1panel.live","https://hub.rat.dev"]}
MIRROR

# 强制清理
echo "🧹 清理旧容器和缓存..."
docker rm -f iris-worker 2>/dev/null || true
docker rmi docker.m.daocloud.io/library/python:3.10-slim 2>/dev/null || true

# 拉取镜像
echo "📥 拉取镜像..."
docker pull docker.m.daocloud.io/library/python:3.10-slim

# 下载代码（带时间戳强制刷新）
WORK_DIR=~/iris-worker-v6
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"
curl -sSL "http://$SERVER_IP:8888/worker_v6_final.py?t=$(date +%s)" -o worker.py

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
HEALTH=$(curl -s "http://localhost:8080/health" 2>/dev/null)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Worker 已启动"
    echo ""
    echo "健康状态：$HEALTH"
else
    echo "⚠️  服务启动中，查看日志..."
    docker logs iris-worker --tail 20
fi

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/?t=$(date +%s)"
echo "📡 WebSocket: ws://$SERVER_IP:5000/ws/worker"
echo ""
echo "🎯 v6 新功能:"
echo "   📦 智能依赖安装（4 个源自动切换）"
echo "   📊 依赖进度（包名/进度/当前源）"
echo "   🧠 训练 Epoch 显示"
echo "   📝 500 条日志缓存（显示 30 条）"
echo ""
echo "💡 如果页面没变化，请："
echo "   1. 强制刷新浏览器：Cmd+Shift+R"
echo "   2. 或使用无痕模式打开"
echo "   3. 或访问：http://localhost:8080/?t=$(date +%s)"
echo ""

# 自动打开（带时间戳）
open "http://localhost:8080/?t=$(date +%s)" 2>/dev/null || true
