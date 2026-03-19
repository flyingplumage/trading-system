#!/usr/bin/env python3
"""
Worker Manager - WebSocket 服务端
可以主动下发指令到 Worker
"""

import asyncio
import json
from datetime import datetime

try:
    import websockets
except ImportError:
    print("❌ 需要安装 websockets: pip install websockets")
    import sys
    sys.exit(1)

# 已连接的 Worker
connected_workers = {}

async def handler(websocket):
    """处理 Worker 连接"""
    # 获取 Worker 信息
    headers = websocket.request_headers if hasattr(websocket, 'request_headers') else {}
    worker_id = headers.get("Worker-ID", "unknown")
    worker_port = headers.get("Worker-Port", "8080")
    
    # 注册 Worker
    worker_info = {
        "id": worker_id,
        "port": worker_port,
        "connected_at": datetime.now().isoformat(),
        "websocket": websocket
    }
    connected_workers[worker_id] = worker_info
    
    print(f"✅ Worker 已连接：{worker_id} (端口：{worker_port})")
    print(f"   当前在线 Worker: {list(connected_workers.keys())}")
    
    try:
        # 发送欢迎消息
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "连接成功，等待指令"
        }))
        
        # 接收并处理消息
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "")
                
                if msg_type == "handshake":
                    print(f"🤝 {worker_id} 握手成功")
                    worker_info["hardware"] = data.get("hardware", {})
                    await websocket.send(json.dumps({
                        "type": "ack",
                        "message": "握手成功"
                    }))
                
                elif msg_type == "heartbeat":
                    worker_info["last_heartbeat"] = datetime.now().isoformat()
                
                else:
                    print(f"📨 收到 {worker_id} 消息：{msg_type}")
            
            except json.JSONDecodeError:
                print(f"⚠️  无效消息：{message}")
    
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Worker 断开连接：{worker_id} (code={e.code})")
    
    finally:
        # 移除断开的 Worker
        if worker_id in connected_workers:
            del connected_workers[worker_id]
        print(f"📋 当前在线 Worker: {list(connected_workers.keys())}")

async def send_command(worker_id, command):
    """向指定 Worker 发送指令"""
    if worker_id not in connected_workers:
        print(f"❌ Worker 不在线：{worker_id}")
        return False
    
    try:
        websocket = connected_workers[worker_id]["websocket"]
        await websocket.send(json.dumps(command))
        print(f"📤 已发送指令到 {worker_id}: {command.get('type')}")
        return True
    except Exception as e:
        print(f"❌ 发送失败：{e}")
        return False

async def broadcast_command(command):
    """向所有 Worker 广播指令"""
    for worker_id in list(connected_workers.keys()):
        await send_command(worker_id, command)

async def main():
    """启动 WebSocket 服务器"""
    print("=" * 50)
    print("  Worker Manager 启动")
    print("=" * 50)
    print("监听端口：8765")
    print("等待 Worker 连接...")
    print("=" * 50)
    
    # 启动 WebSocket 服务器
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # 永久运行

if __name__ == "__main__":
    asyncio.run(main())
