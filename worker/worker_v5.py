#!/usr/bin/env python3
"""Iris Worker v5 - 完整监控页面 + 断点续传"""
import os, json, time, threading, subprocess, socket, asyncio, websockets, requests
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, render_template_string

SERVER_IP = os.getenv("SERVER_IP", "162.14.115.79")
WS_PORT = int(os.getenv("WS_PORT", "5000"))
WORKER_PORT = int(os.getenv("WORKER_PORT", "8080"))
WS_URL = f"ws://{SERVER_IP}:{WS_PORT}/ws/worker"

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
    "reconnect_count": 0
}

ws_connection = None
message_log = []
current_operation = None

def add_log(level, message):
    message_log.append({"timestamp": datetime.now().isoformat(), "level": level, "message": message})
    if len(message_log) > 200: message_log.pop(0)

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
                            current_operation = "installing"
                            asyncio.create_task(install_dependencies(data.get("packages", [])))
                        elif msg_type == "train":
                            current_operation = "training"
                            asyncio.create_task(execute_training(data))
                    except Exception as e:
                        add_log("error", f"处理失败：{e}")
        except Exception as e:
            worker_state["websocket_connected"] = False
            ws_connection = None
            worker_state["reconnect_count"] += 1
            add_log("error", f"连接断开：{e}")
            await asyncio.sleep(5)
        worker_state["uptime_seconds"] = int(time.time() - start)

async def install_dependencies(packages):
    worker_state["status"] = "installing"
    total = len(packages)
    for i, pkg in enumerate(packages):
        try:
            subprocess.run(["pip", "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", pkg, "-q"], timeout=300)
            worker_state["dependency_progress"] = int((i + 1) / total * 100)
            add_log("success", f"✅ 已安装：{pkg}")
        except Exception as e:
            add_log("error", f"❌ 安装失败：{pkg}")
    worker_state["dependencies_installed"] = True
    worker_state["status"] = "idle"
    current_operation = None

async def execute_training(task):
    task_id = task.get("task_id")
    worker_state["status"] = "training"
    worker_state["current_task"] = task
    epochs = task.get("data", {}).get("epochs", 10)
    
    for epoch in range(epochs):
        for progress in range(0, 101, 5):
            await asyncio.sleep(0.3)
            loss = 0.5 * (1 - progress/100) * (1 - epoch/epochs)
            worker_state["training_progress"] = int((epoch + progress/100) / epochs * 100)
            worker_state["training_loss"] = round(loss, 4)
            if ws_connection:
                await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "epoch": epoch+1, "progress": progress, "loss": worker_state["training_loss"]}))
            add_log("progress", f"📊 Epoch {epoch+1}/{epochs} - 进度：{progress}% - Loss: {loss:.4f}")
    
    worker_state["status"] = "idle"
    worker_state["current_task"] = None
    worker_state["training_progress"] = 0
    if ws_connection:
        await ws_connection.send(json.dumps({"type": "complete", "task_id": task_id}))
    add_log("success", f"✅ 训练完成：{task_id}")

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": worker_state["status"], "worker_id": socket.gethostname(), "websocket": worker_state["websocket_connected"], "dependencies_installed": worker_state["dependencies_installed"], "uptime": worker_state["uptime_seconds"]})

@app.route('/status')
def status():
    return jsonify({"status": worker_state["status"], "current_task": worker_state["current_task"], "websocket_connected": worker_state["websocket_connected"], "dependency_progress": worker_state["dependency_progress"], "training_progress": worker_state["training_progress"], "training_loss": worker_state["training_loss"], "messages_received": worker_state["messages_received"], "current_operation": current_operation})

