#!/usr/bin/env python3
"""Iris Worker v3 - 支持远程依赖安装"""

import os, json, time, threading, subprocess, socket, asyncio, websockets, requests
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, render_template_string

SERVER_IP = os.getenv("SERVER_IP", "162.14.115.79")
WS_PORT = int(os.getenv("WS_PORT", "5000"))
WORKER_PORT = int(os.getenv("WORKER_PORT", "8080"))
WS_URL = f"ws://{SERVER_IP}:{WS_PORT}/ws"

WORK_DIR = Path("/tmp/iris-worker")
MODELS_DIR = Path("/tmp/iris_models")
for d in [WORK_DIR, MODELS_DIR]: d.mkdir(parents=True, exist_ok=True)

worker_state = {
    "status": "initializing",
    "current_task": None,
    "websocket_connected": False,
    "dependencies_installed": False,
    "dependency_progress": 0,
    "training_progress": 0,
    "training_loss": 0,
    "messages_received": 0,
    "messages_sent": 0,
    "uptime_seconds": 0,
    "start_time": datetime.now().isoformat()
}

ws_connection = None
message_log = []

def add_log(level, message):
    message_log.append({"timestamp": datetime.now().isoformat(), "level": level, "message": message})
    if len(message_log) > 100: message_log.pop(0)

async def websocket_client():
    global ws_connection, worker_state
    worker_id = socket.gethostname()
    
    while True:
        try:
            print(f"🔌 尝试连接：{WS_URL}")
            async with websockets.connect(WS_URL, additional_headers={"Worker-ID": worker_id, "Worker-Port": str(WORKER_PORT)}) as ws:
                ws_connection = ws
                worker_state["websocket_connected"] = True
                worker_state["status"] = "connected"
                add_log("info", f"✅ WebSocket 已连接：{WS_URL}")
                
                await ws.send(json.dumps({"type": "handshake", "worker_id": worker_id}))
                print(f"✅ 握手已发送")
                
                async for message in ws:
                    worker_state["messages_received"] += 1
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "")
                        add_log("recv", f"收到：{msg_type}")
                        print(f"📨 收到：{msg_type}")
                        
                        if msg_type == "install_dependencies":
                            packages = data.get("packages", ["flask", "requests", "websockets"])
                            asyncio.create_task(install_dependencies(packages))
                        elif msg_type == "train":
                            asyncio.create_task(execute_training(data))
                    except Exception as e:
                        add_log("error", f"处理失败：{e}")
        except Exception as e:
            worker_state["websocket_connected"] = False
            ws_connection = None
            add_log("error", f"连接断开：{e}")
            print(f"❌ 连接失败：{e}")
            await asyncio.sleep(5)

async def install_dependencies(packages):
    worker_state["status"] = "installing"
    try:
        cmd = ["pip", "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"] + packages
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            worker_state["dependencies_installed"] = True
            worker_state["status"] = "idle"
            add_log("success", f"✅ 依赖安装成功")
            print("✅ 依赖安装成功")
        else:
            add_log("error", f"安装失败：{result.stderr[:200]}")
    except Exception as e:
        add_log("error", f"异常：{e}")

async def execute_training(task):
    task_id = task.get("task_id")
    worker_state["status"] = "training"
    for p in range(0, 101, 5):
        await asyncio.sleep(0.5)
        if ws_connection:
            await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "progress": p}))
            add_log("progress", f"📊 {p}%")
    worker_state["status"] = "idle"
    add_log("success", f"✅ 完成：{task_id}")

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": worker_state["status"], "worker_id": socket.gethostname(), "websocket": worker_state["websocket_connected"], "dependencies_installed": worker_state["dependencies_installed"]})

@app.route('/status')
def status():
    return jsonify({"status": worker_state["status"], "current_task": worker_state["current_task"], "websocket_connected": worker_state["websocket_connected"], "messages_received": worker_state["messages_received"]})

@app.route('/logs')
def logs():
    return jsonify({"logs": message_log[-50:]})

@app.route('/')
def index():
    return render_template_string('''<!DOCTYPE html><html><head><title>Iris Worker v3</title><meta http-equiv="refresh" content="2"><style>body{font-family:Arial;margin:20px;background:linear-gradient(135deg,#667eea,#764ba2);color:white}h1{text-align:center}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}.card{background:white;color:#333;padding:20px;border-radius:12px}.stat{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #eee}.log-box{background:#1e1e1e;padding:15px;border-radius:8px;max-height:400px;overflow-y:auto}.log-entry{font-family:Consolas;font-size:13px;padding:3px 0;border-bottom:1px solid #333}.log-info{color:#4fc3f7}.log-success{color:#81c784}.log-error{color:#e57373}</style></head><body><h1>🚀 Iris Worker v3</h1><div class="grid"><div class="card"><h2>📊 状态</h2><div class="stat"><span>Worker</span><span>{{ worker_id }}</span></div><div class="stat"><span>WebSocket</span><span id="ws">...</span></div><div class="stat"><span>依赖</span><span id="deps">...</span></div><div class="stat"><span>状态</span><span id="stat">...</span></div></div><div class="card"><h2>📝 日志</h2><div class="log-box" id="logs">...</div></div></div><script>async function u(){const s=await fetch('/status').then(r=>r.json());const h=await fetch('/health').then(r=>r.json());document.getElementById('ws').innerHTML=h.websocket?'✅':'❌';document.getElementById('deps').innerHTML=h.dependencies_installed?'✅':'⏳';document.getElementById('stat').innerText=s.status;const l=await fetch('/logs').then(r=>r.json());document.getElementById('logs').innerHTML=l.logs.slice(-20).reverse().map(x=>'<div class="log-entry log-'+x.level+'">['+new Date(x.timestamp).toLocaleTimeString()+'] '+x.message+'</div>').join('')}u();setInterval(u,2000)</script></body></html>''', worker_id=socket.gethostname())

if __name__ == "__main__":
    print(f"🚀 Iris Worker v3 启动")
    print(f"WebSocket: {WS_URL}")
    print(f"监控：http://localhost:{WORKER_PORT}/")
    threading.Thread(target=lambda: asyncio.run(websocket_client()), daemon=True).start()
    app.run(host="0.0.0.0", port=WORKER_PORT, debug=False)
