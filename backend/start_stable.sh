#!/bin/bash
# 后端稳定启动脚本
cd /root/.openclaw/workspace/projects/trading-system-release/backend
source venv/bin/activate

# 检查是否已运行
if curl -s http://localhost:5000/health | grep -q "healthy"; then
    echo "✅ 后端已在运行"
    exit 0
fi

# 启动
echo "🚀 启动后端..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 > /tmp/backend.log 2>&1 &
sleep 8

# 验证
if curl -s http://localhost:5000/health | grep -q "healthy"; then
    echo "✅ 后端启动成功"
else
    echo "❌ 后端启动失败"
    cat /tmp/backend.log
fi