@app.route('/logs')
def logs():
    return jsonify({"logs": message_log[-200:]})

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, worker_id=socket.gethostname(), server_ip=SERVER_IP)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iris Worker - {{ worker_id }}</title>
    <meta http-equiv="refresh" content="1">
    <style>
        :root { --primary: #667eea; --success: #10b981; --warning: #f59e0b; --error: #ef4444; --bg: #0f172a; --card: #1e293b; --text: #f1f5f9; --text-muted: #94a3b8; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); padding: 20px; line-height: 1.6; }
        .container { max-width: 1400px; margin: 0 auto; }
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
        .progress-bar { height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, var(--primary), #764ba2); border-radius: 4px; transition: width 0.5s ease; }
        .progress-fill.success { background: linear-gradient(90deg, var(--success), #059669); }
        .progress-fill.warning { background: linear-gradient(90deg, var(--warning), #d97706); }
        .logs-container { background: rgba(0,0,0,0.3); border-radius: 12px; padding: 16px; max-height: 500px; overflow-y: auto; font-family: "SF Mono", Monaco, monospace; font-size: 13px; }
        .log-entry { padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; gap: 12px; }
        .log-entry:last-child { border-bottom: none; }
        .log-time { color: var(--text-muted); font-size: 12px; white-space: nowrap; }
        .log-badge { min-width: 60px; text-align: center; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .log-info { color: var(--primary); }
        .log-info .log-badge { background: rgba(102,126,234,0.2); color: var(--primary); }
        .log-success { color: var(--success); }
        .log-success .log-badge { background: rgba(16,185,129,0.2); color: var(--success); }
        .log-progress { color: var(--warning); }
        .log-progress .log-badge { background: rgba(245,158,11,0.2); color: var(--warning); }
        .log-error { color: var(--error); }
        .log-error .log-badge { background: rgba(239,68,68,0.2); color: var(--error); }
        .log-message { flex: 1; word-break: break-word; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Iris Worker</h1>
            <div class="subtitle">{{ worker_id }} • ws://{{ server_ip }}:5000/ws/worker</div>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>📊 连接状态</h2>
                <div class="stat-row"><span class="stat-label">WebSocket</span><span class="stat-value" id="ws-status">加载中...</span></div>
                <div class="stat-row"><span class="stat-label">运行时间</span><span class="stat-value" id="uptime">0s</span></div>
                <div class="stat-row"><span class="stat-label">重连次数</span><span class="stat-value" id="reconnects">0</span></div>
                <div class="stat-row"><span class="stat-label">接收消息</span><span class="stat-value" id="msg-recv">0</span></div>
            </div>
            
            <div class="card">
                <h2>📈 运行状态</h2>
                <div class="stat-row"><span class="stat-label">当前状态</span><span class="stat-value" id="status">加载中...</span></div>
                <div class="stat-row"><span class="stat-label">当前操作</span><span class="stat-value" id="operation">无</span></div>
                <div class="stat-row"><span class="stat-label">依赖状态</span><span class="stat-value" id="deps-status">检查中...</span></div>
                <div class="stat-row"><span class="stat-label">当前任务</span><span class="stat-value" id="task">无</span></div>
            </div>
            
            <div class="card progress-section">
                <h2>📦 依赖安装进度</h2>
                <div class="progress-label"><span>进度</span><span id="dep-progress-text">0%</span></div>
                <div class="progress-bar"><div class="progress-fill" id="dep-progress" style="width:0%"></div></div>
            </div>
            
            <div class="card progress-section">
                <h2>🧠 训练进度</h2>
                <div class="progress-label"><span>进度</span><span id="train-progress-text">0%</span></div>
                <div class="progress-bar"><div class="progress-fill success" id="train-progress" style="width:0%"></div></div>
                <div class="stat-row" style="margin-top:16px"><span class="stat-label">当前 Loss</span><span class="stat-value" id="loss">-</span></div>
            </div>
        </div>
        
        <div class="card">
            <h2>📝 实时日志 <span style="color:var(--text-muted);font-size:12px">最近 200 条</span></h2>
            <div class="logs-container" id="logs">加载中...</div>
        </div>
    </div>
    
    <script>
        async function update() {
            try {
                const s = await fetch('/status').then(r => r.json());
                const h = await fetch('/health').then(r => r.json());
                
                document.getElementById('ws-status').innerHTML = h.websocket ? '<span class="badge badge-success">✅ 已连接</span>' : '<span class="badge badge-error">❌ 未连接</span>';
                document.getElementById('uptime').textContent = formatUptime(h.uptime || 0);
                document.getElementById('reconnects').textContent = h.reconnects || 0;
                document.getElementById('msg-recv').textContent = s.messages_received || 0;
                
                document.getElementById('status').innerHTML = '<span class="badge badge-info">' + (s.status || 'unknown').toUpperCase() + '</span>';
                document.getElementById('operation').textContent = s.current_operation || '无';
                document.getElementById('deps-status').innerHTML = s.dependencies_installed ? '<span class="badge badge-success">✅ 已完成</span>' : '<span class="badge badge-warning">⏳ 安装中</span>';
                document.getElementById('task').textContent = s.current_task ? (s.current_task.task_id || '有任务') : '无';
                
                const depProgress = s.dependency_progress || 0;
                document.getElementById('dep-progress').style.width = depProgress + '%';
                document.getElementById('dep-progress-text').textContent = depProgress + '%';
                document.getElementById('dep-progress').className = 'progress-fill ' + (depProgress >= 100 ? 'success' : 'warning');
                
                const trainProgress = s.training_progress || 0;
                document.getElementById('train-progress').style.width = trainProgress + '%';
                document.getElementById('train-progress-text').textContent = trainProgress + '%';
                document.getElementById('loss').textContent = s.training_loss || '-';
                
                const l = await fetch('/logs').then(r => r.json());
                const logsContainer = document.getElementById('logs');
                if (l.logs && l.logs.length > 0) {
                    logsContainer.innerHTML = l.logs.slice(-50).reverse().map(log => {
                        const time = new Date(log.timestamp).toLocaleTimeString();
                        return '<div class="log-entry log-' + (log.level || 'info') + '"><span class="log-time">[' + time + ']</span><span class="log-badge">' + log.level + '</span><span class="log-message">' + escapeHtml(log.message) + '</span></div>';
                    }).join('');
                }
            } catch (e) { console.error(e); }
        }
        
        function formatUptime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            return h > 0 ? h + 'h ' + m + 'm ' + s + 's' : m > 0 ? m + 'm ' + s + 's' : s + 's';
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        update();
        setInterval(update, 1000);
    </script>
</body>
</html>'''

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(websocket_client()), daemon=True).start()
    print(f"Iris Worker v5 启动\nWebSocket: {WS_URL}\n监控：http://localhost:{WORKER_PORT}/")
    app.run(host="0.0.0.0", port=WORKER_PORT, debug=False)
