#!/bin/bash
# Iris Worker v11 Mac 一键部署脚本
# 包含：硬件监控 + 100 条日志 + 远程升级功能

set -e

SERVER_IP="162.14.115.79"

echo "============================================================"
echo "🚀 Iris Worker v11 一键部署"
echo "============================================================"
echo ""
echo "🎯 v11 新特性："
echo "  ✅ 硬件资源监控（CPU/内存/磁盘）"
echo "  ✅ 日志显示 100 条（更详细）"
echo "  ✅ 远程升级功能"
echo "  ✅ SSE 实时推送（不刷新页面）"
echo ""

# 1. 配置 Docker 镜像加速
echo "[1/6] 配置 Docker 镜像加速..."
mkdir -p ~/.docker
cat > ~/.docker/daemon.json << 'MIRROR'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ]
}
MIRROR
echo "✅ Docker 镜像加速已配置"

# 2. 清理旧容器
echo ""
echo "[2/6] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true
echo "✅ 清理完成"

# 3. 拉取镜像并安装依赖
echo ""
echo "[3/6] 准备环境..."
WORK_DIR=~/iris-worker-v11
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

echo "📥 拉取基础镜像..."
docker pull docker.m.daocloud.io/library/python:3.10-slim 2>/dev/null || \
docker pull docker.1panel.live/library/python:3.10-slim 2>/dev/null || \
docker pull hub.rat.dev/library/python:3.10-slim 2>/dev/null || {
    echo "❌ 无法拉取镜像"
    exit 1
}
echo "✅ 镜像拉取成功"

# 4. 下载 Worker 代码
echo ""
echo "[4/6] 下载 Worker 代码..."
curl -sSL "http://$SERVER_IP:8888/worker_v11.py" -o worker.py
if [ ! -s worker.py ]; then
    echo "❌ 下载失败"
    exit 1
fi
echo "✅ Worker 代码已下载"

# 5. 启动容器
echo ""
echo "[5/6] 启动容器..."
docker run -d \
  --name iris-worker \
  -p 8080:8080 \
  -v "$WORK_DIR:/app" \
  -w /app \
  -e SERVER_IP="$SERVER_IP" \
  -e WS_PORT="5000" \
  --restart unless-stopped \
  docker.m.daocloud.io/library/python:3.10-slim \
  sh -c "
    echo '📦 安装依赖...' && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask requests websockets psutil -q && \
    echo '✅ 依赖安装完成' && \
    echo '🚀 启动 Worker...' && \
    python3 worker.py
  "

echo "⏳ 等待 20 秒启动..."
sleep 20

# 6. 验证服务
echo ""
echo "[6/6] 验证服务..."
for i in {1..10}; do
    if curl -s "http://localhost:8080/health" 2>/dev/null | grep -q "healthy"; then
        echo "✅ Worker 已启动"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️  服务启动中，请稍候..."
    fi
    sleep 2
done

# 显示状态
HEALTH=$(curl -s "http://localhost:8080/health" 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo ""
    echo "健康状态：$HEALTH"
else
    echo ""
    echo "⚠️  查看日志..."
    docker logs iris-worker --tail 20
fi

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo "📡 WebSocket: ws://$SERVER_IP:5000/ws/worker"
echo ""
echo "🎯 v11 特性:"
echo "   💻 硬件监控（CPU/内存/磁盘）"
echo "   📝 日志 100 条（更详细）"
echo "   🔄 远程升级功能"
echo "   ⚡ SSE 实时推送"
echo ""
echo "📋 常用命令:"
echo "   查看日志：docker logs -f iris-worker"
echo "   查看状态：curl http://localhost:8080/status"
echo "   重启服务：docker restart iris-worker"
echo ""
echo "💡 提示：按 Cmd+Shift+R 强制刷新浏览器"
echo ""

# 自动打开监控面板
echo "🌐 5 秒后自动打开监控面板..."
sleep 5
open "http://localhost:8080/" 2>/dev/null || true
