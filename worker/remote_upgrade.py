#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""远程升级脚本 - 服务端推送升级指令到 Worker"""

import requests
import json
import sys

SERVER_IP = "162.14.115.79"
WS_PORT = 5000

def upgrade_worker(version="v19", restart=True):
    """发送远程升级指令"""
    
    script_url = f"http://{SERVER_IP}:8888/worker_{version}.py"
    
    payload = {
        "type": "upgrade",
        "data": {
            "version": version,
            "script_url": script_url,
            "restart": restart
        }
    }
    
    print(f"📤 发送 {version} 升级指令...")
    print(f"   目标：ws://{SERVER_IP}:{WS_PORT}/ws/worker")
    print(f"   脚本：{script_url}")
    
    try:
        resp = requests.post(
            f"http://{SERVER_IP}:{WS_PORT}/ws/worker/command",
            json=payload,
            timeout=10
        )
        
        result = resp.json()
        print(f"\n✅ 升级指令已发送！")
        print(f"   结果：{result}")
        
        return True
    except Exception as e:
        print(f"\n❌ 发送失败：{e}")
        return False

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "v19"
    success = upgrade_worker(version)
    sys.exit(0 if success else 1)
