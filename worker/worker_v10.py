#!/usr/bin/env python3
"""Iris Worker v10 - 紧凑一屏布局 + 远程升级"""
import os, json, time, threading, subprocess, socket, asyncio, websockets, requests, shutil
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, render_template_string, Response

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
    "messages_received": 0, "uptime_seconds": 0, "reconnect_count": 0,
    "worker_version": "v10"
}

ws_connection = None
message_log = []
current_operation = None
state_changed = threading.Event()

def add_log(level, message):
    message_log.append({"timestamp": datetime.now().isoformat(), "level": level, "message": message})
    if len(message_log) > 200: message_log.pop(0)
    state_changed.set()

async def upgrade_worker(version, script_url, restart):
    """远程升级 Worker"""
    add_log("info", f"🔄 开始升级到 {version}")
    try:
        add_log("info", f"📥 下载 {version}...")
        state_changed.set()
        resp = requests.get(script_url, timeout=60)
        if resp.status_code == 200:
            backup_path = "/app/worker.py.bak"
            if os.path.exists("/app/worker.py"):
                shutil.copy("/app/worker.py", backup_path)
                add_log("info", f"💾 已备份旧版本")
            with open("/app/worker.py", "w") as f:
                f.write(resp.text)
            add_log("success", f"✅ 下载 {version} 成功")
            state_changed.set()
            if restart:
                add_log("info", f"🔄 重启中...")
                state_changed.set()
                time.sleep(2)
                os._exit(0)
        else:
            add_log("error", f"❌ 下载失败：{resp.status_code}")
    except Exception as e:
        add_log("error", f"❌ 升级失败：{e}")

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
                add_log("info", "✅ WebSocket 已连接")
                await ws.send(json.dumps({"type": "handshake", "worker_id": worker_id, "version": worker_state["worker_version"]}))
                async for message in ws:
                    worker_state["messages_received"] += 1
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "")
                        if msg_type == "install_dependencies":
                            packages = data.get("data", {}).get("packages", [])
                            add_log("info", f"📦 收到指令：安装 {packages}")
                            current_operation = "installing"
                            asyncio.create_task(install_dependencies_smart(packages))
                        elif msg_type == "train":
                            train_data = data.get("data", {})
                            add_log("info", f"🧠 收到训练指令：{train_data.get('task_id')}")
                            current_operation = "training"
                            asyncio.create_task(execute_training(train_data))
                        elif msg_type == "upgrade":
                            upgrade_data = data.get("data", {})
                            version = upgrade_data.get("version", "unknown")
                            script_url = upgrade_data.get("script_url", "")
                            restart = upgrade_data.get("restart", True)
                            add_log("info", f"🔄 收到升级指令：{version}")
                            asyncio.create_task(upgrade_worker(version, script_url, restart))
                    except Exception as e:
                        add_log("error", f"处理失败：{e}")
        except Exception as e:
            worker_state["websocket_connected"] = False
            ws_connection = None
            worker_state["reconnect_count"] += 1
            add_log("error", f"连接断开：{e}")
            await asyncio.sleep(5)
        worker_state["uptime_seconds"] = int(time.time() - start)

