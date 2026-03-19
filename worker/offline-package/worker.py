#!/usr/bin/env python3
"""
Iris Worker - 支持 HTTP 轮询远程指令
通过 8888 端口获取指令（无需额外开放端口）
"""

import os
import json
import time
import hashlib
import threading
import subprocess
import socket
import requests
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify

# ==================== 配置 ====================

SERVER_IP = os.getenv("SERVER_IP", "162.14.115.79")
INSTRUCTION_PORT = int(os.getenv("INSTRUCTION_PORT", "8888"))
WORKER_PORT = int(os.getenv("WORKER_PORT", "8080"))
INSTRUCTION_URL = f"http://{SERVER_IP}:{INSTRUCTION_PORT}/instructions.json"

WORK_DIR = Path("/tmp/iris-worker")
MODELS_DIR = Path("/tmp/iris_models")

for d in [WORK_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ==================== Worker 状态 ====================

worker_state = {
    "status": "idle",
    "current_task": None,
    "installed_packages": [],
    "hardware": {},
    "last_instruction_check": None
}

# ==================== 硬件检测 ====================

def detect_hardware():
    hardware = {
        "hostname": socket.gethostname(),
        "platform": "docker",
        "cpu_count": os.cpu_count() or 4,
        "gpu": {"available": False, "type": None}
    }
    try:
        import torch
        if torch.cuda.is_available():
            hardware["gpu"] = {"available": True, "type": "NVIDIA CUDA"}
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            hardware["gpu"] = {"available": True, "type": "Apple Silicon MPS"}
    except:
        pass
    return hardware

# ==================== 指令轮询 ====================

def instruction_polling_loop():
    """定期从服务器获取指令"""
    worker_id = socket.gethostname()
    last_processed_id = None
    
    print(f"🔄 开始轮询指令：{INSTRUCTION_URL}")
    
    while True:
        try:
            # 获取指令文件
            resp = requests.get(INSTRUCTION_URL, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                instructions = data.get("instructions", [])
                
                for instr in instructions:
                    instr_id = instr.get("id")
                    if instr_id != last_processed_id:
                        print(f"\n📨 收到新指令：{instr_id}")
                        process_instruction(instr)
                        last_processed_id = instr_id
            
            worker_state["last_instruction_check"] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"⚠️  轮询失败：{e}")
        
        time.sleep(5)  # 每 5 秒检查一次

def process_instruction(instr):
    """处理指令"""
    cmd_type = instr.get("type", "")
    
    if cmd_type == "install_packages":
        packages = instr.get("packages", [])
        install_packages_local(packages)
    
    elif cmd_type == "assign_task":
        task = instr.get("task", {})
        execute_task(task)
    
    elif cmd_type == "get_status":
        # 状态会通过轮询自动上报
        pass

def install_packages_local(packages):
    """安装依赖包"""
    if not packages:
        return
    
    worker_state["status"] = "installing"
    print(f"📦 安装包：{packages}")
    
    try:
        cmd = ["pip", "install"] + packages
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            worker_state["installed_packages"].extend(packages)
            print(f"✅ 安装成功")
        else:
            print(f"❌ 安装失败：{result.stderr}")
    except Exception as e:
        print(f"❌ 异常：{e}")
    
    finally:
        worker_state["status"] = "idle"

def execute_task(task):
    """执行训练任务"""
    task_id = task.get("id", "unknown")
    task_type = task.get("type", "unknown")
    
    print(f"🚀 执行任务：{task_id}")
    worker_state["status"] = "busy"
    worker_state["current_task"] = task
    
    try:
        # 模拟训练
        time.sleep(5)
        print(f"✅ 任务完成：{task_id}")
    except Exception as e:
        print(f"❌ 任务失败：{e}")
    
    finally:
        worker_state["status"] = "idle"
        worker_state["current_task"] = None

# ==================== HTTP API ====================

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "worker_id": socket.gethostname(),
        "websocket": False,  # 使用 HTTP 轮询
        "http_polling": True,
        "last_check": worker_state["last_instruction_check"],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "worker_id": socket.gethostname(),
        "status": worker_state["status"],
        "current_task": worker_state["current_task"],
        "hardware": detect_hardware(),
        "installed_packages": worker_state["installed_packages"],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/packages/install', methods=['POST'])
def api_install_packages():
    data = request.json
    packages = data.get('packages', [])
    install_packages_local(packages)
    return jsonify({"success": True})

@app.route('/', methods=['GET'])
def index():
    ws_status = "🔄 HTTP 轮询中"
    ws_class = "connected"
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Iris Worker - {socket.gethostname()}</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .status {{ font-size: 24px; font-weight: bold; }}
        .idle {{ color: #4caf50; }}
        .busy {{ color: #ff9800; }}
        .connected {{ color: #4caf50; }}
    </style>
</head>
<body>
    <h1>🚀 Iris Worker</h1>
    
    <div class="card">
        <h2>连接状态</h2>
        <div class="status {ws_class}">{ws_status}</div>
        <p>Worker ID: {socket.gethostname()}</p>
        <p>状态：{worker_state['status'].upper()}</p>
        <p>指令服务器：{INSTRUCTION_URL}</p>
    </div>
    
    <div class="card">
        <h2>API 端点</h2>
        <ul>
            <li><a href="/health">/health</a> - 健康检查</li>
            <li><a href="/status">/status</a> - 详细状态</li>
        </ul>
    </div>
</body>
</html>"""
    return html

# ==================== 主函数 ====================

if __name__ == "__main__":
    # 启动轮询线程
    polling_thread = threading.Thread(target=instruction_polling_loop, daemon=True)
    polling_thread.start()
    
    hardware = detect_hardware()
    print("=" * 50)
    print("  Iris Worker 启动")
    print("=" * 50)
    print(f"主机名：{hardware['hostname']}")
    print(f"指令服务器：{INSTRUCTION_URL}")
    print(f"HTTP 端口：{WORKER_PORT}")
    print("=" * 50)
    print(f"监控面板：http://localhost:{WORKER_PORT}/")
    print("=" * 50)
    
    app.run(host="0.0.0.0", port=WORKER_PORT, debug=False)
