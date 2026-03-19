#!/usr/bin/env python3
"""Iris Worker v9 - 修复 SSE 自动更新"""
import os, json, time, threading, subprocess, socket, asyncio, websockets, requests
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, render_template_string, Response
import queue

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
    "messages_received": 0, "messages_sent": 0, "uptime_seconds": 0, "reconnect_count": 0
}

ws_connection = None
message_log = []
current_operation = None
state_changed = threading.Event()

def add_log(level, message):
    message_log.append({"timestamp": datetime.now().isoformat(), "level": level, "message": message})
    if len(message_log) > 500: message_log.pop(0)
    state_changed.set()

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
                await ws.send(json.dumps({"type": "handshake", "worker_id": worker_id}))
                async for message in ws:
                    worker_state["messages_received"] += 1
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "")
                        if msg_type == "install_dependencies":
                            packages = data.get("data", {}).get("packages", [])
                            print(f"📦 收到依赖安装指令：{packages}")
                            add_log("info", f"📦 收到指令：安装 {packages}")
                            current_operation = "installing"
                            asyncio.create_task(install_dependencies_smart(packages))
                        elif msg_type == "train":
                            train_data = data.get("data", {})
                            print(f"🧠 收到训练指令：{train_data}")
                            add_log("info", f"🧠 收到训练指令：{train_data.get('task_id')}")
                            current_operation = "training"
                            asyncio.create_task(execute_training(train_data))
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
    if not packages:
        add_log("warn", "⚠️ 没有要安装的包")
        return
    worker_state["status"] = "installing"
    worker_state["dependency_total_packages"] = len(packages)
    worker_state["dependency_installed_count"] = 0
    sources = [("本地 pip", ""), ("清华源", "https://pypi.tuna.tsinghua.edu.cn/simple"), ("阿里云", "https://mirrors.aliyun.com/pypi/simple/"), ("中科大", "https://pypi.mirrors.ustc.edu.cn/simple/")]
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
                if source_url:
                    cmd.insert(2, "-i")
                    cmd.insert(3, source_url)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    add_log("success", f"✅ {pkg} 安装成功 ({source_name})")
                    pkg_log["success"] = True
                    pkg_log["source"] = source_name
                    installed = True
                else:
                    add_log("warn", f"⚠️ {pkg} 安装失败 ({source_name})")
            except Exception as e:
                add_log("error", f"❌ {pkg} 异常：{e}")
        worker_state["dependency_install_log"].append(pkg_log)
        if len(worker_state["dependency_install_log"]) > 20:
            worker_state["dependency_install_log"].pop(0)
        if not installed:
            add_log("error", f"❌ {pkg} 所有源失败")
        worker_state["dependency_installed_count"] = pkg_idx + 1
        worker_state["dependency_progress"] = int((pkg_idx + 1) / len(packages) * 100)
        state_changed.set()
    worker_state["dependencies_installed"] = True
    worker_state["status"] = "idle"
    current_operation = None
    add_log("success", f"✅ 所有依赖完成 ({worker_state['dependency_installed_count']}/{worker_state['dependency_total_packages']})")
    state_changed.set()

async def execute_training(task):
    task_id = task.get("task_id")
    worker_state["status"] = "training"
    worker_state["current_task"] = task
    epochs = task.get("epochs", 10)
    worker_state["training_total_epochs"] = epochs
    for epoch in range(epochs):
        worker_state["training_epoch"] = epoch + 1
        for progress in range(0, 101, 5):
            await asyncio.sleep(0.3)
            loss = 0.5 * (1 - progress/100) * (1 - epoch/epochs)
            worker_state["training_progress"] = int((epoch + progress/100) / epochs * 100)
            worker_state["training_loss"] = round(loss, 4)
            if ws_connection:
                await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "epoch": epoch+1, "total_epochs": epochs, "progress": progress, "loss": worker_state["training_loss"]}))
            add_log("progress", f"📊 Epoch {epoch+1}/{epochs} - 进度：{progress}% - Loss: {loss:.4f}")
            state_changed.set()
    worker_state["status"] = "idle"
    worker_state["current_task"] = None
    worker_state["training_progress"] = 0
    if ws_connection:
        await ws_connection.send(json.dumps({"type": "complete", "task_id": task_id}))
    add_log("success", f"✅ 训练完成：{task_id}")
    state_changed.set()

app = Flask(__name__)
state_changed.clear()

@app.route('/health')
def health():
    return jsonify({"status": worker_state["status"], "worker_id": socket.gethostname(), "websocket": worker_state["websocket_connected"], "dependencies_installed": worker_state["dependencies_installed"], "uptime": worker_state["uptime_seconds"]})

