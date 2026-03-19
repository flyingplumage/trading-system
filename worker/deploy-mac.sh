#!/bin/bash
# Iris Worker v5 Mac 一键部署脚本
# 特性：断线续传、实时监控、自动重连

set -e

SERVER_IP="162.14.115.79"

echo "============================================================"
echo "🚀 Iris Worker v5 Mac 一键部署"
echo "============================================================"
echo ""
echo "特性："
echo "  ✅ 断线自动重连"
echo "  ✅ 任务断点续传"
echo "  ✅ 实时进度监控"
echo "  ✅ 增强日志系统"
echo ""

# 1. 配置 Docker 镜像加速
echo "[1/6] 配置 Docker 镜像加速..."
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
echo "✅ Docker 镜像加速已配置"

# 2. 清理旧容器
echo ""
echo "[2/6] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true
echo "✅ 清理完成"

# 3. 拉取基础镜像（多源备用）
echo ""
echo "[3/6] 拉取基础镜像..."
for mirror in "docker.m.daocloud.io/library/python:3.10-slim" \
              "docker.1panel.live/library/python:3.10-slim" \
              "hub.rat.dev/library/python:3.10-slim"; do
    echo "  尝试：$mirror"
    if docker pull "$mirror" 2>/dev/null; then
        echo "  ✅ 镜像拉取成功"
        BASE_IMAGE="$mirror"
        break
    fi
done

if [ -z "$BASE_IMAGE" ]; then
    echo "❌ 无法拉取镜像，请检查网络"
    exit 1
fi

# 4. 创建工作目录并下载代码
echo ""
echo "[4/6] 下载 Worker 代码..."
WORK_DIR=~/iris-worker-v5
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

if curl -sSL "http://$SERVER_IP:8888/worker_v5.py" -o worker.py && [ -s worker.py ]; then
    echo "✅ Worker 代码已下载"
else
    echo "❌ 下载失败"
    exit 1
fi

# 5. 启动容器（自动安装依赖）
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
  "$BASE_IMAGE" \
  sh -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask requests websockets -q && python3 worker.py"

echo "⏳ 等待容器启动..."
sleep 10

# 6. 验证服务
echo ""
echo "[6/6] 验证服务..."
for i in {1..10}; do
    if curl -s "http://localhost:8080/health" | grep -q "healthy"; then
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
echo ""
echo "健康状态：$HEALTH"

# 显示 WebSocket 状态
if echo "$HEALTH" | grep -q '"websocket":true'; then
    echo "✅ WebSocket: 已连接"
else
    echo "⏳ WebSocket: 连接中..."
fi

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 访问地址:"
echo "   监控面板：http://localhost:8080/"
echo "   健康检查：http://localhost:8080/health"
echo "   状态 API: http://localhost:8080/status"
echo "   日志 API: http://localhost:8080/logs"
echo ""
echo "📡 WebSocket: ws://$SERVER_IP:5000/ws/worker"
echo ""
echo "🎯 v5 新特性:"
echo "   ✅ 断线自动重连（自动恢复连接）"
echo "   ✅ 任务断点续传（从中断处继续）"
echo "   ✅ 实时进度追踪（秒级更新）"
echo "   ✅ 增强日志系统（200 条历史）"
echo ""
echo "📋 常用命令:"
echo "   查看日志：docker logs -f iris-worker"
echo "   查看状态：curl http://localhost:8080/status"
echo "   重启服务：docker restart iris-worker"
echo "   停止服务：docker stop iris-worker"
echo "   删除容器：docker rm -f iris-worker"
echo ""
echo "🔧 测试断线续传:"
echo "   1. 发送训练任务"
echo "   2. docker stop iris-worker"
echo "   3. docker start iris-worker"
echo "   4. 查看日志：docker logs iris-worker | grep 续传"
echo ""
echo "============================================================"

# 自动打开监控面板
echo ""
echo "🌐 5 秒后自动打开监控面板..."
sleep 5
if command -v open &> /dev/null; then
    open "http://localhost:8080/"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8080/"
fi