async def install_dependencies_smart(packages):
    if not packages: return
    worker_state["status"] = "installing"
    worker_state["dependency_total_packages"] = len(packages)
    worker_state["dependency_installed_count"] = 0
    sources = [("本地 pip", ""), ("清华源", "https://pypi.tuna.tsinghua.edu.cn/simple")]
    for pkg_idx, pkg in enumerate(packages):
        worker_state["dependency_current_package"] = pkg
        installed = False
        pkg_log = {"package": pkg, "sources_tried": [], "success": False, "source": ""}
        for source_name, source_url in sources:
            if installed: break
            worker_state["dependency_source"] = source_name
            pkg_log["sources_tried"].append(source_name)
            add_log("info", f"📦 安装 {pkg} ({source_name})...")
            state_changed.set()
            try:
                cmd = ["pip", "install", pkg, "-q"]
                if source_url: cmd = ["pip", "install", "-i", source_url, pkg, "-q"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    add_log("success", f"✅ {pkg} 安装成功 ({source_name})")
                    pkg_log["success"] = True
                    pkg_log["source"] = source_name
                    installed = True
                else: add_log("warn", f"⚠️ {pkg} 安装失败 ({source_name})")
            except Exception as e: add_log("error", f"❌ {pkg} 异常：{e}")
        worker_state["dependency_install_log"].append(pkg_log)
        if len(worker_state["dependency_install_log"]) > 10: worker_state["dependency_install_log"].pop(0)
        worker_state["dependency_installed_count"] = pkg_idx + 1
        worker_state["dependency_progress"] = int((pkg_idx + 1) / len(packages) * 100)
        state_changed.set()
    worker_state["dependencies_installed"] = True
    worker_state["status"] = "idle"
    current_operation = None
    add_log("success", f"✅ 所有依赖完成")
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
    add_log("success", f"✅ 训练完成：{task_id}")
    state_changed.set()

app = Flask(__name__)
state_changed.clear()

@app.route('/health')
def health():
    return jsonify({"status": worker_state["status"], "worker_id": socket.gethostname(), "websocket": worker_state["websocket_connected"], "version": worker_state["worker_version"]})

@app.route('/status')
def status():
    return jsonify(worker_state)

@app.route('/logs')
def logs():
    return jsonify({"logs": message_log[-200:]})

@app.route('/stream')
def stream():
    def generate():
        last_state = None
        while True:
            state_changed.wait(timeout=1)
            state_changed.clear()
            current_state = json.dumps(worker_state)
            if current_state != last_state:
                last_state = current_state
                yield f"data: {current_state}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, worker_id=socket.gethostname(), server_ip=SERVER_IP)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iris Worker v10 - {{ worker_id }}</title>
    <style>
        :root { --primary: #667eea; --success: #10b981; --warning: #f59e0b; --error: #ef4444; --bg: #0f172a; --card: #1e293b; --text: #f1f5f9; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); padding: 15px; font-size: 13px; }
        .container { max-width: 1400px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid var(--card); }
        h1 { font-size: 20px; background: linear-gradient(135deg, var(--primary), #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 12px; color: #94a3b8; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 15px; }
        .card { background: var(--card); border-radius: 10px; padding: 15px; border: 1px solid rgba(255,255,255,0.05); }
        .card h2 { font-size: 12px; color: #94a3b8; margin-bottom: 12px; text-transform: uppercase; }
        .stat-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 12px; border-bottom: 1px solid rgba(255,255,255,0.03); }
        .stat-row:last-child { border-bottom: none; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
        .badge-success { background: rgba(16,185,129,0.2); color: #10b981; }
        .badge-warning { background: rgba(245,158,11,0.2); color: #f59e0b; }
        .badge-info { background: rgba(102,126,234,0.2); color: #667eea; }
        .progress-bar { height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; margin: 8px 0; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, var(--primary), #764ba2); border-radius: 3px; transition: width 0.3s ease; }
        .progress-fill.success { background: linear-gradient(90deg, #10b981, #059669); }
        .bottom-section { display: grid; grid-template-columns: 2fr 3fr; gap: 12px; }
        .install-list { max-height: 200px; overflow-y: auto; }
        .install-item { background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px; margin-bottom: 6px; font-size: 12px; }
        .install-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
        .logs-container { background: rgba(0,0,0,0.3); border-radius: 10px; padding: 12px; max-height: 200px; overflow-y: auto; font-family: "SF Mono", Monaco, monospace; font-size: 11px; }
        .log-entry { padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.03); display: flex; gap: 8px; }
        .log-time { color: #64748b; font-size: 10px; white-space: nowrap; }
        .log-badge { min-width: 50px; text-align: center; padding: 1px 6px; border-radius: 3px; font-size: 9px; font-weight: 600; text-transform: uppercase; }
        .log-info { color: #667eea; }
        .log-info .log-badge { background: rgba(102,126,234,0.2); }
        .log-success { color: #10b981; }
        .log-success .log-badge { background: rgba(16,185,129,0.2); }
        .log-progress { color: #f59e0b; }
        .log-progress .log-badge { background: rgba(245,158,11,0.2); }
        .log-error { color: #ef4444; }
        .log-error .log-badge { background: rgba(239,68,68,0.2); }
        .log-message { flex: 1; word-break: break-word; }
        .epoch-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
        .epoch-item { background: rgba(16,185,129,0.2); color: #10b981; padding: 3px 10px; border-radius: 12px; font-size: 11px; }
        .epoch-item.pending { background: rgba(148,163,184,0.2); color: #94a3b8; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🚀 Iris Worker <span id="version-badge" class="badge badge-info">v10</span></h1>
                <div class="subtitle">{{ worker_id }} • ws://{{ server_ip }}:5000/ws/worker</div>
            </div>
            <div id="connection-status" class="badge badge-warning">⏳ 连接中...</div>
        </header>
        <div class="grid">
            <div class="card"><h2>📊 连接状态</h2>
                <div class="stat-row"><span>WebSocket</span><span id="ws-status" class="badge">-</span></div>
                <div class="stat-row"><span>运行时间</span><span id="uptime">0s</span></div>
                <div class="stat-row"><span>重连次数</span><span id="reconnects">0</span></div>
            </div>
            <div class="card"><h2>📈 运行状态</h2>
                <div class="stat-row"><span>当前状态</span><span id="status" class="badge">-</span></div>
                <div class="stat-row"><span>当前操作</span><span id="operation">-</span></div>
                <div class="stat-row"><span>接收消息</span><span id="msg-recv">0</span></div>
            </div>
            <div class="card"><h2>📦 依赖安装</h2>
                <div class="stat-row"><span>进度</span><span id="dep-progress-text">0%</span></div>
                <div class="progress-bar"><div class="progress-fill" id="dep-progress" style="width:0%"></div></div>
                <div class="stat-row"><span>当前包</span><span id="pkg-name">-</span></div>
                <div class="stat-row"><span>已安装</span><span id="dep-installed">0/0</span></div>
            </div>
            <div class="card"><h2>🧠 训练进度</h2>
                <div class="stat-row"><span>进度</span><span id="train-progress-text">0%</span></div>
                <div class="progress-bar"><div class="progress-fill success" id="train-progress" style="width:0%"></div></div>
                <div class="stat-row"><span>Epoch</span><span id="epoch">0/0</span></div>
                <div class="stat-row"><span>Loss</span><span id="loss">-</span></div>
            </div>
        </div>
        <div class="bottom-section">
            <div class="card">
                <h2>📦 依赖安装明细</h2>
                <div class="install-list" id="install-details">暂无数据</div>
                <div id="epoch-container" style="margin-top:12px;display:none;">
                    <h2 style="font-size:12px;color:#94a3b8;margin-bottom:8px;">🧠 Epoch 进度</h2>
                    <div class="epoch-list" id="epoch-list"></div>
                </div>
            </div>
            <div class="card">
                <h2>📝 实时日志</h2>
                <div class="logs-container" id="logs">加载中...</div>
            </div>
        </div>
    </div>
    <script>
        let logs = [];
        let autoScroll = true;
        const eventSource = new EventSource('/stream');
        eventSource.onopen = function() {
            document.getElementById('connection-status').className = 'badge badge-success';
            document.getElementById('connection-status').textContent = '✅ 已连接';
            loadInitialData();
        };
        eventSource.onerror = function() {
            document.getElementById('connection-status').className = 'badge badge-error';
            document.getElementById('connection-status').textContent = '❌ 断开';
        };
        eventSource.addEventListener('message', function(event) {
            try { updateUI(JSON.parse(event.data)); } catch(e) { console.error(e); }
        });
        function loadInitialData() {
            fetch('/status').then(r => r.json()).then(updateUI);
            fetch('/logs').then(r => r.json()).then(data => { logs = data.logs; renderLogs(); });
        }
        function updateUI(s) {
            document.getElementById('version-badge').textContent = s.worker_version || 'v10';
            document.getElementById('ws-status').innerHTML = s.websocket_connected ? '<span class="badge badge-success">✅</span>' : '<span class="badge badge-error">❌</span>';
            document.getElementById('uptime').textContent = formatUptime(s.uptime_seconds || 0);
            document.getElementById('reconnects').textContent = s.reconnect_count || 0;
            document.getElementById('msg-recv').textContent = s.messages_received || 0;
            document.getElementById('status').innerHTML = s.status ? '<span class="badge badge-info">' + s.status.toUpperCase() + '</span>' : '-';
            document.getElementById('operation').textContent = s.current_operation || '-';
            const depProgress = s.dependency_progress || 0;
            document.getElementById('dep-progress').style.width = depProgress + '%';
            document.getElementById('dep-progress-text').textContent = depProgress + '%';
            document.getElementById('dep-installed').textContent = `${s.dependency_installed_count || 0}/${s.dependency_total_packages || 0}`;
            document.getElementById('pkg-name').textContent = s.dependency_current_package || '-';
            const trainProgress = s.training_progress || 0;
            document.getElementById('train-progress').style.width = trainProgress + '%';
            document.getElementById('train-progress-text').textContent = trainProgress + '%';
            document.getElementById('epoch').textContent = `${s.training_epoch || 0}/${s.training_total_epochs || 0}`;
            document.getElementById('loss').textContent = s.training_loss || '-';
            const installLog = s.dependency_install_log || [];
            const installContainer = document.getElementById('install-details');
            installContainer.innerHTML = installLog.length > 0 ? installLog.map(item => {
                const statusClass = item.success ? 'badge-success' : 'badge-warning';
                const statusText = item.success ? '✅' : '⏳';
                return `<div class="install-item"><div class="install-header"><span>${item.package}</span><span class="badge ${statusClass}">${statusText}</span></div><div style="color:#64748b;font-size:11px;">${item.source || '等待中...'}</div></div>`;
            }).join('') : '暂无数据';
            const epochContainer = document.getElementById('epoch-container');
            const epochList = document.getElementById('epoch-list');
            if (s.training_epoch && s.training_total_epochs) {
                epochContainer.style.display = 'block';
                let epochsHtml = '';
                for (let i = 1; i <= s.training_total_epochs; i++) {
                    const completed = i <= s.training_epoch;
                    epochsHtml += `<span class="epoch-item ${completed ? '' : 'pending'}">${completed ? '✅' : '⏳'} E${i}</span>`;
                }
                epochList.innerHTML = epochsHtml;
            } else { epochContainer.style.display = 'none'; }
        }
        function renderLogs() {
            const logsContainer = document.getElementById('logs');
            const wasAtBottom = autoScroll || (logsContainer.scrollHeight - logsContainer.scrollTop === logsContainer.clientHeight);
            logsContainer.innerHTML = logs.slice(-30).reverse().map(log => {
                const time = new Date(log.timestamp).toLocaleTimeString();
                return `<div class="log-entry log-${log.level || 'info'}"><span class="log-time">[${time}]</span><span class="log-badge">${log.level}</span><span class="log-message">${escapeHtml(log.message)}</span></div>`;
            }).join('');
            if (autoScroll || wasAtBottom) logsContainer.scrollTop = logsContainer.scrollHeight;
        }
        function formatUptime(seconds) {
            const h = Math.floor(seconds / 3600), m = Math.floor((seconds % 3600) / 60), s = seconds % 60;
            return h > 0 ? `${h}h${m}m${s}s` : m > 0 ? `${m}m${s}s` : `${s}s`;
        }
        function escapeHtml(text) { const div = document.createElement('div'); div.textContent = text; return div.innerHTML; }
        document.getElementById('logs').addEventListener('scroll', (e) => {
            const c = e.target;
            autoScroll = (c.scrollHeight - c.scrollTop === c.clientHeight);
        });
    </script>
</body>
</html>'''

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(websocket_client()), daemon=True).start()
    print(f"Iris Worker v10 启动\nWebSocket: {WS_URL}\n监控：http://localhost:{WORKER_PORT}/")
    app.run(host="0.0.0.0", port=WORKER_PORT, debug=False, threaded=True)
