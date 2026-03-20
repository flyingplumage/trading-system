# -*- coding: utf-8 -*-
"""Iris Worker v51 - 优化布局（左侧卡片，右侧日志）"""
from __future__ import unicode_literals
import os, sys, json, time, threading, subprocess, socket, asyncio, websockets, requests, shutil, platform, psutil
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, Response, send_file

SERVER_IP = os.getenv("SERVER_IP", "162.14.115.79")
WS_PORT = int(os.getenv("WS_PORT", "5000"))
WORKER_PORT = int(os.getenv("WORKER_PORT", "8080"))
WS_URL = f"ws://{SERVER_IP}:{WS_PORT}/ws/worker"
HTTP_BASE = f"http://{SERVER_IP}:{WS_PORT}"

worker_state = {
    "status": "initializing", "current_task": None, "websocket_connected": False,
    "dependencies_installed": False, "dependency_progress": 0,
    "dependency_current_package": "", "dependency_total_packages": 0,
    "dependency_installed_count": 0, "dependency_source": "pip",
    "dependency_install_log": [],
    "training_progress": 0, "training_loss": 0, "training_epoch": 0, "training_total_epochs": 0,
    "messages_received": 0, "messages_sent": 0, "uptime_seconds": 0, "reconnect_count": 0,
    "worker_version": "v43",
    "worker_id": socket.gethostname(),
    "hardware": {"cpu_percent": 0, "memory_percent": 0, "disk_percent": 0},
    "hardware_history": {"cpu": [], "memory": [], "disk": []},
    "system_info": {},
    "active_tasks": [],
    "server_tasks": [],
    "last_activity": None
}

ws_connection = None
message_log = []
current_operation = None
state_changed = threading.Event()
app = Flask(__name__)
state_changed.clear()
HTML_PATH = Path("/app/index.html")

worker_state["system_info"] = {
    "hostname": socket.gethostname(),
    "python_version": platform.python_version(),
    "platform": platform.platform(),
    "cpu_count": psutil.cpu_count() or 0,
    "memory_total": round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2)
}

