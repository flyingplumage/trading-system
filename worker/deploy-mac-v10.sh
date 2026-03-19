#!/bin/bash
# Iris Worker v10 Mac 一键部署脚本
# 紧凑一屏布局，无需滚动

set -e

SERVER_IP="162.14.115.79"

echo "============================================================"
echo "🚀 Iris Worker v10 一键部署"
echo "============================================================"
echo ""
echo "🎯 紧凑布局："
echo "  ✅ 4 个状态卡片（顶部）"
echo "  ✅ 依赖明细 + 日志（底部）"
echo "  ✅ 一屏显示所有信息"
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
docker pull docker.m.daocloud.io/library/python:3.10-slim 2>/dev/null || true

# 下载代码
WORK_DIR=~/iris-worker-v10
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"
curl -sSL "http://$SERVER_IP:8888/worker_v10.py" -o worker.py

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

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo ""
echo "🎯 v10 改进:"
echo "   ✅ 紧凑一屏布局（无需滚动）"
echo "   ✅ 4 个状态卡片（顶部）"
echo "   ✅ 依赖明细 + 日志（底部）"
echo ""

open "http://localhost:8080/" 2>/dev/null || true
