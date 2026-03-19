# SSH 隧道解决方案

## 问题
服务器自身 IP (162.14.115.79) 无法访问 5000 端口
原因：云服务器安全组或 NAT 配置问题

## 临时解决方案：SSH 隧道

### 在 Mac 上执行：

```bash
# 建立 SSH 隧道（保持终端打开）
ssh -L 5000:localhost:5000 -L 8888:localhost:8888 root@162.14.115.79 -N
```

### 然后修改 Worker 配置：

在 Mac 上重新部署 Worker，使用本地隧道：

```bash
docker rm -f iris-worker

docker run -d \
  --name iris-worker \
  -p 8080:8080 \
  -e SERVER_IP="localhost" \
  -e WS_PORT="5000" \
  --restart unless-stopped \
  docker.m.daocloud.io/library/python:3.10-slim \
  sh -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask requests websockets psutil -q && \
         curl -sSL http://localhost:8888/worker.py -o worker.py && \
         python3 worker.py"
```

### 验证：

```bash
# 测试隧道连接
curl http://localhost:5000/health

# 查看 Worker 日志
docker logs -f iris-worker

# 应该看到：✅ WebSocket 已连接
```

## 永久解决方案：

联系腾讯云客服，确认：
1. 安全组规则已正确配置
2. 5000 和 8888 端口已开放
3. 是否需要额外配置 NAT 或端口转发
