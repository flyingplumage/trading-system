# Iris Worker 离线部署包

## 部署步骤

### 1. 配置 Docker 镜像加速

编辑 `~/.docker/daemon.json`：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ]
}
```

**重启 Docker Desktop**

### 2. 构建镜像

```bash
cd offline-package
docker build -t iris-worker:latest .
```

### 3. 启动容器

```bash
docker run -d \
  --name iris-worker \
  -p 8080:8080 \
  -e SERVER_IP="162.14.115.79" \
  -e INSTRUCTION_PORT="8888" \
  -e WORKER_PORT="8080" \
  --restart unless-stopped \
  iris-worker:latest
```

### 4. 验证

```bash
curl http://localhost:8080/health
docker logs -f iris-worker
```

## 远程指令

服务器会自动向 `http://162.14.115.79:8888/instructions.json` 发送指令
Worker 每 5 秒自动轮询检查
