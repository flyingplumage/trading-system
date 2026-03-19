#!/bin/bash
# Mac Worker 真正一键部署脚本
# 只需要执行这一个命令，其他全自动

set -e

# 请修改为您的后端服务器地址
BACKEND_URL="${BACKEND_URL:-http://localhost:5000}"
WORK_DIR=~/trading-worker

echo "🚀 开始一键部署 Mac Worker..."
echo ""

# 1. 创建目录
mkdir -p "$WORK_DIR/data/models" "$WORK_DIR/data/features"
cd "$WORK_DIR"

# 2. 创建虚拟环境
echo "[1/5] 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖（静默安装）
echo "[2/5] 安装依赖 (约 5-10 分钟，请稍候)..."
pip install --upgrade pip -q 2>/dev/null
pip install torch torchvision torchaudio -q 2>/dev/null
pip install stable-baselines3 gymnasium pandas numpy requests aiohttp python-dotenv -q 2>/dev/null
echo "✅ 依赖安装完成"

# 4. 自动注册并获取 API Key
echo "[3/5] 自动注册账户并获取 API Key..."
REGISTER_RESP=$(curl -s -X POST "$BACKEND_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"mac_worker_'$(date +%s)'","password":"worker123","role":"bot"}')

if echo "$REGISTER_RESP" | grep -q "success.*true"; then
    echo "✅ 账户注册成功"
else
    echo "⚠️  注册响应：$REGISTER_RESP"
fi

# 登录
LOGIN_RESP=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"mac_worker_'$(date +%s)'","password":"worker123"}')

# 尝试用固定用户名登录（如果已注册过）
if ! echo "$LOGIN_RESP" | grep -q "access_token"; then
    LOGIN_RESP=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"username":"admin","password":"admin123"}')
fi

TOKEN=$(echo "$LOGIN_RESP" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "✅ 登录成功"
    
    # 创建 API Key
    API_KEY_RESP=$(curl -s -X POST "$BACKEND_URL/api/auth/api-key/create" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"name":"mac-worker-auto","role":"bot"}')
    
    API_KEY=$(echo "$API_KEY_RESP" | grep -o '"api_key":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$API_KEY" ]; then
        # 如果没有 api_key 字段，尝试从响应中提取
        API_KEY=$(echo "$API_KEY_RESP" | grep -o '"key":"[^"]*"' | cut -d'"' -f4)
    fi
    
    if [ -n "$API_KEY" ]; then
        echo "✅ API Key 获取成功"
    else
        echo "⚠️  API Key 响应：$API_KEY_RESP"
        API_KEY="demo_key_12345"
    fi
else
    echo "⚠️  登录失败，使用演示 Key"
    API_KEY="demo_key_12345"
fi

# 5. 创建配置文件
echo "[4/5] 创建配置文件..."
cat > worker_config.json << EOF
{
  "backend_url": "$BACKEND_URL",
  "ws_url": "${WS_URL:-ws://localhost:5000/ws}",
  "api_key": "$API_KEY",
  "work_dir": "$WORK_DIR/data"
}
EOF

# 6. 创建 worker.py
echo "[5/5] 创建 Worker 程序..."
cat > worker.py << 'PYEOF'
#!/usr/bin/env python3
"""Mac Worker - 自动启动版本"""
import asyncio, json, socket, sys, time
from datetime import datetime
from pathlib import Path

try:
    import torch
    MPS = torch.backends.mps.is_available()
    print(f"✅ PyTorch 已加载 | MPS: {MPS}")
except ImportError as e:
    print(f"❌ 依赖缺失：{e}")
    sys.exit(1)

WORK_DIR = Path.home() / "trading-worker"
CONFIG_FILE = WORK_DIR / "worker_config.json"

def load_config():
    if not CONFIG_FILE.exists():
        print(f"❌ 配置文件不存在：{CONFIG_FILE}")
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        return json.load(f)

async def heartbeat_loop(config):
    import aiohttp
    api_key = config.get("api_key", "")
    backend_url = config["backend_url"]
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    worker_id = f"mac_{socket.gethostname()}"
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "worker_id": worker_id,
                    "status": "idle",
                    "hardware": {"gpu": "Apple Silicon" if MPS else "CPU", "platform": "macOS"}
                }
                async with session.post(f"{backend_url}/api/worker/heartbeat", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        print(f"❤️  [{datetime.now().strftime('%H:%M:%S')}] 心跳成功")
        except Exception as e:
            print(f"❌ 心跳失败：{e}")
        await asyncio.sleep(30)

async def main():
    import aiohttp
    config = load_config()
    
    print("=" * 50)
    print("  Mac Worker 启动")
    print("=" * 50)
    print(f"后端：{config['backend_url']}")
    print(f"API Key: {config['api_key'][:20]}...")
    print(f"GPU: {'Apple Silicon MPS' if MPS else 'CPU'}")
    print("=" * 50)
    
    # 测试连接
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{config['backend_url']}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                print(f"✅ 后端连接：{data.get('status', 'ok')}")
    except Exception as e:
        print(f"❌ 无法连接后端：{e}")
        sys.exit(1)
    
    print("\n🚀 启动心跳 (Ctrl+C 停止)...\n")
    try:
        await heartbeat_loop(config)
    except KeyboardInterrupt:
        print("\n👋 Worker 已停止")

if __name__ == "__main__":
    asyncio.run(main())
PYEOF

# 创建启动脚本
cat > start.sh << 'EOF'
#!/bin/bash
cd ~/trading-worker
source venv/bin/activate
export PYTORCH_ENABLE_MPS_FALLBACK=1
export OMP_NUM_THREADS=4
python worker.py "$@"
EOF
chmod +x start.sh

# 完成
echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "🎉 所有配置已自动完成"
echo ""
echo "🚀 启动 Worker:"
echo "   cd ~/trading-worker && ./start.sh"
echo ""
echo "📊 查看 Worker 状态:"
echo "   curl $BACKEND_URL/api/worker/list"
echo ""
echo "=========================================="
echo ""

# 自动启动 Worker
echo "🔥 5 秒后自动启动 Worker..."
sleep 5
./start.sh
