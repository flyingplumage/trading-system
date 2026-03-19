#!/bin/bash
# Iris Worker Docker 部署脚本
# 纯 WebSocket 方案，不依赖 HTTP 服务

set -e

SERVER_IP="${SERVER_IP:-162.14.115.79}"
WS_PORT="${WS_PORT:-5000}"
WORK_DIR=~/iris-worker

echo "============================================================"
echo "🚀 Iris Worker Docker 部署（纯 WebSocket）"
echo "============================================================"
echo ""
echo "服务器：$SERVER_IP:$WS_PORT"
echo "工作目录：$WORK_DIR"
echo ""

# 1. 创建工作目录
echo "[1/5] 创建工作目录..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 2. 创建 Dockerfile（直接嵌入脚本）
echo "[2/5] 创建 Dockerfile..."
cat > Dockerfile << 'DOCKERFILE'
FROM python:3.10-slim
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir flask requests websockets psutil
WORKDIR /app
COPY worker.py .
RUN mkdir -p /app/models
ENV SERVER_IP=162.14.115.79
ENV WS_PORT=5000
CMD ["python3", "worker.py"]
DOCKERFILE
echo "✅ Dockerfile 已创建"

# 3. 创建 worker.py（直接嵌入脚本）
echo "[3/5] 创建 worker.py..."
cat > worker.py << 'WORKERPY'
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, json, time, threading, subprocess, socket, asyncio, websockets, requests, shutil, base64
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, Response, send_file

try:
    import psutil
except:
    psutil = None

SERVER_IP = os.getenv("SERVER_IP", "162.14.115.79")
WS_PORT = int(os.getenv("WS_PORT", "5000"))
WORKER_PORT = int(os.getenv("WORKER_PORT", "8080"))
WS_URL = f"ws://{SERVER_IP}:{WS_PORT}/ws/worker"

worker_state = {
    "status": "initializing", "current_task": None, "websocket_connected": False,
    "dependencies_installed": False, "dependency_progress": 0,
    "dependency_current_package": "", "dependency_total_packages": 0,
    "dependency_installed_count": 0, "dependency_source": "pip",
    "dependency_install_log": [],
    "training_progress": 0, "training_loss": 0, "training_epoch": 0, "training_total_epochs": 0,
    "messages_received": 0, "messages_sent": 0, "uptime_seconds": 0, "reconnect_count": 0,
    "worker_version": "v24",
    "hardware": {"cpu_percent": 0, "memory_percent": 0, "disk_percent": 0},
    "hardware_history": {"cpu": [], "memory": [], "disk": []}
}

