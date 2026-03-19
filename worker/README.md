# Iris Worker - 纯 WebSocket 方案

## 架构

```
Mac Worker                    服务端
┌─────────────────┐          ┌──────────────┐
│ Docker 镜像      │          │ WebSocket    │
│ (代码已打包)     │ ────────▶│ 5000 端口     │
│                 │          │              │
│ - 启动即连接    │          │ - 接收指令    │
│ - 只连 WebSocket│          │ - 发送进度    │
└─────────────────┘          └──────────────┘
```

## 优势

- ✅ **纯 WebSocket** - 不依赖 HTTP 服务
- ✅ **代码打包** - Worker 代码直接打包进镜像
- ✅ **远程升级** - 通过 WebSocket 推送代码更新
- ✅ **自动重连** - 断开后自动重连

## Mac 部署

### 方案 1: 一键部署脚本

```bash
curl -sSL http://162.14.115.79:8888/deploy-mac-docker.sh | bash
```

### 方案 2: 手动部署

```bash
# 1. 创建工作目录
cd ~/iris-worker

# 2. 构建镜像
docker build -t iris-worker:latest .

# 3. 启动容器
docker run -d \
  --name iris-worker \
  -e SERVER_IP=162.14.115.79 \
  -e WS_PORT=5000 \
  -p 8080:8080 \
  --restart unless-stopped \
  iris-worker:latest

# 4. 查看日志
docker logs -f iris-worker

# 5. 访问监控面板
open http://localhost:8080/
```

### 方案 3: Docker Compose

```bash
cd ~/iris-worker
docker-compose up -d
docker-compose logs -f
```

## 常用命令

```bash
# 查看日志
docker logs -f iris-worker

# 查看状态
curl http://localhost:8080/health

# 重启服务
docker restart iris-worker

# 停止服务
docker stop iris-worker

# 删除容器
docker rm -f iris-worker

# 重新构建镜像
docker build -t iris-worker:latest .
```

## 远程升级

服务端发送升级指令：

```bash
curl -X POST http://162.14.115.79:5000/ws/worker/command \
  -H "Content-Type: application/json" \
  -d '{
    "type": "upgrade",
    "data": {
      "version": "v25",
      "script_url": "http://162.14.115.79:8888/worker_v25.py",
      "restart": true
    }
  }'
```

Worker 会自动：
1. 下载新版本代码
2. 备份旧版本
3. 重启进程

## 监控

访问 http://localhost:8080/ 查看：
- WebSocket 连接状态
- 硬件资源使用（CPU/内存/磁盘）
- 实时日志
- 训练进度

## 故障排查

### Worker 无法连接

```bash
# 1. 检查容器状态
docker ps | grep iris-worker

# 2. 查看日志
docker logs iris-worker --tail 50

# 3. 测试网络连接
docker exec iris-worker ping -c 2 162.14.115.79

# 4. 重启容器
docker restart iris-worker
```

### 监控面板无法访问

```bash
# 1. 检查端口
docker port iris-worker

# 2. 测试健康检查
curl http://localhost:8080/health

# 3. 查看容器日志
docker logs iris-worker | grep -i "error\|exception"
```

## 文件说明

- `Dockerfile` - Docker 镜像配置
- `docker-compose.yml` - Docker Compose 配置
- `worker.py` - Worker 主程序
- `deploy-mac-docker.sh` - Mac 部署脚本
- `README.md` - 本文档
