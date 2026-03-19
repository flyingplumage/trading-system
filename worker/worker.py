#!/usr/bin/env python3
"""
分布式训练 Worker - Docker 版本
只负责执行训练任务，上报结果
"""
import asyncio, json, os, socket, sys, time
from datetime import datetime
from pathlib import Path

try:
    import torch
    MPS = torch.backends.mps.is_available()
    print(f"✅ PyTorch 已加载 | MPS: {MPS}")
except ImportError as e:
    print(f"❌ 依赖缺失：{e}")
    sys.exit(1)

import aiohttp

# 配置（从环境变量读取）
# 默认值仅用于本地开发，生产环境请设置 BACKEND_URL 和 WS_URL 环境变量
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
WS_URL = os.getenv("WS_URL", "ws://localhost:5000/ws")
API_KEY = os.getenv("API_KEY", "")
WORK_DIR = Path(os.getenv("WORK_DIR", "./data"))

def get_hardware_info():
    """获取硬件信息"""
    return {
        "hostname": socket.gethostname(),
        "platform": "Docker/macOS",
        "gpu": {"available": MPS, "type": "Apple Silicon GPU" if MPS else "CPU"},
        "worker_id": f"docker_{socket.gethostname()}_{int(time.time())}"
    }

async def heartbeat_loop():
    """心跳循环 - 定期上报状态"""
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    worker_info = get_hardware_info()
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "worker_id": worker_info["worker_id"],
                    "status": "idle",
                    "hardware": worker_info["hardware"]
                }
                async with session.post(
                    f"{BACKEND_URL}/api/worker/heartbeat",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        print(f"❤️  [{datetime.now().strftime('%H:%M:%S')}] 心跳成功")
                    else:
                        print(f"⚠️  心跳响应：{resp.status}")
        except Exception as e:
            print(f"❌ 心跳失败：{e}")
        await asyncio.sleep(30)

async def main():
    print("=" * 50)
    print("  Worker 启动")
    print("=" * 50)
    print(f"后端地址：{BACKEND_URL}")
    print(f"WebSocket: {WS_URL}")
    print(f"API Key: {API_KEY[:20] if API_KEY else 'None'}...")
    print(f"硬件：{get_hardware_info()['gpu']['type']}")
    print("=" * 50)
    
    # 测试连接后端
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