ws_connection = None
message_log = []
current_operation = None
state_changed = threading.Event()
app = Flask(__name__)
state_changed.clear()
HTML_PATH = Path("/app/index.html")

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>Iris Worker v24</title>
<style>:root{--bg:#0f172a;--card:#1e293b;--text:#f1f5f9}*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);padding:15px}.container{max-width:1800px;margin:0 auto}header{margin-bottom:15px}.top-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:15px}.card{background:var(--card);border-radius:10px;padding:15px}.card h2{font-size:12px;margin-bottom:12px}.hw-chart{height:80px;margin-top:10px}.hw-line polyline{fill:none;stroke-width:1.5}.hw-line.cpu polyline{stroke:#3b82f6}.hw-line.memory polyline{stroke:#8b5cf6}.hw-line.disk polyline{stroke:#ec4899}.hw-current{text-align:center;margin-bottom:5px}.hw-label{text-align:center;font-size:10px}.bottom-grid{display:grid;grid-template-columns:2fr 1fr;gap:12px}.logs-container{max-height:600px;overflow-y:visible;font-family:monospace;font-size:11px}.log-entry{padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.03)}</style>
</head>
<body><div class="container"><header><h1>Iris Worker v24</h1><div id="subtitle">Loading...</div></header><div class="top-grid"><div class="card"><h2>Connection</h2><div id="ws-status">-</div></div><div class="card"><h2>Status</h2><div id="op-status">-</div></div><div class="card"><h2>CPU</h2><div class="hw-current" id="cpu-current">0%</div><div class="hw-chart cpu"><svg viewBox="0 0 300 80"><polyline id="cpu-polyline" points=""></polyline></svg></div></div><div class="card"><h2>Memory</h2><div class="hw-current" id="memory-current">0%</div><div class="hw-chart memory"><svg viewBox="0 0 300 80"><polyline id="memory-polyline" points=""></polyline></svg></div></div><div class="card"><h2>Disk</h2><div class="hw-current" id="disk-current">0%</div><div class="hw-chart disk"><svg viewBox="0 0 300 80"><polyline id="disk-polyline" points=""></polyline></svg></div></div></div><div class="bottom-grid"><div class="card"><h2>Logs</h2><div class="logs-container" id="logs"></div></div><div class="card"><h2>Dependencies</h2><div id="install-details"></div></div></div></div>
<script>const eventSource=new EventSource('/stream');eventSource.onopen=()=>loadInitialData();eventSource.addEventListener('message',e=>updateUI(JSON.parse(e.data)));function loadInitialData(){fetch('/status').then(r=>r.json()).then(updateUI);fetch('/logs').then(r=>r.json()).then(d=>renderLogs(d.logs));}function updateUI(s){document.getElementById('subtitle').textContent=s.worker_id+' - ws://'+s.worker_id;document.getElementById('ws-status').textContent=s.websocket_connected?'Connected':'Disconnected';document.getElementById('op-status').textContent=s.status||'-';document.getElementById('cpu-current').textContent=(s.hardware?.cpu_percent||0)+'%';document.getElementById('memory-current').textContent=(s.hardware?.memory_percent||0)+'%';document.getElementById('disk-current').textContent=(s.hardware?.disk_percent||0)+'%';renderChart('cpu',s.hardware_history?.cpu||[]);renderChart('memory',s.hardware_history?.memory||[]);renderChart('disk',s.hardware_history?.disk||[]);document.getElementById('install-details').innerHTML=(s.dependency_install_log||[]).map(i=>i.package+' '+(i.success?'OK':'Wait')).join('<br>');}function renderChart(t,d){const p=document.getElementById(t+'-polyline');if(!p||d.length<2)return;const w=300,h=80,s=w/(d.length-1);p.setAttribute('points',d.map((v,i)=>(i*s)+','+(h-(v/100*h))).join(' '));}function renderLogs(logs){document.getElementById('logs').innerHTML=(logs||[]).slice(-100).reverse().map(l=>'['+new Date(l.timestamp).toLocaleTimeString()+'] ['+l.level+'] '+l.message).join('<br>');}</script>
</body></html>'''

def get_hardware_info():
    if psutil:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {"cpu_percent": round(psutil.cpu_percent(interval=0.1), 1), "memory_percent": round(mem.percent, 1), "disk_percent": round(disk.percent, 1)}
    return {"cpu_percent": 0, "memory_percent": 0, "disk_percent": 0}

def add_log(level, message):
    message_log.append({"timestamp": datetime.now().isoformat(), "level": level, "message": message})
    if len(message_log) > 500: message_log.pop(0)
    state_changed.set()

async def hardware_monitor():
    while True:
        hw = get_hardware_info()
        worker_state["hardware"] = hw
        for key in ["cpu", "memory", "disk"]:
            worker_state["hardware_history"][key].append(hw[f"{key}_percent"])
            if len(worker_state["hardware_history"][key]) > 30:
                worker_state["hardware_history"][key].pop(0)
        state_changed.set()
        await asyncio.sleep(2)

async def upgrade_worker(version, script_url, restart):
    add_log("info", f"Starting upgrade to {version}")
    try:
        add_log("info", f"Downloading {version}...")
        state_changed.set()
        resp = requests.get(script_url, timeout=60)
        if resp.status_code == 200:
            if os.path.exists("/app/worker.py"):
                shutil.copy("/app/worker.py", "/app/worker.py.bak")
                add_log("info", "Backed up old version")
            with open("/app/worker.py", "w", encoding='utf-8') as f:
                f.write(resp.text)
            add_log("success", f"Downloaded {version} successfully")
            state_changed.set()
            if restart:
                add_log("info", "Restarting...")
                state_changed.set()
                time.sleep(2)
                os._exit(0)
        else:
            add_log("error", f"Download failed: {resp.status_code}")
    except Exception as e:
        add_log("error", f"Upgrade failed: {e}")

async def websocket_client():
    global ws_connection, worker_state, current_operation
    worker_id = socket.gethostname()
    start = time.time()
    while True:
        try:
            async with websockets.connect(WS_URL, additional_headers={"Worker-ID": worker_id, "Worker-Port": str(WORKER_PORT)}) as ws:
                ws_connection = ws
                worker_state["websocket_connected"] = True
                worker_state["status"] = "connected"
                worker_state["reconnect_count"] = 0
                add_log("info", "WebSocket connected successfully")
                await ws.send(json.dumps({"type": "handshake", "worker_id": worker_id, "version": worker_state["worker_version"]}))
                async for message in ws:
                    worker_state["messages_received"] += 1
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "")
                        if msg_type == "install_dependencies":
                            packages = data.get("data", {}).get("packages", [])
                            add_log("info", f"Received command: install {packages}")
                            current_operation = "installing"
                            asyncio.create_task(install_dependencies_smart(packages))
                        elif msg_type == "train":
                            train_data = data.get("data", {})
                            add_log("info", f"Received training command: {train_data.get('task_id')}")
                            current_operation = "training"
                            asyncio.create_task(execute_training(train_data))
                        elif msg_type == "upgrade":
                            upgrade_data = data.get("data", {})
                            version = upgrade_data.get("version", "unknown")
                            script_url = upgrade_data.get("script_url", "")
                            restart = upgrade_data.get("restart", True)
                            add_log("info", f"Received upgrade command: {version}")
                            asyncio.create_task(upgrade_worker(version, script_url, restart))
                    except Exception as e:
                        add_log("error", f"Processing failed: {e}")
        except Exception as e:
            worker_state["websocket_connected"] = False
            ws_connection = None
            worker_state["reconnect_count"] += 1
            add_log("error", f"Connection lost: {e}")
            await asyncio.sleep(5)
        worker_state["uptime_seconds"] = int(time.time() - start)

async def install_dependencies_smart(packages):
    if not packages: return
    worker_state["status"] = "installing"
    worker_state["dependency_total_packages"] = len(packages)
    worker_state["dependency_installed_count"] = 0
    sources = [("local pip", ""), ("tsinghua", "https://pypi.tuna.tsinghua.edu.cn/simple")]
    for pkg_idx, pkg in enumerate(packages):
        worker_state["dependency_current_package"] = pkg
        installed = False
        pkg_log = {"package": pkg, "sources_tried": [], "success": False, "source": ""}
        for source_name, source_url in sources:
            if installed: break
            worker_state["dependency_source"] = source_name
            pkg_log["sources_tried"].append(source_name)
            add_log("info", f"Installing {pkg} ({source_name})...")
            state_changed.set()
            try:
                cmd = ["pip", "install", pkg, "-q"]
                if source_url: cmd = ["pip", "install", "-i", source_url, pkg, "-q"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    add_log("success", f"{pkg} installed successfully ({source_name})")
                    pkg_log["success"] = True
                    pkg_log["source"] = source_name
                    installed = True
                else: add_log("warn", f"{pkg} installation failed ({source_name})")
            except Exception as e: add_log("error", f"{pkg} exception: {e}")
        worker_state["dependency_install_log"].append(pkg_log)
        if len(worker_state["dependency_install_log"]) > 10: worker_state["dependency_install_log"].pop(0)
        worker_state["dependency_installed_count"] = pkg_idx + 1
        worker_state["dependency_progress"] = int((pkg_idx + 1) / len(packages) * 100)
        state_changed.set()
    worker_state["dependencies_installed"] = True
    worker_state["status"] = "idle"
    current_operation = None
    add_log("success", "All dependencies installed")
    state_changed.set()

async def execute_training(task):
    task_id = task.get("task_id")
    worker_state["status"] = "training"
    worker_state["current_task"] = task
    epochs = task.get("epochs", 10)
    worker_state["training_total_epochs"] = epochs
    for epoch in range(epochs):
        worker_state["training_epoch"] = epoch + 1
        for progress in range(0, 101, 10):
            await asyncio.sleep(0.2)
            loss = 0.5 * (1 - progress/100) * (1 - epoch/epochs)
            worker_state["training_progress"] = int((epoch + progress/100) / epochs * 100)
            worker_state["training_loss"] = round(loss, 4)
            add_log("progress", f"Epoch {epoch+1}/{epochs} - {progress}% - Loss:{loss:.3f}")
            state_changed.set()
    worker_state["status"] = "idle"
    worker_state["current_task"] = None
    worker_state["training_progress"] = 0
    add_log("success", f"Training complete: {task_id}")
    state_changed.set()

@app.route('/health')
def health():
    return jsonify({"status": worker_state["status"], "worker_id": socket.gethostname(), "websocket": worker_state["websocket_connected"], "version": worker_state["worker_version"]})

@app.route('/status')
def status():
    return jsonify(worker_state)

@app.route('/logs')
def logs():
    return jsonify({"logs": message_log[-500:]})

@app.route('/stream')
def stream():
    def generate():
        last_state = None
        while True:
            state_changed.wait(timeout=1)
            state_changed.clear()
            current_state = json.dumps(worker_state, ensure_ascii=False)
            if current_state != last_state:
                last_state = current_state
                yield f"data: {current_state}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.route('/')
def index():
    if not HTML_PATH.exists():
        with open(HTML_PATH, 'w', encoding='utf-8') as f:
            f.write(HTML_TEMPLATE)
    return send_file(str(HTML_PATH), mimetype='text/html; charset=utf-8')

if __name__ == "__main__":
    os.makedirs("/app/models", exist_ok=True)
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)
    print(f"HTML template created: {HTML_PATH}")
    threading.Thread(target=lambda: asyncio.run(websocket_client()), daemon=True).start()
    if psutil:
        threading.Thread(target=lambda: asyncio.run(hardware_monitor()), daemon=True).start()
    print(f"Iris Worker v24 started\nWebSocket: {WS_URL}\nMonitor: http://localhost:{WORKER_PORT}/")
    app.run(host="0.0.0.0", port=WORKER_PORT, debug=False, threaded=True)
WORKERPY
echo "✅ worker.py 已创建"

# 4. 构建镜像
echo "[4/5] 构建 Docker 镜像..."
docker build -t iris-worker:latest . 2>&1 | tail -10
echo "✅ 镜像构建完成"

# 5. 启动容器
echo "[5/5] 启动容器..."
docker rm -f iris-worker 2>/dev/null || true

docker run -d \
  --name iris-worker \
  -e SERVER_IP="$SERVER_IP" \
  -e WS_PORT="$WS_PORT" \
  -p 8080:8080 \
  --restart unless-stopped \
  iris-worker:latest

sleep 10

# 验证
echo ""
echo "📊 验证服务..."
if curl -s "http://localhost:8080/health" 2>/dev/null | grep -q "healthy"; then
    echo "✅ Worker 已启动"
else
    echo "⚠️  服务启动中..."
fi

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo "🔌 WebSocket: ws://$SERVER_IP:$WS_PORT/ws/worker"
echo ""
echo "📋 常用命令:"
echo "   查看日志：docker logs -f iris-worker"
echo "   查看状态：curl http://localhost:8080/health"
echo "   重启服务：docker restart iris-worker"
echo ""
echo "🎯 纯 WebSocket 方案："
echo "   ✅ 不需要 HTTP 服务"
echo "   ✅ 代码已打包进镜像"
echo "   ✅ 远程升级通过 WebSocket"
echo ""

# 自动打开监控面板
echo "🌐 5 秒后自动打开监控面板..."
sleep 5
open "http://localhost:8080/" 2>/dev/null || true