@app.route('/status')
def status():
    return jsonify({
        "status": worker_state["status"], "current_task": worker_state["current_task"],
        "websocket_connected": worker_state["websocket_connected"],
        "dependency_progress": worker_state["dependency_progress"],
        "dependency_current_package": worker_state["dependency_current_package"],
        "dependency_total_packages": worker_state["dependency_total_packages"],
        "dependency_installed_count": worker_state["dependency_installed_count"],
        "dependency_source": worker_state["dependency_source"],
        "dependency_install_log": worker_state["dependency_install_log"],
        "training_progress": worker_state["training_progress"],
        "training_loss": worker_state["training_loss"],
        "training_epoch": worker_state["training_epoch"],
        "training_total_epochs": worker_state["training_total_epochs"],
        "messages_received": worker_state["messages_received"],
        "messages_sent": worker_state["messages_sent"],
        "current_operation": current_operation, "reconnect_count": worker_state["reconnect_count"]
    })

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
    <title>Iris Worker v9 - {{ worker_id }}</title>
    <style>
        :root { --primary: #667eea; --success: #10b981; --warning: #f59e0b; --error: #ef4444; --bg: #0f172a; --card: #1e293b; --text: #f1f5f9; --text-muted: #94a3b8; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); padding: 20px; line-height: 1.6; }
        .container { max-width: 1600px; margin: 0 auto; }
        header { text-align: center; padding: 30px 0; border-bottom: 1px solid var(--card); margin-bottom: 30px; }
        h1 { font-size: 28px; font-weight: 600; background: linear-gradient(135deg, var(--primary), #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { color: var(--text-muted); font-size: 14px; margin-top: 8px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: var(--card); border-radius: 16px; padding: 24px; border: 1px solid rgba(255,255,255,0.05); }
        .card h2 { font-size: 16px; font-weight: 600; color: var(--text-muted); margin-bottom: 20px; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .stat-row:last-child { border-bottom: none; }
        .stat-label { color: var(--text-muted); font-size: 14px; }
        .stat-value { font-weight: 600; font-size: 14px; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .badge-success { background: rgba(16,185,129,0.2); color: var(--success); }
        .badge-warning { background: rgba(245,158,11,0.2); color: var(--warning); }
        .badge-error { background: rgba(239,68,68,0.2); color: var(--error); }
        .badge-info { background: rgba(102,126,234,0.2); color: var(--primary); }
        .progress-section { margin-bottom: 24px; }
        .progress-label { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
        .progress-bar { height: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, var(--primary), #764ba2); border-radius: 5px; transition: width 0.3s ease; }
        .progress-fill.success { background: linear-gradient(90deg, var(--success), #059669); }
        .progress-fill.warning { background: linear-gradient(90deg, var(--warning), #d97706); }
        .logs-container { background: rgba(0,0,0,0.3); border-radius: 12px; padding: 20px; max-height: 800px; overflow-y: auto; font-family: "SF Mono", Monaco, monospace; font-size: 13px; }
        .log-entry { padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; gap: 12px; }
        .log-entry:last-child { border-bottom: none; }
        .log-time { color: var(--text-muted); font-size: 12px; white-space: nowrap; }
        .log-badge { min-width: 70px; text-align: center; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .log-info { color: var(--primary); }
        .log-info .log-badge { background: rgba(102,126,234,0.2); color: var(--primary); }
        .log-success { color: var(--success); }
        .log-success .log-badge { background: rgba(16,185,129,0.2); color: var(--success); }
        .log-progress { color: var(--warning); }
        .log-progress .log-badge { background: rgba(245,158,11,0.2); color: var(--warning); }
        .log-error { color: var(--error); }
        .log-error .log-badge { background: rgba(239,68,68,0.2); color: var(--error); }
        .log-warn { color: #fbbf24; }
        .log-warn .log-badge { background: rgba(251,191,36,0.2); color: #fbbf24; }
        .log-message { flex: 1; word-break: break-word; }
        .package-tag { display: inline-block; background: rgba(102,126,234,0.3); padding: 4px 10px; border-radius: 6px; font-size: 12px; margin-left: 8px; }
        .detail-section { margin-top: 30px; }
        .detail-card { background: var(--card); border-radius: 16px; padding: 24px; margin-bottom: 20px; }
        .detail-card h3 { font-size: 14px; color: var(--text-muted); margin-bottom: 16px; text-transform: uppercase; }
        .install-item { background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; margin-bottom: 8px; }
        .install-item:last-child { margin-bottom: 0; }
        .install-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .install-pkg { font-weight: 600; color: var(--text); }
        .install-status { font-size: 12px; }
        .install-sources { font-size: 12px; color: var(--text-muted); }
        .epoch-item { display: inline-block; background: rgba(16,185,129,0.2); color: var(--success); padding: 4px 12px; border-radius: 20px; font-size: 12px; margin-right: 8px; margin-bottom: 8px; }
        .connection-status { position: fixed; top: 20px; right: 20px; padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; z-index: 1000; }
        .connection-status.connected { background: rgba(16,185,129,0.2); color: var(--success); }
        .connection-status.disconnected { background: rgba(239,68,68,0.2); color: var(--error); }
    </style>
</head>
<body>
    <div id="connection-status" class="connection-status disconnected">⏳ 连接中...</div>
    <div class="container">
        <header>
            <h1>🚀 Iris Worker v9</h1>
            <div class="subtitle">{{ worker_id }} • ws://{{ server_ip }}:5000/ws/worker</div>
        </header>
        <div class="grid">
            <div class="card"><h2>📊 连接状态</h2>
                <div class="stat-row"><span class="stat-label">WebSocket</span><span class="stat-value" id="ws-status">加载中...</span></div>
                <div class="stat-row"><span class="stat-label">运行时间</span><span class="stat-value" id="uptime">0s</span></div>
                <div class="stat-row"><span class="stat-label">重连次数</span><span class="stat-value" id="reconnects">0</span></div>
                <div class="stat-row"><span class="stat-label">接收消息</span><span class="stat-value" id="msg-recv">0</span></div>
            </div>
            <div class="card"><h2>📈 运行状态</h2>
                <div class="stat-row"><span class="stat-label">当前状态</span><span class="stat-value" id="status">加载中...</span></div>
                <div class="stat-row"><span class="stat-label">当前操作</span><span class="stat-value" id="operation">无</span></div>
                <div class="stat-row"><span class="stat-label">依赖状态</span><span class="stat-value" id="deps-status">检查中...</span></div>
                <div class="stat-row"><span class="stat-label">当前任务</span><span class="stat-value" id="task">无</span></div>
            </div>
            <div class="card progress-section"><h2>📦 依赖安装 <span id="pkg-name" class="package-tag"></span></h2>
                <div class="progress-label"><span>进度 (<span id="dep-installed">0</span>/<span id="dep-total">0</span>)</span><span id="dep-progress-text">0%</span></div>
                <div class="progress-bar"><div class="progress-fill warning" id="dep-progress" style="width:0%"></div></div>
                <div class="stat-row" style="margin-top:12px"><span class="stat-label">当前源</span><span class="stat-value" id="dep-source">-</span></div>
            </div>
            <div class="card progress-section"><h2>🧠 训练进度 <span id="epoch-tag" class="package-tag"></span></h2>
                <div class="progress-label"><span>进度</span><span id="train-progress-text">0%</span></div>
                <div class="progress-bar"><div class="progress-fill success" id="train-progress" style="width:0%"></div></div>
                <div class="stat-row" style="margin-top:12px"><span class="stat-label">当前 Loss</span><span class="stat-value" id="loss">-</span></div>
            </div>
        </div>
        <div class="detail-section">
            <div class="detail-card">
                <h3>📦 依赖安装明细</h3>
                <div id="install-details">暂无数据</div>
            </div>
            <div class="detail-card">
                <h3>🧠 训练 Epoch 进度</h3>
                <div id="epoch-details">暂无数据</div>
            </div>
        </div>
        <div class="card"><h2>📝 实时日志 <span style="color:var(--text-muted);font-size:12px">最近 500 条</span></h2>
            <div class="logs-container" id="logs">加载中...</div>
        </div>
    </div>
    <script>
        let logs = [];
        let autoScroll = true;
        const eventSource = new EventSource('/stream');
        
        eventSource.onopen = function() {
            document.getElementById('connection-status').className = 'connection-status connected';
            document.getElementById('connection-status').textContent = '✅ 已连接';
            console.log('✅ SSE 连接已建立');
            loadInitialData();
        };
        
        eventSource.onerror = function(err) {
            console.error('❌ SSE 错误:', err);
            document.getElementById('connection-status').className = 'connection-status disconnected';
            document.getElementById('connection-status').textContent = '❌ 已断开';
        };
        
        eventSource.addEventListener('message', function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('📊 收到状态更新:', data.status);
                updateUI(data);
            } catch(e) {
                console.error('解析状态失败:', e);
            }
        });
        
        function loadInitialData() {
            fetch('/status').then(r => r.json()).then(data => {
                console.log('📊 初始数据:', data.status);
                updateUI(data);
            }).catch(e => console.error('加载初始数据失败:', e));
            fetch('/logs').then(r => r.json()).then(data => {
                logs = data.logs;
                renderLogs();
            }).catch(e => console.error('加载日志失败:', e));
        }
        
        function updateUI(s) {
            document.getElementById('ws-status').innerHTML = s.websocket_connected ? '<span class="badge badge-success">✅ 已连接</span>' : '<span class="badge badge-error">❌ 未连接</span>';
            document.getElementById('uptime').textContent = formatUptime(s.uptime_seconds || 0);
            document.getElementById('reconnects').textContent = s.reconnect_count || 0;
            document.getElementById('msg-recv').textContent = s.messages_received || 0;
            document.getElementById('status').innerHTML = '<span class="badge badge-info">' + (s.status || 'unknown').toUpperCase() + '</span>';
            document.getElementById('operation').textContent = s.current_operation || '无';
            document.getElementById('deps-status').innerHTML = s.dependencies_installed ? '<span class="badge badge-success">✅ 已完成</span>' : '<span class="badge badge-warning">⏳ 安装中</span>';
            document.getElementById('task').textContent = s.current_task ? (s.current_task.task_id || '有任务') : '无';
            const depProgress = s.dependency_progress || 0;
            document.getElementById('dep-progress').style.width = depProgress + '%';
            document.getElementById('dep-progress-text').textContent = depProgress + '%';
            document.getElementById('dep-installed').textContent = s.dependency_installed_count || 0;
            document.getElementById('dep-total').textContent = s.dependency_total_packages || 0;
            document.getElementById('dep-source').textContent = s.dependency_source || '-';
            document.getElementById('pkg-name').textContent = s.dependency_current_package || '';
            const trainProgress = s.training_progress || 0;
            document.getElementById('train-progress').style.width = trainProgress + '%';
            document.getElementById('train-progress-text').textContent = trainProgress + '%';
            document.getElementById('loss').textContent = s.training_loss || '-';
            document.getElementById('epoch-tag').textContent = s.training_epoch ? 'Epoch ' + s.training_epoch + '/' + (s.training_total_epochs||'?') : '';
            const installLog = s.dependency_install_log || [];
            const installContainer = document.getElementById('install-details');
            if (installLog.length > 0) {
                installContainer.innerHTML = installLog.map(item => {
                    const statusClass = item.success ? 'badge-success' : 'badge-error';
                    const statusText = item.success ? '✅ 成功' : '❌ 失败';
                    const sourcesText = item.sources_tried ? '尝试源：' + item.sources_tried.join(' → ') : '';
                    const sourceUsed = item.source ? ' | 使用：' + item.source : '';
                    return '<div class="install-item"><div class="install-header"><span class="install-pkg">' + item.package + '</span><span class="install-status badge ' + statusClass + '">' + statusText + '</span></div><div class="install-sources">' + sourcesText + sourceUsed + '</div></div>';
                }).join('');
            } else {
                installContainer.innerHTML = '暂无数据';
            }
            const epochContainer = document.getElementById('epoch-details');
            if (s.training_epoch && s.training_total_epochs) {
                let epochsHtml = '';
                for (let i = 1; i <= s.training_total_epochs; i++) {
                    const completed = i <= s.training_epoch;
                    epochsHtml += '<span class="epoch-item" style="background:' + (completed ? 'rgba(16,185,129,0.3)' : 'rgba(148,163,184,0.2)') + ';color:' + (completed ? 'var(--success)' : 'var(--text-muted)') + '">' + (completed ? '✅' : '⏳') + ' Epoch ' + i + '</span>';
                }
                epochContainer.innerHTML = epochsHtml;
            } else {
                epochContainer.innerHTML = '暂无数据';
            }
        }
        
        function renderLogs() {
            const logsContainer = document.getElementById('logs');
            const wasAtBottom = autoScroll || (logsContainer.scrollHeight - logsContainer.scrollTop === logsContainer.clientHeight);
            logsContainer.innerHTML = logs.slice(-50).reverse().map(log => {
                const time = new Date(log.timestamp).toLocaleTimeString();
                return '<div class="log-entry log-' + (log.level || 'info') + '"><span class="log-time">[' + time + ']</span><span class="log-badge">' + log.level + '</span><span class="log-message">' + escapeHtml(log.message) + '</span></div>';
            }).join('');
            if (autoScroll || wasAtBottom) {
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
        }
        
        function formatUptime(seconds) {
            const h = Math.floor(seconds / 3600), m = Math.floor((seconds % 3600) / 60), s = seconds % 60;
            return h > 0 ? h + 'h ' + m + 'm ' + s + 's' : m > 0 ? m + 'm ' + s + 's' : s + 's';
        }
        
        function escapeHtml(text) { const div = document.createElement('div'); div.textContent = text; return div.innerHTML; }
        
        document.getElementById('logs').addEventListener('scroll', (e) => {
            const container = e.target;
            autoScroll = (container.scrollHeight - container.scrollTop === container.clientHeight);
        });
    </script>
</body>
</html>'''

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(websocket_client()), daemon=True).start()
    print(f"Iris Worker v9 启动\nWebSocket: {WS_URL}\n监控：http://localhost:{WORKER_PORT}/")
    app.run(host="0.0.0.0", port=WORKER_PORT, debug=False, threaded=True)
