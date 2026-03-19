#!/bin/bash
# Iris Worker v18 Mac 一键部署脚本
# 完整重新部署，确保所有文件都是最新的

set -e

SERVER_IP="162.14.115.79"

echo "============================================================"
echo "🚀 Iris Worker v18 一键部署"
echo "============================================================"
echo ""
echo "🎯 v18 优化："
echo "  ✅ 亮色趋势线（蓝/紫/粉）"
echo "  ✅ 发光效果（更明显）"
echo "  ✅ 日志中文正常"
echo "  ✅ 图表背景浅色"
echo ""

# 1. 清理旧容器
echo "[1/6] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true
echo "✅ 清理完成"

# 2. 创建工作目录
echo ""
echo "[2/6] 准备工作目录..."
WORK_DIR=~/iris-worker-v18
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 3. 下载 Worker 代码
echo ""
echo "[3/6] 下载 Worker 代码..."
curl -sSL "http://$SERVER_IP:8888/worker_v18.py" -o worker.py
if [ ! -s worker.py ]; then
    echo "❌ 下载失败"
    exit 1
fi
echo "✅ Worker 代码已下载"

# 4. 启动容器
echo ""
echo "[4/6] 启动容器..."
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

# 5. 验证服务
echo ""
echo "[5/6] 验证服务..."
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

HEALTH=$(curl -s "http://localhost:8080/health" 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo ""
    echo "健康状态：$HEALTH"
else
    echo ""
    echo "⚠️  查看日志..."
    docker logs iris-worker --tail 30
fi

# 6. 检查 HTML 文件
echo ""
echo "[6/6] 检查 HTML 模板..."
docker exec iris-worker ls -la /app/index.html 2>&1 && echo "✅ HTML 模板已创建" || echo "⚠️  HTML 模板未创建"

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo ""
echo "🎯 v18 特性:"
echo "   ✅ 亮色趋势线（蓝/紫/粉）"
echo "   ✅ 发光效果（更明显）"
echo "   ✅ 日志中文正常"
echo "   ✅ 图表背景浅色"
echo ""
echo "💡 提示："
echo "   1. 如果看到 HTML 源码，请强制刷新：Cmd+Shift+R"
echo "   2. 查看日志：docker logs -f iris-worker"
echo "   3. 等待 30 秒让趋势图显示"
echo ""

# 自动打开监控面板
echo "🌐 5 秒后自动打开监控面板..."
sleep 5
open "http://localhost:8080/" 2>/dev/null || true
