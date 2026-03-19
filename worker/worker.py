# -*- coding: utf-8 -*-
"""Iris Worker v29 - WebSocket 信令 + HTTP 文件传输"""
from __future__ import unicode_literals
import os, json, time, threading, subprocess, socket, asyncio, websockets, requests, shutil, platform, psutil
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
    "worker_version": "v29",
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

# HTML 模板（简化版）
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>Iris Worker v29</title><meta http-equiv="refresh" content="2">
<style>:root{--bg:#0f172a;--card:#1e293b;--text:#f1f5f9;--primary:#667eea;--success:#10b981;--warning:#f59e0b;--error:#ef4444}*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);padding:20px}.container{max-width:2000px;margin:0 auto}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding-bottom:15px;border-bottom:1px solid var(--card)}h1{font-size:24px;background:linear-gradient(135deg,var(--primary),#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.subtitle{font-size:12px;color:#94a3b8}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:15px;margin-bottom:20px}.card{background:var(--card);border-radius:12px;padding:20px;border:1px solid rgba(255,255,255,0.05)}.card h2{font-size:14px;color:#94a3b8;margin-bottom:15px;text-transform:uppercase}.stat-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.03)}.stat-row:last-child{border-bottom:none}.stat-label{color:#94a3b8}.stat-value{font-weight:600}.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600}.badge-success{background:rgba(16,185,129,0.2);color:#10b981}.badge-warning{background:rgba(245,158,11,0.2);color:#f59e0b}.badge-error{background:rgba(239,68,68,0.2);color:#ef4444}.badge-info{background:rgba(102,126,234,0.2);color:#667eea}.progress-bar{height:8px;background:rgba(255,255,255,0.1);border-radius:4px;overflow:hidden;margin:10px 0}.progress-fill{height:100%;background:linear-gradient(90deg,var(--primary),#764ba2)}.progress-fill.success{background:linear-gradient(90deg,#10b981,#059669)}.progress-fill.warning{background:linear-gradient(90deg,#f59e0b,#d97706)}.progress-fill.info{background:linear-gradient(90deg,#667eea,#764ba2)}.hw-chart{height:100px;margin-top:10px}.hw-line polyline{fill:none;stroke-width:2}.hw-line.cpu polyline{stroke:#3b82f6}.hw-line.memory polyline{stroke:#8b5cf6}.hw-line.disk polyline{stroke:#ec4899}.hw-current{text-align:center;margin-bottom:8px;font-size:20px;font-weight:600}.hw-label{text-align:center;font-size:11px;color:#94a3b8}.logs-container{max-height:500px;overflow-y:auto;font-family:monospace;font-size:11px;background:rgba(0,0,0,0.3);border-radius:10px;padding:15px}.log-entry{padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.03);display:flex;gap:10px}.log-time{color:#64748b;font-size:10px}.log-badge{min-width:60px;text-align:center;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:600}.log-info{color:#667eea}.log-info .log-badge{background:rgba(102,126,234,0.2)}.log-success{color:#10b981}.log-success .log-badge{background:rgba(16,185,129,0.2)}.log-progress{color:#f59e0b}.log-progress .log-badge{background:rgba(245,158,11,0.2)}.log-error{color:#ef4444}.log-error .log-badge{background:rgba(239,68,68,0.2)}.log-message{flex:1;word-break:break-word}.install-list{max-height:300px;overflow-y:auto}.install-item{background:rgba(0,0,0,0.2);padding:10px;border-radius:8px;margin-bottom:8px}.epoch-list{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}.epoch-item{background:rgba(16,185,129,0.2);color:#10b981;padding:4px 12px;border-radius:12px}.epoch-item.pending{background:rgba(148,163,184,0.2);color:#94a3b8}.task-item{background:rgba(0,0,0,0.2);padding:12px;border-radius:8px;margin-bottom:10px}.task-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}.task-name{font-weight:600}.task-status{font-size:11px;padding:2px 8px;border-radius:8px}.task-status.running{background:rgba(245,158,11,0.2);color:#f59e0b}.task-status.completed{background:rgba(16,185,129,0.2);color:#10b981}.task-status.pending{background:rgba(102,126,234,0.2);color:#667eea}::-webkit-scrollbar{width:8px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--card);border-radius:4px}</style>
</head>
<body><div class="container"><header><div><h1>🚀 Iris Worker <span id="version-badge" class="badge badge-info">v29</span></h1><div class="subtitle" id="subtitle">Loading...</div></div><div><span id="connection-status" class="badge badge-warning">⏳ 连接中...</span></div></header><div class="grid"><div class="card"><h2>📊 连接状态</h2><div class="stat-row"><span class="stat-label">WebSocket</span><span id="ws-status" class="badge">-</span></div><div class="stat-row"><span class="stat-label">运行时间</span><span id="uptime">0s</span></div><div class="stat-row"><span class="stat-label">重连次数</span><span id="reconnects">0</span></div><div class="stat-row"><span class="stat-label">接收消息</span><span id="msg-recv">0</span></div><div class="stat-row"><span class="stat-label">发送消息</span><span id="msg-sent">0</span></div></div><div class="card"><h2>📈 运行状态</h2><div class="stat-row"><span class="stat-label">当前状态</span><span id="op-status" class="badge">-</span></div><div class="stat-row"><span class="stat-label">当前操作</span><span id="operation">-</span></div><div class="stat-row"><span class="stat-label">当前任务</span><span id="current-task">-</span></div><div class="stat-row"><span class="stat-label">最后活动</span><span id="last-activity">-</span></div></div><div class="card"><h2>💻 CPU</h2><div class="hw-current" id="cpu-current">0%</div><div class="progress-bar"><div class="progress-fill" id="cpu-progress" style="width:0%"></div></div><div class="hw-chart cpu"><svg viewBox="0 0 300 100"><polyline id="cpu-polyline" points=""></polyline></svg></div><div class="hw-label">最近 60 秒趋势</div></div><div class="card"><h2>🧠 内存</h2><div class="hw-current" id="memory-current">0%</div><div class="progress-bar"><div class="progress-fill" id="memory-progress" style="width:0%"></div></div><div class="hw-chart memory"><svg viewBox="0 0 300 100"><polyline id="memory-polyline" points=""></polyline></svg></div><div class="hw-label">最近 60 秒趋势</div></div><div class="card"><h2>💾 磁盘</h2><div class="hw-current" id="disk-current">0%</div><div class="progress-bar"><div class="progress-fill" id="disk-progress" style="width:0%"></div></div><div class="hw-chart disk"><svg viewBox="0 0 300 100"><polyline id="disk-polyline" points=""></polyline></svg></div><div class="hw-label">使用率</div></div><div class="card"><h2>🖥️ 系统信息</h2><div class="stat-row"><span class="stat-label">主机名</span><span id="sys-hostname" class="stat-value">-</span></div><div class="stat-row"><span class="stat-label">Python</span><span id="sys-python" class="stat-value">-</span></div><div class="stat-row"><span class="stat-label">平台</span><span id="sys-platform" class="stat-value">-</span></div><div class="stat-row"><span class="stat-label">CPU 核心</span><span id="sys-cpu" class="stat-value">-</span></div><div class="stat-row"><span class="stat-label">内存总量</span><span id="sys-memory" class="stat-value">-</span></div></div></div><div class="grid" style="grid-template-columns:2fr 1fr;"><div class="card" style="grid-column:span 2;"><h2>📝 实时日志 (最近 200 条)</h2><div class="logs-container" id="logs">加载中...</div></div><div style="display:flex;flex-direction:column;gap:15px;"><div class="card"><h2>📦 依赖安装</h2><div class="stat-row"><span class="stat-label">进度</span><span id="dep-progress-text" class="stat-value">0%</span></div><div class="progress-bar"><div class="progress-fill warning" id="dep-progress" style="width:0%"></div></div><div class="stat-row"><span class="stat-label">已安装</span><span id="dep-installed" class="stat-value">0/0</span></div><div class="stat-row"><span class="stat-label">当前源</span><span id="dep-source" class="stat-value">-</span></div><div class="install-list" id="install-details" style="margin-top:10px;">暂无数据</div></div><div class="card"><h2>🧠 训练进度</h2><div class="stat-row"><span class="stat-label">进度</span><span id="train-progress-text" class="stat-value">0%</span></div><div class="progress-bar"><div class="progress-fill success" id="train-progress" style="width:0%"></div></div><div class="stat-row"><span class="stat-label">Epoch</span><span id="train-epoch" class="stat-value">0/0</span></div><div class="stat-row"><span class="stat-label">Loss</span><span id="train-loss" class="stat-value">-</span></div><div id="epoch-container" style="margin-top:10px;display:none;"><div class="hw-label" style="margin-bottom:8px;">Epoch 进度</div><div class="epoch-list" id="epoch-list"></div></div></div></div></div><div class="card" id="tasks-card" style="margin-top:20px;display:none;"><h2>📋 活动任务（服务端监控）</h2><div id="tasks-list">暂无活动任务</div></div></div>
<script>const eventSource=new EventSource('/stream');eventSource.onopen=()=>{document.getElementById('connection-status').className='badge badge-success';document.getElementById('connection-status').textContent='✅ 已连接';loadInitialData();};eventSource.onerror=()=>{document.getElementById('connection-status').className='badge badge-error';document.getElementById('connection-status').textContent='❌ 断开';};eventSource.addEventListener('message',e=>updateUI(JSON.parse(e.data)));function loadInitialData(){fetch('/status').then(r=>r.json()).then(updateUI);fetch('/logs').then(r=>r.json()).then(d=>renderLogs(d.logs));}function updateUI(s){document.getElementById('version-badge').textContent=s.worker_version||'v29';document.getElementById('subtitle').textContent=(s.worker_id||'')+' • ws://'+(s.worker_id||'');document.getElementById('ws-status').innerHTML=s.websocket_connected?'<span class="badge badge-success">✅ 已连接</span>':'<span class="badge badge-error">❌ 未连接</span>';document.getElementById('uptime').textContent=formatUptime(s.uptime_seconds||0);document.getElementById('reconnects').textContent=s.reconnect_count||0;document.getElementById('msg-recv').textContent=s.messages_received||0;document.getElementById('msg-sent').textContent=s.messages_sent||0;document.getElementById('op-status').innerHTML=s.status?'<span class="badge badge-info">'+s.status.toUpperCase()+'</span>':'-';document.getElementById('operation').textContent=s.current_operation||'-';document.getElementById('current-task').textContent=s.current_task?(s.current_task.task_id||'有任务'):'-';document.getElementById('last-activity').textContent=s.last_activity?new Date(s.last_activity).toLocaleString():'-';const hw=s.hardware||{};document.getElementById('cpu-current').textContent=(hw.cpu_percent||0)+'%';document.getElementById('cpu-progress').style.width=(hw.cpu_percent||0)+'%';document.getElementById('memory-current').textContent=(hw.memory_percent||0)+'%';document.getElementById('memory-progress').style.width=(hw.memory_percent||0)+'%';document.getElementById('disk-current').textContent=(hw.disk_percent||0)+'%';document.getElementById('disk-progress').style.width=(hw.disk_percent||0)+'%';renderChart('cpu',s.hardware_history?.cpu||[]);renderChart('memory',s.hardware_history?.memory||[]);renderChart('disk',s.hardware_history?.disk||[]);const sys=s.system_info||{};document.getElementById('sys-hostname').textContent=sys.hostname||'-';document.getElementById('sys-python').textContent=sys.python_version||'-';document.getElementById('sys-platform').textContent=sys.platform||'-';document.getElementById('sys-cpu').textContent=sys.cpu_count?sys.cpu_count+' 核心':'-';document.getElementById('sys-memory').textContent=sys.memory_total?sys.memory_total+' GB':'-';const dp=s.dependency_progress||0;document.getElementById('dep-progress').style.width=dp+'%';document.getElementById('dep-progress-text').textContent=dp+'%';document.getElementById('dep-installed').textContent=(s.dependency_installed_count||0)+'/'+(s.dependency_total_packages||0);document.getElementById('dep-source').textContent=s.dependency_source||'-';document.getElementById('install-details').innerHTML=(s.dependency_install_log||[]).map(i=>'<div class="install-item"><div class="install-header"><span>'+i.package+'</span><span class="badge '+(i.success?'badge-success':'badge-warning')+'">'+(i.success?'✅ 成功':'⏳ 等待')+'</span></div><div style="color:#64748b;font-size:11px;">'+(i.source||'等待中...')+'</div></div>').join('')||'暂无数据';const tp=s.training_progress||0;document.getElementById('train-progress').style.width=tp+'%';document.getElementById('train-progress-text').textContent=tp+'%';document.getElementById('train-epoch').textContent=(s.training_epoch||0)+'/'+(s.training_total_epochs||0);document.getElementById('train-loss').textContent=s.training_loss||'-';const ec=document.getElementById('epoch-container'),el=document.getElementById('epoch-list');if(s.training_epoch&&s.training_total_epochs){ec.style.display='block';let h='';for(let i=1;i<=s.training_total_epochs;i++)h+='<span class="epoch-item '+(i<=s.training_epoch?'':'pending')+'">'+(i<=s.training_epoch?'✅':'⏳')+' E'+i+'</span>';el.innerHTML=h;}else ec.style.display='none';renderTasks(s.server_tasks||[]);}function renderChart(t,d){const p=document.getElementById(t+'-polyline');if(!p||d.length<2)return;const w=300,h=100,s=w/(d.length-1);p.setAttribute('points',d.map((v,i)=>(i*s)+','+(h-(v/100*h))).join(' '));}function renderLogs(logs){const l=document.getElementById('logs');l.innerHTML=(logs||[]).slice(-200).reverse().map(log=>'<div class="log-entry log-'+(log.level||'info')+'"><span class="log-time">['+new Date(log.timestamp).toLocaleTimeString()+']</span><span class="log-badge">'+log.level+'</span><span class="log-message">'+escapeHtml(log.message)+'</span></div>').join('');l.scrollTop=l.scrollHeight;}function renderTasks(tasks){const card=document.getElementById('tasks-card'),list=document.getElementById('tasks-list');if(!tasks||tasks.length===0){card.style.display='none';return;}card.style.display='block';let html='';for(const task of tasks){const status=task.status||'pending',prog=task.progress||0;html+='<div class="task-item"><div class="task-header"><span class="task-name">'+task.task_id+'</span><span class="task-status '+status+'">'+status+'</span></div><div class="progress-bar"><div class="progress-fill info" style="width:'+prog+'%"></div></div><div style="font-size:11px;color:#94a3b8;margin-top:5px;">'+prog+'% 完成 - '+task.task_type+'</div></div>';}list.innerHTML=html||'暂无活动任务';}function formatUptime(s){const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),r=s%60;return h>0?h+'h '+m+'m '+r+'s':m>0?m+'m '+r+'s':r+'s';}function escapeHtml(t){if(!t)return'';const d=document.createElement('div');d.textContent=String(t);return d.innerHTML;}</script>
</body></html>'''

def get_hardware_info():
    return {"cpu_percent": round(psutil.cpu_percent(interval=0.1), 1), "memory_percent": round(psutil.virtual_memory().percent, 1), "disk_percent": round(psutil.disk_usage('/').percent, 1)}

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

async def upgrade_worker_via_http(version):
    """通过 HTTP 下载代码进行升级"""
    add_log("info", f"Starting upgrade to {version} via HTTP")
    try:
        # 通过 HTTP 下载代码
        code_url = f"{HTTP_BASE}/files/worker.py"
        add_log("info", f"Downloading from {code_url}...")
        state_changed.set()
        
        resp = requests.get(code_url, timeout=60)
        if resp.status_code == 200:
            # 备份旧版本
            if os.path.exists("/app/worker.py"):
                shutil.copy("/app/worker.py", "/app/worker.py.bak")
                add_log("info", "Backed up old version")
            
            # 写入新版本
            with open("/app/worker.py", "w", encoding='utf-8') as f:
                f.write(resp.text)
            add_log("success", f"Downloaded {version} successfully")
            state_changed.set()
            
            add_log("info", "Restarting...")
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
                worker_state["worker_id"] = worker_id
                add_log("info", "WebSocket connected successfully")
                
                # 发送握手
                await ws.send(json.dumps({"type": "handshake", "worker_id": worker_id, "version": worker_state["worker_version"]}))
                
                async for message in ws:
                    worker_state["messages_received"] += 1
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "")
                        
                        # 服务端推送的任务更新
                        if msg_type == "task_update":
                            task = data.get("task", {})
                            existing = [t for t in worker_state["server_tasks"] if t.get("task_id") == task.get("task_id")]
                            if existing:
                                existing[0].update(task)
                            else:
                                worker_state["server_tasks"].append(task)
                            state_changed.set()
                            add_log("info", f"Task update: {task.get('task_id')} - {task.get('progress')}%")
                        
                        # 活动任务列表
                        elif msg_type == "active_tasks":
                            worker_state["server_tasks"] = data.get("tasks", [])
                            state_changed.set()
                        
                        # 指令处理
                        elif msg_type == "install_dependencies":
                            packages = data.get("data", {}).get("packages", [])
                            add_log("info", f"Received command: install {packages}")
                            current_operation = "installing"
                            asyncio.create_task(install_dependencies_smart(packages))
                        elif msg_type == "train":
                            train_data = data.get("data", {})
                            add_log("info", f"Received training command: {train_data.get('task_id')}")
                            current_operation = "training"
                            asyncio.create_task(execute_training(train_data, ws))
                        elif msg_type == "upgrade":
                            upgrade_data = data.get("data", {})
                            version = upgrade_data.get("version", "unknown")
                            # ✅ 通过 HTTP 下载代码！
                            add_log("info", f"Received upgrade command: {version}")
                            asyncio.create_task(upgrade_worker_via_http(version))
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
            
            # 上报进度给服务端（通过 WebSocket 信令）
            if ws:
                await ws.send(json.dumps({
                    "type": "progress",
                    "task_id": task_id,
                    "progress": int((epoch + progress/100) / epochs * 100),
                    "status": "running",
                    "epoch": epoch + 1,
                    "loss": loss
                }))
            
            add_log("progress", f"Epoch {epoch+1}/{epochs} - {progress}% - Loss:{loss:.3f}")
            state_changed.set()
    
    worker_state["status"] = "idle"
    worker_state["current_task"] = None
    worker_state["training_progress"] = 0
    
    # 上报完成给服务端
    if ws:
        await ws.send(json.dumps({
            "type": "complete",
            "task_id": task_id,
            "result": {"final_loss": worker_state["training_loss"]}
        }))
    
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
    threading.Thread(target=lambda: asyncio.run(hardware_monitor()), daemon=True).start()
    print(f"Iris Worker v29 started\nWebSocket: {WS_URL}\nHTTP Files: {HTTP_BASE}/files/\nMonitor: http://localhost:{WORKER_PORT}/")
    app.run(host="0.0.0.0", port=WORKER_PORT, debug=False, threaded=True)