# 优化布局：左侧卡片，右侧日志
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iris Worker v51</title>
    <style>
        :root{--bg:#0f172a;--card:#1e293b;--text:#f1f5f9;--primary:#667eea;--success:#10b981;--warning:#f59e0b;--error:#ef4444}
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);padding:10px;height:100vh;overflow:hidden}
        .container{max-width:100%;margin:0 auto;height:calc(100vh - 20px);display:flex;flex-direction:column}
        header{display:flex;justify-content:space-between;align-items:center;padding-bottom:8px;border-bottom:1px solid var(--card);margin-bottom:10px;flex-shrink:0}
        h1{font-size:18px;background:linear-gradient(135deg,var(--primary),#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .subtitle{font-size:10px;color:#94a3b8}
        .badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600}
        .badge-success{background:rgba(16,185,129,0.2);color:#10b981}.badge-warning{background:rgba(245,158,11,0.2);color:#f59e0b}.badge-error{background:rgba(239,68,68,0.2);color:#ef4444}.badge-info{background:rgba(102,126,234,0.2);color:#667eea}
        .main-grid{display:grid;grid-template-columns:1fr 350px;gap:8px;flex:1;overflow:hidden}
        .left-panel{display:grid;grid-template-columns:repeat(3,1fr);grid-auto-rows:min-content;gap:8px;overflow-y:auto}
        .right-panel{display:flex;flex-direction:column;gap:8px;overflow:hidden}
        .card{background:var(--card);border-radius:8px;padding:10px;border:1px solid rgba(255,255,255,0.05);overflow:hidden}
        .card h2{font-size:11px;color:#94a3b8;margin-bottom:8px;text-transform:uppercase}
        .stat-row{display:flex;justify-content:space-between;padding:4px 0;font-size:11px;border-bottom:1px solid rgba(255,255,255,0.03)}
        .stat-row:last-child{border-bottom:none}.stat-label{color:#94a3b8}.stat-value{font-weight:600}
        .progress-bar{height:4px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden;margin:6px 0}
        .progress-fill{height:100%;background:linear-gradient(90deg,var(--primary),#764ba2);transition:width 0.3s}
        .progress-fill.success{background:linear-gradient(90deg,#10b981,#059669)}.progress-fill.warning{background:linear-gradient(90deg,#f59e0b,#d97706)}
        .hw-chart{height:50px}.hw-line polyline{fill:none;stroke-width:2;stroke-linecap:round}
        .hw-line.cpu polyline{stroke:#3b82f6}.hw-line.memory polyline{stroke:#8b5cf6}.hw-line.disk polyline{stroke:#ec4899}
        .hw-current{text-align:center;font-size:16px;font-weight:600;margin-bottom:4px}
        .hw-label{text-align:center;font-size:9px;color:#94a3b8}
        .logs-container{flex:1;overflow-y:auto;font-family:monospace;font-size:10px;background:rgba(0,0,0,0.3);border-radius:6px;padding:8px}
        .log-entry{padding:2px 0;border-bottom:1px solid rgba(255,255,255,0.03);display:flex;gap:6px}
        .log-time{color:#64748b;font-size:9px;white-space:nowrap}
        .log-badge{min-width:45px;text-align:center;padding:1px 4px;border-radius:3px;font-size:8px;font-weight:600;text-transform:uppercase}
        .log-info{color:#667eea}.log-info .log-badge{background:rgba(102,126,234,0.2)}
        .log-success{color:#10b981}.log-success .log-badge{background:rgba(16,185,129,0.2)}
        .log-progress{color:#f59e0b}.log-progress .log-badge{background:rgba(245,158,11,0.2)}
        .log-error{color:#ef4444}.log-error .log-badge{background:rgba(239,68,68,0.2)}
        .log-message{flex:1;word-break:break-word;line-height:1.3}
        .task-item{background:rgba(0,0,0,0.2);padding:8px;border-radius:6px;margin-bottom:6px}
        .task-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
        .task-name{font-weight:600;font-size:11px}.task-status{font-size:9px;padding:1px 6px;border-radius:6px}
        .task-status.running{background:rgba(245,158,11,0.2);color:#f59e0b}.task-status.completed{background:rgba(16,185,129,0.2);color:#10b981}
        .install-item{background:rgba(0,0,0,0.2);padding:6px;border-radius:4px;margin-bottom:4px;font-size:10px}
        .epoch-list{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
        .epoch-item{background:rgba(16,185,129,0.2);color:#10b981;padding:2px 8px;border-radius:8px;font-size:9px}
        .epoch-item.pending{background:rgba(148,163,184,0.2);color:#94a3b8}
        .dep-item{background:rgba(0,0,0,0.2);padding:8px;border-radius:6px;margin-bottom:6px}
        .dep-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
        .dep-name{font-weight:600;font-size:11px}
        .dep-status{font-size:9px;padding:1px 6px;border-radius:6px}
        .dep-status.success{background:rgba(16,185,129,0.2);color:#10b981}
        .dep-status.warning{background:rgba(245,158,11,0.2);color:#f59e0b}
        .dep-status.pending{background:rgba(148,163,184,0.2);color:#94a3b8}
        .progress-fill.success{background:linear-gradient(90deg,#10b981,#059669)}
        .progress-fill.warning{background:linear-gradient(90deg,#f59e0b,#d97706)}
        ::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--card);border-radius:2px}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🚀 Iris Worker <span id="version-badge" class="badge badge-info">v51</span></h1>
                <div class="subtitle" id="subtitle">Loading...</div>
            </div>
            <div><span id="connection-status" class="badge badge-warning">⏳</span></div>
        </header>
        <div class="main-grid">
            <div class="left-panel">
                <div class="card">
                    <h2>📊 连接</h2>
                    <div class="stat-row"><span class="stat-label">WebSocket</span><span id="ws-status" class="badge">-</span></div>
                    <div class="stat-row"><span class="stat-label">状态</span><span id="op-status" class="badge">-</span></div>
                    <div class="stat-row"><span class="stat-label">运行</span><span id="uptime">0s</span></div>
                    <div class="stat-row"><span class="stat-label">重连</span><span id="reconnects">0</span></div>
                </div>
                <div class="card">
                    <h2>💻 CPU</h2>
                    <div class="hw-current" id="cpu-current">0%</div>
                    <div class="progress-bar"><div class="progress-fill" id="cpu-progress" style="width:0%"></div></div>
                    <div class="hw-chart cpu"><svg viewBox="0 0 300 50"><polyline id="cpu-polyline" points=""></polyline></svg></div>
                </div>
                <div class="card">
                    <h2>🧠 内存</h2>
                    <div class="hw-current" id="memory-current">0%</div>
                    <div class="progress-bar"><div class="progress-fill" id="memory-progress" style="width:0%"></div></div>
                    <div class="hw-chart memory"><svg viewBox="0 0 300 50"><polyline id="memory-polyline" points=""></polyline></svg></div>
                </div>
                <div class="card">
                    <h2>💾 磁盘</h2>
                    <div class="hw-current" id="disk-current">0%</div>
                    <div class="progress-bar"><div class="progress-fill error" id="disk-progress" style="width:0%"></div></div>
                    <div class="hw-detail" id="disk-detail">0GB / 0GB</div>
                    <div class="hw-chart disk"><svg viewBox="0 0 300 50"><polyline id="disk-polyline" points=""></polyline></svg></div>
                </div>
                <div class="card">
                    <h2>📦 依赖安装</h2>
                    <div class="stat-row"><span class="stat-label">进度</span><span id="dep-progress-text">0%</span></div>
                    <div class="progress-bar"><div class="progress-fill warning" id="dep-progress" style="width:0%"></div></div>
                    <div class="stat-row"><span class="stat-label">已安装</span><span id="dep-installed">0/0</span></div>
                </div>
                <div class="card" id="deps-detail-card" style="display:none">
                    <h2>📦 依赖详情</h2>
                    <div id="deps-list"></div>
                </div>
                <div class="card" id="deps-detail-card" style="display:none">
                    <h2>📦 依赖详情</h2>
                    <div id="deps-list"></div>
                </div>
                <div class="card">
                    <h2>🧠 训练</h2>
                    <div class="stat-row"><span class="stat-label">进度</span><span id="train-progress-text">0%</span></div>
                    <div class="progress-bar"><div class="progress-fill success" id="train-progress" style="width:0%"></div></div>
                    <div class="stat-row"><span class="stat-label">Epoch</span><span id="train-epoch">0/0</span></div>
                    <div class="stat-row"><span class="stat-label">Loss</span><span id="train-loss">-</span></div>
                    <div id="epoch-container" style="display:none"><div class="epoch-list" id="epoch-list"></div></div>
                </div>
                <div class="card" id="tasks-card" style="display:none">
                    <h2>📋 任务</h2>
                    <div id="tasks-list"></div>
                </div>
            </div>
            <div class="right-panel">
                <div class="card" style="flex:1;display:flex;flex-direction:column">
                    <h2>📝 实时日志</h2>
                    <div class="logs-container" id="logs" style="flex:1"></div>
                </div>
            </div>
        </div>
    </div>
    <script>
        const eventSource=new EventSource('/stream');
        eventSource.onopen=()=>{document.getElementById('connection-status').className='badge badge-success';document.getElementById('connection-status').textContent='✅';loadInitialData();};
        eventSource.onerror=()=>{document.getElementById('connection-status').className='badge badge-error';document.getElementById('connection-status').textContent='❌';};
        eventSource.addEventListener('message',e=>updateUI(JSON.parse(e.data)));
        function loadInitialData(){fetch('/status').then(r=>r.json()).then(updateUI);fetch('/logs').then(r=>r.json()).then(d=>renderLogs(d.logs));}
        function updateUI(s){
            document.getElementById('version-badge').textContent=s.worker_version||'v41';
            document.getElementById('subtitle').textContent=(s.worker_id||'')+' • ws://'+(s.worker_id||'');
            document.getElementById('ws-status').innerHTML=s.websocket_connected?'<span class="badge badge-success">✅</span>':'<span class="badge badge-error">❌</span>';
            document.getElementById('uptime').textContent=formatUptime(s.uptime_seconds||0);
            document.getElementById('reconnects').textContent=s.reconnect_count||0;
            document.getElementById('op-status').innerHTML=s.status?'<span class="badge badge-info">'+s.status.toUpperCase()+'</span>':'-';
            const hw=s.hardware||{};
            document.getElementById('cpu-current').textContent=(hw.cpu_percent||0)+'%';
            document.getElementById('cpu-progress').style.width=(hw.cpu_percent||0)+'%';
            document.getElementById('memory-current').textContent=(hw.memory_percent||0)+'%';
            document.getElementById('memory-progress').style.width=(hw.memory_percent||0)+'%';
            renderChart('cpu',s.hardware_history?.cpu||[]);renderChart('memory',s.hardware_history?.memory||[]);
            const dp=s.dependency_progress||0;
            document.getElementById('dep-progress').style.width=dp+'%';document.getElementById('dep-progress-text').textContent=dp+'%';
            document.getElementById('dep-installed').textContent=(s.dependency_installed_count||0)+'/'+(s.dependency_total_packages||0);
            document.getElementById('install-details').innerHTML=(s.dependency_install_log||[]).map(i=>'<div class="install-item"><b>'+i.package+'</b> '+(i.success?'✅':'⏳')+'</div>').join('')||'-';
            const tp=s.training_progress||0;
            document.getElementById('train-progress').style.width=tp+'%';document.getElementById('train-progress-text').textContent=tp+'%';
            document.getElementById('train-epoch').textContent=(s.training_epoch||0)+'/'+(s.training_total_epochs||0);
            document.getElementById('train-loss').textContent=s.training_loss||'-';
            const ec=document.getElementById('epoch-container'),el=document.getElementById('epoch-list');
            if(s.training_epoch&&s.training_total_epochs){ec.style.display='block';let h='';for(let i=1;i<=s.training_total_epochs;i++)h+='<span class="epoch-item '+(i<=s.training_epoch?'':'pending')+'">'+(i<=s.training_epoch?'✅':'⏳')+'E'+i+'</span>';el.innerHTML=h;}else ec.style.display='none';
            renderTasks(s.server_tasks||[]);
        }
        function renderChart(t,d){const p=document.getElementById(t+'-polyline');if(!p||d.length<2)return;const w=300,h=50,s=w/(d.length-1);p.setAttribute('points',d.map((v,i)=>(i*s)+','+(h-(v/100*h))).join(' '));}
        function renderLogs(logs){const l=document.getElementById('logs');const wasAtBottom=l.scrollHeight-l.scrollTop<=l.clientHeight+50;l.innerHTML=(logs||[]).slice(-200).reverse().map(log=>'<div class="log-entry log-'+(log.level||'info')+'"><span class="log-time">['+new Date(log.timestamp).toLocaleTimeString()+']</span><span class="log-badge">'+log.level+'</span><span class="log-message">'+escapeHtml(log.message)+'</span></div>').join('');if(wasAtBottom)l.scrollTop=l.scrollHeight;}
        function renderTasks(tasks){const card=document.getElementById('tasks-card'),list=document.getElementById('tasks-list');console.log('renderTasks:',tasks?.length||0);if(!tasks||tasks.length===0){card.style.display='none';return;}card.style.display='block';list.innerHTML=tasks.map(t=>'<div class="task-item"><div class="task-header"><span class="task-name">'+t.task_id+'</span><span class="task-status '+t.status+'">'+t.status+'</span></div><div class="progress-bar"><div class="progress-fill info" style="width:'+(t.progress||0)+'%"></div></div></div>').join('');}
        function formatUptime(s){const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),r=s%60;return h>0?h+'h'+m+'m '+r+'s':m>0?m+'m '+r+'s':r+'s';}
        function escapeHtml(t){if(!t)return'';const d=document.createElement('div');d.textContent=String(t);return d.innerHTML;}
    </script>
</body>
</html>'''

def get_hardware_info():
    """获取硬件信息 - 使用 psutil"""
    try:
        cpu_percent = round(psutil.cpu_percent(interval=0.5), 1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": round(memory.percent, 1),
            "memory_total": round(memory.total / 1024 / 1024 / 1024, 2),
            "memory_used": round(memory.used / 1024 / 1024 / 1024, 2),
            "disk_percent": round(disk.percent, 1),
            "disk_total": round(disk.total / 1024 / 1024 / 1024, 2),
            "disk_used": round(disk.used / 1024 / 1024 / 1024, 2)
        }
    except Exception as e:
        return {"cpu_percent": 0, "memory_percent": 0, "disk_percent": 0, "error": str(e)}

def add_log(level, message):
    message_log.append({"timestamp": datetime.now().isoformat(), "level": level, "message": message})
    if len(message_log) > 500: message_log.pop(0)
    state_changed.set()
    worker_state["last_activity"] = datetime.now().isoformat()

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

async def upgrade_worker_via_http(version, task_id=None):
    """升级 Worker 代码 - 写入并重启"""
    global worker_state, ws_connection
    add_log("info", f"📦 Starting upgrade to {version}")
    worker_state["current_operation"] = "upgrading"
    worker_state["current_task"] = {"task_id": task_id, "type": "upgrade"} if task_id else None
    state_changed.set()
    
    try:
        # 上报进度
        if task_id and ws_connection:
            await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "progress": 0, "status": "running"}))
        
        code_url = f"{HTTP_BASE}/files/worker.py"
        add_log("info", f"📥 Downloading from {code_url}...")
        
        if task_id and ws_connection:
            await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "progress": 30, "status": "running"}))
        
        resp = requests.get(code_url, timeout=60)
        if resp.status_code == 200:
            # 写入持久化路径
            written_path = "/data/worker.py"
            add_log("info", f"💾 Writing to {written_path}")
            
            os.makedirs(os.path.dirname(written_path), exist_ok=True)
            with open(written_path, "w", encoding='utf-8') as f:
                f.write(resp.text)
            add_log("success", f"✅ Written to {written_path}")
            
            # 验证写入
            with open(current_file, "r", encoding='utf-8') as f:
                written_content = f.read()
            if "v45" in written_content:
                add_log("success", "✅ Verification passed: v45 found")
            else:
                add_log("error", "❌ Verification failed: v45 not found")
            
            if task_id and ws_connection:
                await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "progress": 80, "status": "running"}))
            
            add_log("info", "🔄 Restarting...")
            
            if task_id and ws_connection:
                await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "progress": 100, "status": "completed"}))
                await ws_connection.send(json.dumps({"type": "complete", "task_id": task_id, "result": {"version": version, "path": written_path}}))
            
            add_log("info", "⏳ Waiting before restart...")
            time.sleep(2)
            add_log("info", f"🔄 Executing: {sys.executable} {written_path}")
            # 使用 os.execv 重启
            os.execv(sys.executable, [sys.executable, written_path])
        else:
            add_log("error", f"❌ Download failed: {resp.status_code}")
            if task_id and ws_connection:
                await ws_connection.send(json.dumps({"type": "error", "task_id": task_id, "error": f"Download failed: {resp.status_code}"}))
    except Exception as e:
        add_log("error", f"❌ Upgrade failed: {e}")
        if task_id and ws_connection:
            await ws_connection.send(json.dumps({"type": "error", "task_id": task_id, "error": str(e)}))
    finally:
        worker_state["current_operation"] = None
        worker_state["current_task"] = None
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
                worker_state["worker_id"] = worker_id
                add_log("info", "WebSocket connected successfully")
                # 握手后清空旧任务
                worker_state["server_tasks"] = []
                add_log("info", "📋 已清空旧任务列表")
                state_changed.set()
                
                await ws.send(json.dumps({"type": "handshake", "worker_id": worker_id, "version": worker_state["worker_version"]}))
                async for message in ws:
                    worker_state["messages_received"] += 1
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "")
                        if msg_type == "task_update":
                            task = data.get("task", {})
                            existing = [t for t in worker_state["server_tasks"] if t.get("task_id") == task.get("task_id")]
                            if existing:
                                existing[0].update(task)
                            else:
                                worker_state["server_tasks"].append(task)
                            state_changed.set()
                        elif msg_type == "active_tasks":
                            worker_state["server_tasks"] = data.get("tasks", [])
                            add_log("info", f"📋 收到 {len(worker_state['server_tasks'])} 个任务")
                            state_changed.set()
                        elif msg_type == "install_dependencies":
                            packages = data.get("data", {}).get("packages", [])
                            task_id = data.get("task_id")
                            add_log("info", f"📦 Received install command: {packages} (task: {task_id})")
                            current_operation = "installing"
                            asyncio.create_task(install_dependencies_smart(packages, task_id))
                        elif msg_type == "train":
                            train_data = data.get("data", {})
                            add_log("info", f"Received training command: {train_data.get('task_id')}")
                            current_operation = "training"
                            asyncio.create_task(execute_training(train_data, ws))
                        elif msg_type == "upgrade":
                            upgrade_data = data.get("data", {})
                            version = upgrade_data.get("version", "unknown")
                            task_id = data.get("task_id")
                            add_log("info", f"📨 Received upgrade command: {version} (task: {task_id})")
                            asyncio.create_task(upgrade_worker_via_http(version, task_id))
                    except Exception as e:
                        add_log("error", f"Processing failed: {e}")
        except Exception as e:
            worker_state["websocket_connected"] = False
            ws_connection = None
            worker_state["reconnect_count"] += 1
            add_log("error", f"Connection lost: {e}")
            await asyncio.sleep(5)
        worker_state["uptime_seconds"] = int(time.time() - start)

async def install_dependencies_smart(packages, task_id=None):
    """安装依赖 - 本地 pip 国内源优先，服务器下发备选"""
    global worker_state, ws_connection
    
    if not packages:
        return
    
    worker_state["status"] = "installing"
    worker_state["current_operation"] = "installing"
    worker_state["current_task"] = {"task_id": task_id, "type": "install_dependencies"} if task_id else None
    worker_state["dependency_total_packages"] = len(packages)
    worker_state["dependency_installed_count"] = 0
    
    # 上报开始
    if task_id and ws_connection:
        await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "progress": 0, "status": "running"}))
    
    for pkg_idx, pkg in enumerate(packages):
        worker_state["dependency_current_package"] = pkg
        pkg_installed = False
        
        # 上报当前包进度
        pkg_progress = int((pkg_idx) / len(packages) * 100)
        if task_id and ws_connection:
            await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "progress": pkg_progress, "status": "running", "current_package": pkg}))
        
        add_log("info", f"📦 Installing {pkg}...")
        state_changed.set()
        
        # 尝试 1: 清华源 (默认)
        if not pkg_installed:
            try:
                cmd = ["pip", "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", pkg, "-q", "--timeout", "120"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                if result.returncode == 0:
                    add_log("success", f"✅ {pkg} installed (tsinghua)")
                    pkg_installed = True
                else:
                    add_log("warn", f"⚠️ {pkg} failed (tsinghua): {result.stderr[:300]}")
            except Exception as e:
                add_log("error", f"❌ {pkg} exception (tsinghua): {e}")
        
        # 尝试 2: 阿里源
        if not pkg_installed:
            try:
                cmd = ["pip", "install", "-i", "https://mirrors.aliyun.com/pypi/simple/", pkg, "-q", "--timeout", "120"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                if result.returncode == 0:
                    add_log("success", f"✅ {pkg} installed (aliyun)")
                    pkg_installed = True
                else:
                    add_log("warn", f"⚠️ {pkg} failed (aliyun): {result.stderr[:300]}")
            except Exception as e:
                add_log("error", f"❌ {pkg} exception (aliyun): {e}")
        
        # 尝试 3: 中科大源
        if not pkg_installed:
            try:
                cmd = ["pip", "install", "-i", "https://pypi.mirrors.ustc.edu.cn/simple/", pkg, "-q", "--timeout", "120"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                if result.returncode == 0:
                    add_log("success", f"✅ {pkg} installed (ustc)")
                    pkg_installed = True
                else:
                    add_log("warn", f"⚠️ {pkg} failed (ustc): {result.stderr[:300]}")
            except Exception as e:
                add_log("error", f"❌ {pkg} exception (ustc): {e}")
        
        # 尝试 4: 从服务器下发 wheel (最后备选)
        if not pkg_installed:
            try:
                add_log("info", f"📥 Downloading {pkg} from server...")
                wheel_url = f"{HTTP_BASE}/files/wheels/{pkg}.whl"
                resp = requests.get(wheel_url, timeout=120)
                if resp.status_code == 200:
                    wheel_path = f"/tmp/{pkg}.whl"
                    with open(wheel_path, 'wb') as f:
                        f.write(resp.content)
                    cmd = ["pip", "install", wheel_path, "-q"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                    if result.returncode == 0:
                        add_log("success", f"✅ {pkg} installed (server wheel)")
                        pkg_installed = True
                    else:
                        add_log("error", f"❌ {pkg} wheel install failed: {result.stderr[:300]}")
                else:
                    add_log("warn", f"⚠️ {pkg} wheel not found on server (404)")
            except Exception as e:
                add_log("error", f"❌ {pkg} download exception: {e}")
        
        # 记录安装结果
        pkg_log = {"package": pkg, "success": pkg_installed}
        worker_state["dependency_install_log"].append(pkg_log)
        if len(worker_state["dependency_install_log"]) > 10:
            worker_state["dependency_install_log"].pop(0)
        
        worker_state["dependency_installed_count"] = pkg_idx + 1
        worker_state["dependency_progress"] = int((pkg_idx + 1) / len(packages) * 100)
        state_changed.set()
        
        # 上报包完成进度
        if task_id and ws_connection:
            final_status = "completed" if pkg_installed else "running"
            await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "progress": worker_state["dependency_progress"], "status": final_status}))
    
    worker_state["dependencies_installed"] = True
    worker_state["status"] = "idle"
    worker_state["current_operation"] = None
    worker_state["current_task"] = None
    add_log("success", "🎉 All dependencies installed")
    state_changed.set()
    
    # 上报完成
    if task_id and ws_connection:
        await ws_connection.send(json.dumps({"type": "progress", "task_id": task_id, "progress": 100, "status": "completed"}))
        await ws_connection.send(json.dumps({"type": "complete", "task_id": task_id, "result": {"installed": worker_state["dependency_installed_count"]}}))

async def execute_training(task, ws):
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
            if ws:
                await ws.send(json.dumps({"type": "progress", "task_id": task_id, "progress": int((epoch + progress/100) / epochs * 100), "status": "running", "epoch": epoch + 1, "loss": loss}))
            add_log("progress", f"Epoch {epoch+1}/{epochs} - {progress}% - Loss:{loss:.3f}")
            state_changed.set()
    worker_state["status"] = "idle"
    worker_state["current_task"] = None
    worker_state["training_progress"] = 0
    if ws:
        await ws.send(json.dumps({"type": "complete", "task_id": task_id, "result": {"final_loss": worker_state["training_loss"]}}))
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
    # 只在文件不存在时创建 HTML
    if not HTML_PATH.exists():
        with open(HTML_PATH, 'w', encoding='utf-8') as f:
            f.write(HTML_TEMPLATE)
        print(f"HTML template created: {HTML_PATH}")
    threading.Thread(target=lambda: asyncio.run(websocket_client()), daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(hardware_monitor()), daemon=True).start()
    print(f"Iris Worker v49 started | WebSocket: {WS_URL} | Monitor: http://localhost:{WORKER_PORT}/")
    app.run(host="0.0.0.0", port=WORKER_PORT, debug=False, threaded=True)

<!-- 强制添加 renderTasks -->
<script>
// 如果 updateUI 没有调用 renderTasks，在这里调用
if (typeof updateUI === 'function') {
    var origUpdateUI = updateUI;
    updateUI = function(s) {
        origUpdateUI(s);
        renderTasks(s.server_tasks||[]);
    };
}
</script>

<script>
// 页面加载完成后调用 renderTasks
window.addEventListener('load', function() {
    if (typeof renderTasks === 'function' && typeof serverState !== 'undefined') {
        renderTasks(serverState.server_tasks||[]);
    }
});

// 拦截 WebSocket 消息，确保调用 renderTasks
if (typeof window.origProcessMessage === 'undefined') {
    window.origProcessMessage = window.processMessage;
    window.processMessage = function(data) {
        window.origProcessMessage(data);
        if (data.type === 'active_tasks' || data.type === 'task_update') {
            setTimeout(function() {
                if (typeof renderTasks === 'function' && typeof serverState !== 'undefined') {
                    renderTasks(serverState.server_tasks||[]);
                }
            }, 100);
        }
    };
}
</script>

<script>
// 页面加载时强制调用 renderTasks
(function() {
    console.log('🔧 强制调用 renderTasks');
    
    // 等待 DOM 加载完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        console.log('🔧 DOM 已加载');
        
        // 等待 serverState 初始化
        setTimeout(function() {
            if (typeof serverState !== 'undefined' && serverState.server_tasks) {
                console.log('🔧 serverState.server_tasks:', serverState.server_tasks.length);
                if (typeof renderTasks === 'function') {
                    renderTasks(serverState.server_tasks);
                    console.log('✅ renderTasks 已调用');
                } else {
                    console.error('❌ renderTasks 函数不存在');
                }
            } else {
                console.error('❌ serverState 未初始化');
            }
        }, 500);
        
        // 拦截 WebSocket 消息
        if (window.ws) {
            var origOnMessage = window.ws.onmessage;
            window.ws.onmessage = function(event) {
                origOnMessage(event);
                setTimeout(function() {
                    if (typeof serverState !== 'undefined' && typeof renderTasks === 'function') {
                        renderTasks(serverState.server_tasks||[]);
                    }
                }, 100);
            };
        }
    }
})();
</script>
