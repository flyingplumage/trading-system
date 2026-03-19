#!/bin/bash
# Mac 端连接测试脚本

SERVER_IP="162.14.115.79"

echo "============================================================"
echo "🔍 Mac 端连接测试"
echo "============================================================"
echo ""

echo "1. 测试 HTTP 连接..."
curl -s --connect-timeout 5 http://$SERVER_IP:5000/health && echo "✅ HTTP 连接成功" || echo "❌ HTTP 连接失败"

echo ""
echo "2. 测试 WebSocket 连接..."
python3 << 'PYEOF'
import asyncio
import websockets

async def test():
    try:
        async with websockets.connect("ws://162.14.115.79:5000/ws/worker", additional_headers={"Worker-ID": "test", "Worker-Port": "8080"}, open_timeout=5) as ws:
            print("✅ WebSocket 连接成功")
            await ws.send(json.dumps({"type": "handshake", "worker_id": "test"}))
            resp = await ws.recv()
            print(f"📨 响应：{resp}")
    except Exception as e:
        print(f"❌ WebSocket 连接失败：{e}")

asyncio.run(test())
PYEOF

echo ""
echo "3. 检查 Worker 容器..."
docker ps | grep iris-worker && echo "✅ Worker 容器运行中" || echo "❌ Worker 容器未运行"

echo ""
echo "4. 查看 Worker 日志..."
docker logs iris-worker --tail 20 2>&1 | tail -10

echo ""
echo "============================================================"
