#!/bin/bash
# 后端守护脚本 - 确保服务稳定运行

LOG_FILE="/tmp/backend.log"
PID_FILE="/tmp/backend.pid"

start_backend() {
    echo "🚀 启动后端服务..."
    cd /root/.openclaw/workspace/projects/trading-system-release/backend
    source venv/bin/activate
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 > $LOG_FILE 2>&1 &
    echo $! > $PID_FILE
    sleep 5
    
    if ps -p $(cat $PID_FILE) > /dev/null 2>&1; then
        echo "✅ 后端服务已启动 (PID: $(cat $PID_FILE))"
        return 0
    else
        echo "❌ 后端服务启动失败"
        return 1
    fi
}

check_backend() {
    if [ -f $PID_FILE ] && ps -p $(cat $PID_FILE) > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 主循环
echo "📊 后端守护进程已启动"
echo "   日志：$LOG_FILE"
echo "   PID: $PID_FILE"
echo ""

while true; do
    if ! check_backend; then
        echo "⚠️  后端服务已停止，正在重启..."
        start_backend
    fi
    sleep 10
done
