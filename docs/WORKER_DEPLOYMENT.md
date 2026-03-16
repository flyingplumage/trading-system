# 分布式训练 Worker 部署指南

**版本:** v1.0  
**更新:** 2026-03-16

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────┐
│      后端服务器 (端口 5000)              │
│  - 任务调度                              │
│  - Worker 管理                            │
│  - 结果接收                              │
└──────────────┬──────────────────────────┘
               │
        WebSocket + HTTP
               │
    ┌──────────┼──────────┬──────────┐
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Worker 1│ │Worker 2│ │Worker 3│ │Worker N│
│ (Linux)│ │ (Mac)  │ │ (Win)  │ │ (Mac)  │
└────────┘ └────────┘ └────────┘ └────────┘
```

---

## 📦 Worker 功能

- ✅ 跨平台支持 (Linux/Mac/Windows)
- ✅ WebSocket 实时接收指令
- ✅ HTTP 上报训练结果
- ✅ 自动心跳保活
- ✅ GPU/CPU 自动检测
- ✅ Mac M1/M2 MPS 支持
- ✅ 训练进度实时上报
- ✅ 断点续训支持

---

## 🚀 快速部署

### Linux 部署

```bash
# 1. 运行安装脚本
curl -O http://YOUR_BACKEND_IP:5000/worker/install.sh
chmod +x install.sh
./install.sh

# 2. 配置 Worker
cd ~/trading-worker
vi worker_config.json

# 3. 启动 Worker
source venv/bin/activate
python worker.py --api-key YOUR_API_KEY
```

### Mac 部署 (推荐)

```bash
# 1. 运行 Mac 专用脚本
curl -O http://YOUR_BACKEND_IP:5000/worker/deploy-mac.sh
chmod +x deploy-mac.sh
./deploy-mac.sh

# 2. 配置 Worker
cd ~/trading-worker
vi worker_config.json

# 3. 启动 Worker
./start.sh --api-key YOUR_API_KEY
```

### Windows 部署

```powershell
# 1. 下载 Worker 文件
# 从 GitHub 下载 worker 目录

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 Worker
python worker.py --api-key YOUR_API_KEY
```

---

## ⚙️ 配置说明

### worker_config.json

```json
{
  "backend_url": "http://192.168.1.100:5000",
  "ws_url": "ws://192.168.1.100:5000/ws",
  "api_key": "FDMxaWwvNoIsabnbcrZHy3oQ_GiFlgynt81rjTLKt4g",
  "work_dir": "/home/user/trading-worker/data"
}
```

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `backend_url` | 后端 HTTP 地址 | `http://192.168.1.100:5000` |
| `ws_url` | 后端 WebSocket 地址 | `ws://192.168.1.100:5000/ws` |
| `api_key` | API Key (从后端获取) | `FDMxaWwv...` |
| `work_dir` | 工作目录 | `/home/user/trading-worker/data` |

---

## 🔧 系统服务配置

### Linux (systemd)

```bash
# 1. 复制服务文件
sudo cp worker.service /etc/systemd/system/

# 2. 编辑服务文件
sudo vi /etc/systemd/system/worker.service
# 修改 User 和 WorkingDirectory

# 3. 启用服务
sudo systemctl daemon-reload
sudo systemctl enable worker
sudo systemctl start worker

# 4. 查看状态
sudo systemctl status worker

# 5. 查看日志
sudo journalctl -u worker -f
```

### Mac (launchd)

```bash
# 1. 创建启动脚本
cat > ~/Library/LaunchAgents/com.trading.worker.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.trading.worker</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/YOUR_USER/trading-worker/venv/bin/python</string>
    <string>/Users/YOUR_USER/trading-worker/worker.py</string>
    <string>--api-key</string>
    <string>YOUR_API_KEY</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/YOUR_USER/trading-worker</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
EOF

# 2. 加载服务
launchctl load ~/Library/LaunchAgents/com.trading.worker.plist

# 3. 查看状态
launchctl list | grep trading.worker
```

---

## 📊 后端管理

### 查看 Worker 列表

```bash
curl http://localhost:5000/api/worker/list \
  -H "Authorization: Bearer TOKEN"
```

**响应:**
```json
{
  "success": true,
  "data": {
    "total": 3,
    "workers": [
      {
        "worker_id": "worker_a1b2c3d4",
        "hostname": "macbook-pro",
        "platform": "Darwin",
        "status": "idle",
        "last_heartbeat": "2026-03-16T22:50:00",
        "gpu_info": {
          "available": true,
          "count": 1,
          "devices": [{"name": "Apple Silicon GPU"}]
        }
      }
    ]
  }
}
```

### 查看 Worker 统计

```bash
curl http://localhost:5000/api/worker/stats \
  -H "Authorization: Bearer TOKEN"
```

**响应:**
```json
{
  "total_workers": 5,
  "online_workers": 4,
  "busy_workers": 2,
  "idle_workers": 2
}
```

---

## 🔍 故障排查

### Worker 无法连接后端

```bash
# 检查网络
ping YOUR_BACKEND_IP

# 检查端口
telnet YOUR_BACKEND_IP 5000

# 检查防火墙
sudo ufw status  # Linux
sudo pfctl -sr   # Mac
```

### Worker 频繁离线

```bash
# 查看日志
tail -f ~/trading-worker/worker.log

# 检查资源
htop  # CPU/内存
nvidia-smi  # GPU (Linux)
```

### Mac M1/M2 GPU 未启用

```bash
# 检查 PyTorch MPS 支持
python3 -c "import torch; print(torch.backends.mps.is_available())"

# 重新安装 MPS 支持的 PyTorch
pip uninstall torch
pip install torch torchvision torchaudio
```

---

## 📈 性能优化

### Mac 优化

```bash
# 使用 MPS 加速
export PYTORCH_ENABLE_MPS_FALLBACK=1

# 限制 CPU 使用
export OMP_NUM_THREADS=4
```

### Linux 优化

```bash
# 使用 NVIDIA GPU
export CUDA_VISIBLE_DEVICES=0

# 优化内存
export MALLOC_MMAP_THRESHOLD_=1000000
```

---

## 🎯 使用流程

1. **后端创建训练任务**
   ```bash
   POST /api/train/start
   ```

2. **Worker 接收任务** (WebSocket 推送)

3. **Worker 执行训练**
   - 加载数据
   - 创建特征
   - 训练模型
   - 上报进度

4. **Worker 上报结果**
   - 上传模型文件
   - 上报训练指标

5. **后端保存结果**
   - 注册模型
   - 更新任务状态

---

## 🔐 安全建议

1. **API Key 管理**
   - 每个 Worker 使用独立 API Key
   - 定期轮换密钥
   - 限制 API Key 权限

2. **网络安全**
   - 使用内网通信
   - 启用防火墙
   - 使用 HTTPS/WSS

3. **资源限制**
   - 限制 CPU 使用率
   - 限制内存使用
   - 限制磁盘空间

---

**Lyra 备注:** Worker 系统设计为轻量级、易部署，支持大规模分布式训练。
