#!/bin/bash
# Iris Worker v15 Mac 一键部署脚本
# 完整重新部署，确保所有文件都是最新的

set -e

SERVER_IP="162.14.115.79"

echo "============================================================"
echo "🚀 Iris Worker v15 一键部署"
echo "============================================================"
echo ""
echo "🎯 v15 修复："
echo "  ✅ HTML 模板分离（解决渲染问题）"
echo "  ✅ UTF-8 编码（解决乱码问题）"
echo "  ✅ 趋势线图（硬件监控）"
echo "  ✅ 日志 150 条（更高卡片）"
echo ""

# 1. 清理旧容器
echo "[1/5] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true
echo "✅ 清理完成"

# 2. 创建工作目录
echo ""
echo "[2/5] 准备工作目录..."
WORK_DIR=~/iris-worker-v15
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 3. 下载 Worker 代码
echo ""
echo "[3/5] 下载 Worker 代码..."
curl -sSL "http://$SERVER_IP:8888/worker_v15.py" -o worker.py
if [ ! -s worker.py ]; then
    echo "❌ 下载失败"
    exit 1
fi
echo "✅ Worker 代码已下载"

# 4. 启动容器（会自动创建 HTML 模板）
echo ""
echo "[4/5] 启动容器..."
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
echo "[5/5] 验证服务..."
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

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo ""
echo "🎯 v15 特性:"
echo "   ✅ HTML 模板分离（解决渲染问题）"
echo "   ✅ UTF-8 编码（解决乱码问题）"
echo "   ✅ 趋势线图（硬件监控）"
echo "   ✅ 日志 150 条（更高卡片）"
echo ""
echo "💡 提示："
echo "   1. 如果看到 HTML 源码，请强制刷新：Cmd+Shift+R"
echo "   2. 如果看到乱码，请清除浏览器缓存"
echo "   3. 查看日志：docker logs -f iris-worker"
echo ""

# 自动打开监控面板
echo "🌐 5 秒后自动打开监控面板..."
sleep 5
open "http://localhost:8080/" 2>/dev/null || true
