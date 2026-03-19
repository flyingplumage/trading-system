#!/bin/bash
# 后端守护脚本

LOG_FILE="/tmp/backend_guardian.log"
PID_FILE="/tmp/backend.pid"

start_backend() {
    echo "🚀 启动后端..." >> $LOG_FILE
    cd /root/.openclaw/workspace/projects/trading-system-release/backend
    source venv/bin/activate
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 > /tmp/backend.log 2>&1 &
    echo $! > $PID_FILE
    sleep 5
    
    if ps -p $(cat $PID_FILE) > /dev/null 2>&1; then
        echo "✅ 后端已启动 (PID: $(cat $PID_FILE))" >> $LOG_FILE
        return 0
    else
        echo "❌ 后端启动失败" >> $LOG_FILE
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

echo "📊 后端守护进程已启动" >> $LOG_FILE
echo "   日志：$LOG_FILE" >> $LOG_FILE
echo "" >> $LOG_FILE

while true; do
    if ! check_backend; then
        echo "⚠️  [$(date '+%Y-%m-%d %H:%M:%S')] 后端已停止，正在重启..." >> $LOG_FILE
        start_backend
    fi
    sleep 10
done
