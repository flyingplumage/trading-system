#!/usr/bin/env python3
"""
Worker 远程升级脚本
通过 WebSocket 接收升级指令
"""

import requests
import subprocess
import sys
import os

def upgrade_worker(script_url):
    """下载并执行新版本的 worker.py"""
    print(f"📥 下载新版本：{script_url}")
    
    try:
        # 下载新版本
        resp = requests.get(script_url, timeout=30)
        if resp.status_code != 200:
            print(f"❌ 下载失败：{resp.status_code}")
            return False
        
        # 保存新版本
        with open('/app/worker_new.py', 'wb') as f:
            f.write(resp.content)
        
        print("✅ 下载成功")
        
        # 备份旧版本
        if os.path.exists('/app/worker.py'):
            os.rename('/app/worker.py', '/app/worker.py.bak')
            print("📦 已备份旧版本")
        
        # 替换为新版本
        os.rename('/app/worker_new.py', '/app/worker.py')
        print("✅ 升级完成")
        
        return True
    
    except Exception as e:
        print(f"❌ 升级失败：{e}")
        return False

def restart_worker():
    """重启 Worker 进程"""
    print("🔄 重启 Worker...")
    
    # 方式 1: Docker 容器内，退出进程让 Docker 重启
    print("👋 退出当前进程，Docker 将自动重启")
    os._exit(0)

if __name__ == "__main__":
    script_url = sys.argv[1] if len(sys.argv) > 1 else "http://162.14.115.79:8888/worker.py"
    restart = sys.argv[2] == "true" if len(sys.argv) > 2 else True
    
    if upgrade_worker(script_url):
        if restart:
            restart_worker()
    else:
        print("❌ 升级失败，继续使用旧版本")
        sys.exit(1)
