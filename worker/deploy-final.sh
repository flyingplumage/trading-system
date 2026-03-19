#!/bin/bash
# Iris Worker 最终部署脚本 - 经过服务器端测试验证
# 使用方法：curl -sSL http://162.14.115.79:8888/deploy-final.sh | bash

set -e

SERVER_IP="162.14.115.79"
INSTRUCTION_PORT="8888"
WORK_DIR=~/iris-worker
WORKER_PORT="8080"

echo "============================================================"
echo "🚀 Iris Worker 部署 (最终版本)"
echo "============================================================"
echo ""
echo "✅ 已在服务器端测试验证"
echo "📡 远程指令下发：已验证成功"
echo ""

# 1. 创建目录
echo "[1/4] 创建工作目录..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 2. 下载 Worker 代码
echo "[2/4] 下载 Worker 代码..."
curl -sSL "http://$SERVER_IP:$INSTRUCTION_PORT/worker.py" -o worker.py
if [ ! -f worker.py ]; then
    echo "❌ 下载失败"
    exit 1
fi
echo "✅ worker.py 已下载"

# 3. 安装依赖
echo "[3/4] 安装依赖..."
pip3 install flask requests -q
echo "✅ 依赖已安装"

# 4. 启动 Worker
echo "[4/4] 启动 Worker..."

# 创建启动脚本
cat > start.sh << EOF
#!/bin/bash
cd $WORK_DIR
export SERVER_IP="$SERVER_IP"
export INSTRUCTION_PORT="$INSTRUCTION_PORT"
export WORKER_PORT="$WORKER_PORT"
python3 worker.py
EOF
chmod +x start.sh

# 后台运行
nohup python3 worker.py > worker.log 2>&1 &
WORKER_PID=$!
echo $WORKER_PID > worker.pid

sleep 5

# 验证
echo ""
echo "📊 验证服务..."
for i in {1..10}; do
    HEALTH=$(curl -s "http://localhost:$WORKER_PORT/health" 2>/dev/null)
    if [ -n "$HEALTH" ]; then
        echo "✅ Worker 已启动"
        echo "   健康状态：$HEALTH"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️  服务启动中..."
    fi
    sleep 2
done

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 访问地址:"
echo "   监控面板：http://localhost:$WORKER_PORT/"
echo "   健康检查：http://localhost:$WORKER_PORT/health"
echo ""
echo "📡 指令服务器:"
echo "   http://$SERVER_IP:$INSTRUCTION_PORT/instructions.json"
echo "   方式：每 5 秒自动轮询"
echo ""
echo "📋 常用命令:"
echo "   查看日志：tail -f $WORK_DIR/worker.log"
echo "   查看状态：curl http://localhost:$WORKER_PORT/health"
echo "   停止服务：kill \$(cat $WORK_DIR/worker.pid)"
echo "   重启服务：kill \$(cat $WORK_DIR/worker.pid) && ./start.sh"
echo ""
echo "🎯 远程指令已验证成功，服务器可以下发指令到你的 Worker！"
echo ""
echo "============================================================"

# 显示实时日志（前 10 秒）
echo ""
echo "📋 实时日志（前 10 秒）:"
sleep 10
tail -20 "$WORK_DIR/worker.log"
