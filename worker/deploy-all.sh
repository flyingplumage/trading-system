#!/bin/bash
# Iris Worker v5 一键部署（完整版）
# 包含服务端配置和 Mac 端部署

set -e

MODE=${1:-mac}  # 默认部署 Mac 端
SERVER_IP="162.14.115.79"

echo "============================================================"
echo "🚀 Iris Worker v5 一键部署"
echo "============================================================"
echo ""
echo "版本：v5（支持断点续传）"
echo "特性："
echo "  ✅ 实时任务追踪"
echo "  ✅ 断线自动重连"
echo "  ✅ 任务断点续传"
echo "  ✅ 实时进度监控"
echo "  ✅ 增强日志系统"
echo ""

if [ "$MODE" = "server" ]; then
    echo "📋 部署服务端..."
    echo ""
    
    # 1. 安装任务管理器
    echo "[1/4] 安装任务管理器..."
    mkdir -p /root/.openclaw/workspace/projects/trading-system-release/backend/app/services
    curl -sSL "http://$SERVER_IP:8888/task_manager.py" -o /root/.openclaw/workspace/projects/trading-system-release/backend/app/services/task_manager.py 2>/dev/null || \
    cp /root/.openclaw/workspace/projects/trading-system-release/worker/task_manager.py /root/.openclaw/workspace/projects/trading-system-release/backend/app/services/
    echo "✅ 任务管理器已安装"
    
    # 2. 更新 WebSocket API
    echo ""
    echo "[2/4] 更新 WebSocket API..."
    curl -sSL "http://$SERVER_IP:8888/websocket_v2.py" -o /root/.openclaw/workspace/projects/trading-system-release/backend/app/api/websocket_v2.py 2>/dev/null || \
    cp /root/.openclaw/workspace/projects/trading-system-release/worker/websocket_v2.py /root/.openclaw/workspace/projects/trading-system-release/backend/app/api/
    echo "✅ WebSocket API 已更新"
    
    # 3. 重启后端
    echo ""
    echo "[3/4] 重启后端服务..."
    pkill -f "uvicorn.*5000" 2>/dev/null || true
    sleep 3
    cd /root/.openclaw/workspace/projects/trading-system-release/backend
    source venv/bin/activate
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 > /tmp/backend_v5.log 2>&1 &
    sleep 8
    echo "✅ 后端服务已重启"
    
    # 4. 验证
    echo ""
    echo "[4/4] 验证服务..."
    if curl -s "http://localhost:5000/health" | grep -q "healthy"; then
        echo "✅ 后端运行正常"
        echo "✅ 服务端部署完成！"
    else
        echo "⚠️  后端启动中，请稍候..."
    fi
    
    echo ""
    echo "============================================================"
    echo "✅ 服务端部署完成！"
    echo "============================================================"
    echo ""
    echo "📊 访问地址:"
    echo "   API 文档：http://$SERVER_IP:5000/docs"
    echo "   Worker 列表：http://$SERVER_IP:5000/ws/workers"
    echo "   任务列表：http://$SERVER_IP:5000/ws/tasks"
    echo "   统计信息：http://$SERVER_IP:5000/ws/stats"
    echo ""

elif [ "$MODE" = "mac" ]; then
    echo "📋 部署 Mac Worker..."
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
    
    # 3. 拉取基础镜像
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
        echo "❌ 无法拉取镜像"
        exit 1
    fi
    
    # 4. 创建工作目录并下载代码
    echo ""
    echo "[4/6] 下载 Worker 代码..."
    WORK_DIR=~/iris-worker-v5
    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"
    
    curl -sSL "http://$SERVER_IP:8888/worker_v5.py" -o worker.py || {
        echo "❌ 下载失败"
        exit 1
    }
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
      "$BASE_IMAGE" \
      sh -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask requests websockets -q && python3 worker.py"
    
    sleep 10
    
    # 6. 验证
    echo ""
    echo "[6/6] 验证服务..."
    for i in {1..10}; do
        if curl -s "http://localhost:8080/health" | grep -q "healthy"; then
            echo "✅ Worker 已启动"
            break
        fi
        sleep 2
    done
    
    HEALTH=$(curl -s "http://localhost:8080/health" 2>/dev/null)
    echo ""
    echo "健康状态：$HEALTH"
    
    echo ""
    echo "============================================================"
    echo "✅ Mac Worker 部署完成！"
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
    echo "   ✅ 断线自动重连"
    echo "   ✅ 任务断点续传"
    echo "   ✅ 实时进度追踪"
    echo ""
    echo "📋 常用命令:"
    echo "   查看日志：docker logs -f iris-worker"
    echo "   查看状态：curl http://localhost:8080/status"
    echo "   重启服务：docker restart iris-worker"
    echo ""
    
    # 自动打开监控面板
    echo "🌐 5 秒后自动打开监控面板..."
    sleep 5
    open "http://localhost:8080/" 2>/dev/null || true
fi

echo "============================================================"
