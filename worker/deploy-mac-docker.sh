#!/bin/bash
# Mac Worker Docker 一键部署
# 只部署 Worker，后端在服务器

set -e

# 请修改为您的后端服务器地址
BACKEND_URL="${BACKEND_URL:-http://localhost:5000}"
WORK_DIR=~/trading-worker-docker

echo "🐳 Mac Worker Docker 一键部署"
echo "后端：$BACKEND_URL"
echo ""

# 1. 创建工作目录
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 2. 自动获取 API Key
echo "[1/4] 自动获取 API Key..."
REGISTER_RESP=$(curl -s -X POST "$BACKEND_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"worker_$(date +%s)\",\"password\":\"worker123\",\"role\":\"bot\"}")

LOGIN_RESP=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"worker_$(date +%s)\",\"password\":\"worker123\"}")

if ! echo "$LOGIN_RESP" | grep -q "access_token"; then
    LOGIN_RESP=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"username":"admin","password":"admin123"}')
fi

TOKEN=$(echo "$LOGIN_RESP" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    API_KEY_RESP=$(curl -s -X POST "$BACKEND_URL/api/auth/api-key/create" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"name":"docker-worker","role":"bot"}')
    API_KEY=$(echo "$API_KEY_RESP" | grep -o '"api_key":"[^"]*"' | cut -d'"' -f4)
    [ -z "$API_KEY" ] && API_KEY=$(echo "$API_KEY_RESP" | grep -o '"key":"[^"]*"' | cut -d'"' -f4)
    [ -z "$API_KEY" ] && API_KEY="demo_key"
    echo "✅ API Key: ${API_KEY:0:20}..."
else
    echo "⚠️  使用演示 Key"
    API_KEY="demo_key"
fi

# 3. 创建 Worker 程序
echo "[2/4] 创建 Worker 程序..."
cat > worker.py << 'PYEOF'
#!/usr/bin/env python3
import asyncio, json, os, socket, sys, time
from datetime import datetime
from pathlib import Path

try:
    import torch
    MPS = torch.backends.mps.is_available()
    print(f"✅ PyTorch | MPS: {MPS}")
except ImportError as e:
    print(f"❌ 依赖缺失：{e}")
    sys.exit(1)

import aiohttp

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
API_KEY = os.getenv("API_KEY", "")

def get_hardware_info():
    return {"hostname": socket.gethostname(), "platform": "Docker/macOS", "gpu": {"available": MPS, "type": "Apple Silicon GPU" if MPS else "CPU"}, "worker_id": f"docker_{socket.gethostname()}_{int(time.time())}"}

async def heartbeat_loop():
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    worker_info = get_hardware_info()
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"worker_id": worker_info["worker_id"], "status": "idle", "hardware": worker_info["hardware"]}
                async with session.post(f"{BACKEND_URL}/api/worker/heartbeat", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        print(f"❤️  [{datetime.now().strftime('%H:%M:%S')}] 心跳成功")
        except Exception as e:
            print(f"❌ 心跳失败：{e}")
        await asyncio.sleep(30)

async def main():
    print("=" * 50)
    print("  Worker 启动")
    print("=" * 50)
    print(f"后端：{BACKEND_URL}")
    print(f"API Key: {API_KEY[:20] if API_KEY else 'None'}...")
    print(f"硬件：{get_hardware_info()['gpu']['type']}")
    print("=" * 50)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                print(f"✅ 后端连接：{data.get('status', 'ok')}")
    except Exception as e:
        print(f"❌ 无法连接后端：{e}")
        sys.exit(1)
    print("\n🚀 启动心跳 (等待训练任务)...\n")
    try:
        await heartbeat_loop()
    except KeyboardInterrupt:
        print("\n👋 Worker 已停止")

if __name__ == "__main__":
    asyncio.run(main())
PYEOF

# 4. 创建 Docker Compose
echo "[3/4] 创建 Docker Compose..."
cat > docker-compose.yml << EOF
version: '3.8'
services:
  worker:
    image: python:3.12-slim
    container_name: trading-worker
    restart: unless-stopped
    environment:
      - BACKEND_URL=$BACKEND_URL
      - API_KEY=$API_KEY
      - PYTORCH_ENABLE_MPS_FALLBACK=1
    volumes:
      - worker_data:/root/trading-worker/data
    working_dir: /root/trading-worker
    command: >
      sh -c "
      pip install torch torchvision torchaudio stable-baselines3 gymnasium pandas numpy requests aiohttp -q &&
      python worker.py
      "

volumes:
  worker_data:
EOF

# 5. 启动
echo "[4/4] 启动 Docker Worker..."
docker compose up -d

sleep 5

echo ""
echo "=========================================="
echo "  ✅ Worker 已启动！"
echo "=========================================="
echo ""
echo "📍 工作目录：$WORK_DIR"
echo "🔗 后端：$BACKEND_URL"
echo ""
echo "📊 查看状态:"
echo "   docker compose ps"
echo ""
echo "📋 查看日志:"
echo "   docker compose logs -f"
echo ""
echo "🛑 停止:"
echo "   docker compose down"
echo ""
echo "=========================================="

# 显示日志
echo ""
echo "📋 实时日志:"
docker compose logs -f
