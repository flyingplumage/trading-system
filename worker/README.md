# Worker 已移除

Worker 模块已完全剥离为独立项目。

## 📦 独立项目

**项目名称：** distributed-trainer

**本地路径：** `/root/.openclaw/workspace/projects/distributed-trainer/`

**GitHub：** https://github.com/flyingplumage/distributed-trainer

## 🚀 部署 Worker

### 方式 1：从独立项目部署

```bash
cd /root/.openclaw/workspace/projects/distributed-trainer
pip install -r requirements.txt
python core/worker.py
```

### 方式 2：Docker 部署

```bash
docker run -d \
  -p 8080:8080 \
  -e SERVER_IP=your-server.com \
  -v worker-data:/models \
  flyingplumage/distributed-trainer:latest
```

### 方式 3：一键部署（任何机器）

```bash
curl -sSL https://raw.githubusercontent.com/flyingplumage/distributed-trainer/main/deploy.sh | bash
```

## 🔗 量化项目集成

量化后端通过 HTTP API 调用 Worker：

```python
import requests

# 提交量化训练任务
response = requests.post('http://worker:8080/api/task/submit', json={
    'task_id': 'quant-train-001',
    'type': 'quant',  # 路由到量化训练插件
    'params': {
        'algorithm': 'PPO',
        'stock_code': '000001.SZ',
        'epochs': 100,
        'initial_capital': 100000
    }
})

# 查询状态
status = requests.get('http://worker:8080/api/task/status/quant-train-001')
```

## 📡 API 参考

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/capabilities` | GET | 获取支持的训练类型 |
| `/api/task/submit` | POST | 提交训练任务 |
| `/api/task/status/<id>` | GET | 查询任务状态 |
| `/api/task/queue` | GET | 任务队列 |

## 📁 目录说明

本目录保留仅作为占位符，提醒使用独立项目。

**不要在此目录放置任何代码！**

---

查看完整文档：https://github.com/flyingplumage/distributed-trainer
