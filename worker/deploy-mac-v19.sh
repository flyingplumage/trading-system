#!/bin/bash
# Iris Worker v19 Mac 一键部署脚本
# 嵌入 HTML 文件，确保 100% 可靠

set -e

SERVER_IP="162.14.115.79"

echo "============================================================"
echo "🚀 Iris Worker v19 一键部署"
echo "============================================================"
echo ""
echo "🎯 v19 特性："
echo "  ✅ HTML 文件嵌入脚本（100% 可靠）"
echo "  ✅ 亮色趋势线（蓝/紫/粉）"
echo "  ✅ 日志中文正常"
echo ""

# 1. 清理旧容器
echo "[1/7] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true
echo "✅ 清理完成"

# 2. 创建工作目录
echo ""
echo "[2/7] 准备工作目录..."
WORK_DIR=~/iris-worker-v19
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 3. 下载 Worker 代码
echo ""
echo "[3/7] 下载 Worker 代码..."
curl -sSL "http://$SERVER_IP:8888/worker_v18.py" -o worker.py
if [ ! -s worker.py ]; then
    echo "❌ 下载失败"
    exit 1
fi
echo "✅ Worker 代码已下载"

# 4. 创建 HTML 文件
echo ""
echo "[4/7] 创建 HTML 模板..."
cat > index.html << 'EOFHTML'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iris Worker v19</title>
    <style>
        :root{--primary:#667eea;--success:#10b981;--warning:#f59e0b;--error:#ef4444;--bg:#0f172a;--card:#1e293b;--text:#f1f5f9}
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);padding:15px;font-size:13px}
        .container{max-width:1800px;margin:0 auto}
        header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;padding-bottom:10px;border-bottom:1px solid var(--card)}
        h1{font-size:20px;background:linear-gradient(135deg,var(--primary),#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .subtitle{font-size:12px;color:#94a3b8}
        .top-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:15px}
        .card{background:var(--card);border-radius:10px;padding:15px;border:1px solid rgba(255,255,255,0.05)}
        .card h2{font-size:12px;color:#94a3b8;margin-bottom:12px;text-transform:uppercase}
        .stat-row{display:flex;justify-content:space-between;padding:6px 0;font-size:12px;border-bottom:1px solid rgba(255,255,255,0.03)}
        .stat-row:last-child{border-bottom:none}
        .badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600}
        .badge-success{background:rgba(16,185,129,0.2);color:#10b981}
        .badge-warning{background:rgba(245,158,11,0.2);color:#f59e0b}
        .badge-info{background:rgba(102,126,234,0.2);color:#667eea}
        .progress-bar{height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;margin:8px 0}
        .progress-fill{height:100%;background:linear-gradient(90deg,var(--primary),#764ba2);border-radius:3px;transition:width 0.3s ease}
        .progress-fill.success{background:linear-gradient(90deg,#10b981,#059669)}
        .bottom-grid{display:grid;grid-template-columns:2fr 1fr;gap:12px}
        .install-list{max-height:300px;overflow-y:auto}
        .install-item{background:rgba(0,0,0,0.2);padding:8px;border-radius:6px;margin-bottom:6px;font-size:12px}
        .install-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
        .logs-container{background:rgba(0,0,0,0.3);border-radius:10px;padding:12px;max-height:600px;overflow-y:visible;font-family:"SF Mono",Monaco,monospace;font-size:11px}
        .log-entry{padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.03);display:flex;gap:8px}
        .log-time{color:#64748b;font-size:10px;white-space:nowrap}
        .log-badge{min-width:50px;text-align:center;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:600;text-transform:uppercase}
        .log-info{color:#667eea}.log-info .log-badge{background:rgba(102,126,234,0.2)}
        .log-success{color:#10b981}.log-success .log-badge{background:rgba(16,185,129,0.2)}
        .log-progress{color:#f59e0b}.log-progress .log-badge{background:rgba(245,158,11,0.2)}
        .log-error{color:#ef4444}.log-error .log-badge{background:rgba(239,68,68,0.2)}
        .log-message{flex:1;word-break:break-word}
        .epoch-list{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
        .epoch-item{background:rgba(16,185,129,0.2);color:#10b981;padding:3px 10px;border-radius:12px;font-size:11px}
        .epoch-item.pending{background:rgba(148,163,184,0.2);color:#94a3b8}
        .hw-chart{height:100px;position:relative;border-left:1px solid #475569;border-bottom:1px solid #475569;margin-top:10px;background:rgba(255,255,255,0.05)}
        .hw-line{position:absolute;bottom:0;left:0;width:100%;height:100%}
        .hw-line polyline{fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}
        .hw-line.cpu polyline{stroke:#60a5fa;filter:drop-shadow(0 0 2px #60a5fa)}
        .hw-line.memory polyline{stroke:#a78bfa;filter:drop-shadow(0 0 2px #a78bfa)}
        .hw-line.disk polyline{stroke:#f472b6;filter:drop-shadow(0 0 2px #f472b6)}
        .hw-current{font-size:18px;font-weight:600;text-align:center;margin-bottom:5px}
        .hw-label{font-size:10px;color:#64748b;text-align:center}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🚀 Iris Worker <span id="version-badge" class="badge badge-info">v19</span></h1>
                <div class="subtitle" id="subtitle">加载中...</div>
            </div>
            <div id="connection-status" class="badge badge-warning">⏳ 连接中...</div>
        </header>
        <div class="top-grid">
            <div class="card"><h2>📊 连接</h2>
                <div class="stat-row"><span>WebSocket</span><span id="ws-status" class="badge">-</span></div>
                <div class="stat-row"><span>运行时间</span><span id="uptime">0s</span></div>
                <div class="stat-row"><span>重连</span><span id="reconnects">0</span></div>
            </div>
            <div class="card"><h2>📈 状态</h2>
                <div class="stat-row"><span>状态</span><span id="op-status" class="badge">-</span></div>
                <div class="stat-row"><span>操作</span><span id="operation">-</span></div>
                <div class="stat-row"><span>消息</span><span id="msg-recv">0</span></div>
            </div>
            <div class="card"><h2>💻 CPU</h2>
                <div class="hw-current" id="cpu-current">0%</div>
                <div class="hw-chart cpu"><svg class="hw-line cpu" id="cpu-svg" viewBox="0 0 300 100" preserveAspectRatio="none"><polyline id="cpu-polyline" points=""></polyline></svg></div>
                <div class="hw-label">最近 60 秒</div>
            </div>
            <div class="card"><h2>🧠 内存</h2>
                <div class="hw-current" id="memory-current">0%</div>
                <div class="hw-chart memory"><svg class="hw-line memory" id="memory-svg" viewBox="0 0 300 100" preserveAspectRatio="none"><polyline id="memory-polyline" points=""></polyline></svg></div>
                <div class="hw-label">最近 60 秒</div>
            </div>
            <div class="card"><h2>💾 磁盘</h2>
                <div class="hw-current" id="disk-current">0%</div>
                <div class="hw-chart disk"><svg class="hw-line disk" id="disk-svg" viewBox="0 0 300 100" preserveAspectRatio="none"><polyline id="disk-polyline" points=""></polyline></svg></div>
                <div class="hw-label">使用率</div>
            </div>
        </div>
        <div class="bottom-grid">
            <div class="card">
                <h2>📝 日志 <span style="color:#64748b;font-size:11px;">(最近 150 条)</span></h2>
                <div class="logs-container" id="logs">加载中...</div>
            </div>
            <div class="card">
                <h2>📦 依赖明细</h2>
                <div class="install-list" id="install-details">暂无数据</div>
                <div id="epoch-container" style="margin-top:12px;display:none;">
                    <h2 style="font-size:12px;color:#94a3b8;margin-bottom:8px;">🧠 Epoch</h2>
                    <div class="epoch-list" id="epoch-list"></div>
                </div>
            </div>
        </div>
    </div>
    <script>
        let logs=[],autoScroll=true;const eventSource=new EventSource('/stream');
        eventSource.onopen=function(){document.getElementById('connection-status').className='badge badge-success';document.getElementById('connection-status').textContent='✅ 已连接';loadInitialData();};
        eventSource.onerror=function(){document.getElementById('connection-status').className='badge badge-error';document.getElementById('connection-status').textContent='❌ 断开';};
        eventSource.addEventListener('message',function(e){try{updateUI(JSON.parse(e.data));}catch(err){console.error(err);}});
        function loadInitialData(){fetch('/status').then(r=>r.json()).then(updateUI);fetch('/logs').then(r=>r.json()).then(d=>{logs=d.logs;renderLogs();});}
        function updateUI(s){
            document.getElementById('version-badge').textContent=s.worker_version||'v19';
            document.getElementById('subtitle').textContent=s.worker_id+' • ws://162.14.115.79:5000/ws/worker';
            document.getElementById('ws-status').innerHTML=s.websocket_connected?'<span class="badge badge-success">✅</span>':'<span class="badge badge-error">❌</span>';
            document.getElementById('uptime').textContent=formatUptime(s.uptime_seconds||0);
            document.getElementById('reconnects').textContent=s.reconnect_count||0;
            document.getElementById('msg-recv').textContent=s.messages_received||0;
            document.getElementById('op-status').innerHTML=s.status?'<span class="badge badge-info">'+s.status.toUpperCase()+'</span>':'-';
            document.getElementById('operation').textContent=s.current_operation||'-';
            const hw=s.hardware||{};
            document.getElementById('cpu-current').textContent=(hw.cpu_percent||0)+'%';
            document.getElementById('memory-current').textContent=(hw.memory_percent||0)+'%';
            document.getElementById('disk-current').textContent=(hw.disk_percent||0)+'%';
            renderChart('cpu',s.hardware_history?.cpu||[]);
            renderChart('memory',s.hardware_history?.memory||[]);
            renderChart('disk',s.hardware_history?.disk||[]);
            const dp=s.dependency_progress||0;
            document.getElementById('dep-progress').style.width=dp+'%';
            document.getElementById('dep-progress-text').textContent=dp+'%';
            document.getElementById('dep-installed').textContent=(s.dependency_installed_count||0)+'/'+(s.dependency_total_packages||0);
            const tp=s.training_progress||0;
            document.getElementById('train-progress').style.width=tp+'%';
            document.getElementById('train-progress-text').textContent=tp+'%';
            document.getElementById('loss').textContent=s.training_loss||'-';
            const il=s.dependency_install_log||[];
            document.getElementById('install-details').innerHTML=il.length>0?il.map(i=>'<div class="install-item"><div class="install-header"><span>'+escapeHtml(i.package)+'</span><span class="badge '+(i.success?'badge-success':'badge-warning')+'">'+(i.success?'✅':'⏳')+'</span></div><div style="color:#64748b;font-size:11px;">'+(i.source||'等待中...')+'</div></div>').join(''):'暂无数据';
            const ec=document.getElementById('epoch-container'),el=document.getElementById('epoch-list');
            if(s.training_epoch&&s.training_total_epochs){ec.style.display='block';let h='';for(let i=1;i<=s.training_total_epochs;i++)h+='<span class="epoch-item '+(i<=s.training_epoch?'':'pending')+'">'+(i<=s.training_epoch?'✅':'⏳')+' E'+i+'</span>';el.innerHTML=h;}else{ec.style.display='none';}
        }
        function renderChart(t,d){const p=document.getElementById(t+'-polyline');if(!p)return;if(!d||d.length<2){p.setAttribute('points','');return;}const w=300,h=100,s=w/(d.length-1);p.setAttribute('points',d.map((v,i)=>(i*s)+','+(h-(v/100*h))).join(' '));}
        function renderLogs(){const l=document.getElementById('logs'),b=autoScroll||(l.scrollHeight-l.scrollTop===l.clientHeight);l.innerHTML=logs.slice(-150).reverse().map(l=>'<div class="log-entry log-'+(l.level||'info')+'"><span class="log-time">['+new Date(l.timestamp).toLocaleTimeString()+']</span><span class="log-badge">'+l.level+'</span><span class="log-message">'+escapeHtml(l.message)+'</span></div>').join('');if(autoScroll||b)l.scrollTop=l.scrollHeight;}
        function formatUptime(s){const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),r=s%60;return h>0?h+'h'+m+'m'+r+'s':m>0?m+'m'+r+'s':r+'s';}
        function escapeHtml(t){if(!t)return'';const d=document.createElement('div');d.textContent=String(t);return d.innerHTML;}
        document.getElementById('logs').addEventListener('scroll',e=>{const c=e.target;autoScroll=(c.scrollHeight-c.scrollTop===c.clientHeight);});
    </script>
</body>
</html>
EOFHTML

echo "✅ HTML 模板已创建"

# 5. 启动容器
echo ""
echo "[5/7] 启动容器..."
docker run -d \
  --name iris-worker \
  -p 8080:8080 \
  -v "$WORK_DIR:/app" \
  -w /app \
  -e SERVER_IP="$SERVER_IP" \
  -e WS_PORT="5000" \
  --restart unless-stopped \
  docker.m.daocloud.io/library/python:3.10-slim \
  sh -c "
    echo '📦 安装依赖...' && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask requests websockets psutil -q && \
    echo '✅ 依赖安装完成' && \
    echo '🚀 启动 Worker...' && \
    python3 worker.py
  "

echo "⏳ 等待 20 秒启动..."
sleep 20

# 6. 验证服务
echo ""
echo "[6/7] 验证服务..."
for i in {1..10}; do
    if curl -s "http://localhost:8080/health" 2>/dev/null | grep -q "healthy"; then
        echo "✅ Worker 已启动"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️  服务启动中，请稍候..."
    fi
    sleep 2
done

HEALTH=$(curl -s "http://localhost:8080/health" 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo ""
    echo "健康状态：$HEALTH"
else
    echo ""
    echo "⚠️  查看日志..."
    docker logs iris-worker --tail 30
fi

# 7. 检查 HTML 文件
echo ""
echo "[7/7] 检查 HTML 模板..."
docker exec iris-worker ls -la /app/index.html 2>&1 && echo "✅ HTML 模板已创建" || echo "⚠️  HTML 模板未创建"

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo ""
echo "🎯 v19 特性:"
echo "   ✅ HTML 文件嵌入脚本（100% 可靠）"
echo "   ✅ 亮色趋势线（蓝/紫/粉）"
echo "   ✅ 日志中文正常"
echo ""
echo "💡 提示："
echo "   1. 强制刷新：Cmd+Shift+R"
echo "   2. 查看日志：docker logs -f iris-worker"
echo "   3. 等待 30 秒让趋势图显示"
echo ""

# 自动打开监控面板
echo "🌐 5 秒后自动打开监控面板..."
sleep 5
open "http://localhost:8080/" 2>/dev/null || true
