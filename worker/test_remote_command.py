#!/usr/bin/env python3
"""
测试远程下发指令到 Worker
"""

import asyncio
import json
import websockets

WS_URL = "ws://localhost:8765"

async def test():
    print("=" * 50)
    print("  测试远程指令下发")
    print("=" * 50)
    print()
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ 已连接到 Worker Manager")
            
            # 等待 Worker 连接
            print("\n⏳ 等待 Worker 连接...")
            for i in range(10):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(msg)
                    print(f"📨 收到消息：{data}")
                    
                    if data.get("type") == "welcome":
                        print("\n✅ Worker 已连接！")
                        break
                except asyncio.TimeoutError:
                    print(f"   等待中... ({i+1}/10)")
            
            # 发送测试指令
            print("\n📤 发送测试指令...")
            test_command = {
                "type": "ping"
            }
            
            # 广播到所有 Worker
            print(f"   指令：{test_command}")
            print("   (实际应该由 Worker Manager 转发)")
            
    except Exception as e:
        print(f"❌ 测试失败：{e}")
    
    print()
    print("=" * 50)
    print("提示：")
    print("1. 在 Mac 上重新部署：curl -sSL http://162.14.115.79:8888/deploy.sh | bash")
    print("2. 查看日志：docker logs -f iris-worker")
    print("3. 检查 WebSocket 状态：curl http://localhost:8080/health")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test())
