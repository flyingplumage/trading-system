#!/usr/bin/env python3
"""
Iris Worker - 跨平台训练节点
支持：macOS / Ubuntu / Windows (WSL)

使用方法：
1. 一行命令部署：
   curl -sSL http://SERVER_IP:8888/deploy.sh | bash

2. 或直接运行：
   python3 worker.py
"""

import os
import json
import time
import hashlib
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

# 配置
WORKER_ID = f'iris-worker-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}'
# 请修改为您的服务器 IP，或通过环境变量 SERVER_IP 设置
SERVER_IP = os.environ.get('SERVER_IP', 'YOUR_SERVER_IP')
WORKER_PORT = int(os.environ.get('WORKER_PORT', '8080'))
TASK_QUEUE_URL = f'http://{SERVER_IP}:8888/api/train/queue'

# 目录
MODEL_DIR = Path('/tmp/iris_models')
LOG_DIR = Path('/tmp/iris_logs')
MODEL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 任务存储
tasks = {}

# Flask 应用
app = Flask(__name__)

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Iris Worker - {{ worker_id }}</title>
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #1a202c;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e2e8f0;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }
        .info-item {
            background: #f7fafc;
            padding: 12px;
            border-radius: 8px;
        }
        .info-label { color: #718096; font-size: 0.875rem; }
        .info-value { color: #1a202c; font-weight: 600; margin-top: 4px; }
        .task-card {
            background: #f7fafc;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            border-left: 4px solid #cbd5e0;
        }
        .task-card.status-queued { border-left-color: #f6ad55; }
        .task-card.status-training { border-left-color: #667eea; }
        .task-card.status-completed { border-left-color: #48bb78; }
        .task-card.status-failed { border-left-color: #f56565; }
        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .task-id {
            font-family: monospace;
            font-size: 1.1rem;
            color: #1a202c;
        }
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-badge.queued { background: #fef3c7; color: #92400e; }
        .status-badge.training { background: #dbeafe; color: #1e40af; }
        .status-badge.completed { background: #d1fae5; color: #065f46; }
        .status-badge.failed { background: #fee2e2; color: #991b1b; }
        .progress-bar {
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s;
        }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #a0aec0;
        }
        .footer {
            text-align: center;
            color: white;
            margin-top: 20px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Iris Worker</h1>
            <p>分布式训练节点 · 实时监控</p>
        </div>
        
        <div class="card">
            <h2>节点信息</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Worker ID</div>
                    <div class="info-value" style="font-family:monospace;">{{ worker_id }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">服务器</div>
                    <div class="info-value">{{ server_ip }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">运行时间</div>
                    <div class="info-value">{{ uptime }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">任务总数</div>
                    <div class="info-value">{{ tasks|length }}</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>训练任务</h2>
            {% if tasks %}
            {% for tid, t in tasks.items() %}
            <div class="task-card status-{{ t.status }}">
                <div class="task-header">
                    <span class="task-id">{{ tid }}</span>
                    <span class="status-badge {{ t.status }}">{{ t.status }}</span>
                </div>
                {% if t.get('started_at') %}
                <div style="font-size:0.875rem;color:#718096;">
                    开始：{{ t.started_at }}
                </div>
                {% endif %}
                {% if t.status == 'training' %}
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ t.get('progress', 0) }}%;"></div>
                </div>
                <div style="font-size:0.875rem;color:#718096;margin-top:4px;">
                    进度：{{ t.get('progress', 0) }}%
                </div>
                {% endif %}
                {% if t.get('completed_at') %}
                <div style="font-size:0.875rem;color:#718096;margin-top:8px;">
                    完成：{{ t.completed_at }}
                </div>
                {% endif %}
            </div>
            {% endfor %}
            {% else %}
            <div class="empty-state">
                <p style="font-size:3rem;margin-bottom:16px;">📭</p>
                <p>暂无训练任务</p>
                <p style="font-size:0.875rem;margin-top:8px;">任务将在这里显示</p>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>🔄 自动刷新：每 5 秒 | 服务器轮询：每 30 秒</p>
        </div>
    </div>
</body>
</html>
"""

# 轮询服务器任务
def poll_server():
    """定期从服务器拉取任务"""
    print(f"📡 开始轮询服务器：{TASK_QUEUE_URL}")
    while True:
        try:
            import requests
            resp = requests.get(TASK_QUEUE_URL, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                server_tasks = data.get('tasks', {})
                # 同步服务器任务到本地
                for tid, tdata in server_tasks.items():
                    if tid not in tasks:
                        print(f"✅ 拉取新任务：{tid}")
                        tasks[tid] = {
                            'status': 'queued',
                            'data': tdata.get('data', {}),
                            'progress': 0,
                            'from_server': True
                        }
                        threading.Thread(target=execute_training, args=(tid, tdata.get('data', {})), daemon=True).start()
            time.sleep(30)  # 每 30 秒轮询一次
        except Exception as e:
            print(f"⚠️ 轮询失败：{e}")
            time.sleep(30)

# 执行训练
def execute_training(tid, data):
    """执行训练任务"""
    try:
        tasks[tid]['status'] = 'training'
        tasks[tid]['started_at'] = datetime.now().isoformat()
        
        cfg = data.get('config', {})
        model_name = cfg.get('model_name', 'bert-base-chinese')
        dataset = data.get('dataset_path', '')
        epochs = cfg.get('epochs', 3)
        lora_r = cfg.get('lora_r', 32)
        batch_size = cfg.get('batch_size', 4)
        
        print(f"🎯 开始训练：{tid}")
        print(f"   模型：{model_name}")
        print(f"   数据集：{dataset}")
        print(f"   Epochs: {epochs}")
        
        # 训练命令
        cmd = [
            'python3', '-m', 'llama_factory.cli.train',
            '--stage', 'sft',
            '--do_train',
            '--model_name_or_path', model_name,
            '--dataset', dataset if dataset else 'alpaca_en_demo',
            '--template', 'qwen',
            '--finetuning_type', 'lora',
            '--lora_r', str(lora_r),
            '--lora_alpha', str(cfg.get('lora_alpha', lora_r * 2)),
            '--output_dir', str(MODEL_DIR / f'adapter_{tid}'),
            '--overwrite_cache',
            '--per_device_train_batch_size', str(batch_size),
            '--gradient_accumulation_steps', '4',
            '--lr_scheduler_type', 'cosine',
            '--logging_steps', '10',
            '--warmup_steps', '20',
            '--save_steps', '100',
            '--learning_rate', str(cfg.get('learning_rate', '2e-4')),
            '--num_train_epochs', str(epochs),
            '--plot_loss',
            '--fp16'
        ]
        
        log_file = LOG_DIR / f'{tid}.log'
        with open(log_file, 'w') as f:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                f.write(line)
                # 解析进度
                if 'Epoch' in line or 'Loss' in line or 'steps' in line:
                    tasks[tid]['progress'] = min(95, tasks[tid].get('progress', 0) + 2)
            process.wait()
        
        if process.returncode == 0:
            tasks[tid]['status'] = 'completed'
            tasks[tid]['progress'] = 100
            print(f"✅ 训练完成：{tid}")
        else:
            tasks[tid]['status'] = 'failed'
            tasks[tid]['error'] = f'Exit code: {process.returncode}'
            print(f"❌ 训练失败：{tid}")
        
        tasks[tid]['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        tasks[tid]['status'] = 'failed'
        tasks[tid]['error'] = str(e)
        tasks[tid]['completed_at'] = datetime.now().isoformat()
        print(f"❌ 训练异常：{tid} - {e}")

# 路由
@app.route('/')
def index():
    """监控面板"""
    uptime = str(datetime.now() - datetime.fromtimestamp(time.time() - time.process_time())).split('.')[0]
    return render_template_string(
        HTML_TEMPLATE,
        worker_id=WORKER_ID,
        server_ip=SERVER_IP,
        uptime=uptime,
        tasks=tasks
    )

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'worker_id': WORKER_ID,
        'server': SERVER_IP,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/train/submit', methods=['POST'])
def submit_task():
    """提交训练任务"""
    data = request.json
    tid = data.get('task_id')
    if not tid:
        return jsonify({'error': 'no task_id'}), 400
    
    tasks[tid] = {'status': 'queued', 'data': data, 'progress': 0}
    threading.Thread(target=execute_training, args=(tid, data), daemon=True).start()
    
    return jsonify({'status': 'accepted', 'task_id': tid})

@app.route('/api/train/queue')
def task_queue():
    """任务队列"""
    return jsonify({'total': len(tasks), 'tasks': tasks})

@app.route('/api/train/status/<tid>')
def task_status(tid):
    """任务状态"""
    return jsonify(tasks.get(tid, {'status': 'not_found'}))

# 主函数
if __name__ == '__main__':
    print("="*60)
    print("🚀 Iris Worker 启动")
    print("="*60)
    print(f"Worker ID: {WORKER_ID}")
    print(f"服务器：{SERVER_IP}")
    print(f"轮询 URL: {TASK_QUEUE_URL}")
    print(f"端口：{WORKER_PORT}")
    print("="*60)
    
    # 启动轮询线程
    poll_thread = threading.Thread(target=poll_server, daemon=True)
    poll_thread.start()
    
    # 启动 Flask
    app.run(host='0.0.0.0', port=WORKER_PORT, debug=False)
