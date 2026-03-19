# 解决方案：Worker 无法连接 5000 端口

## 问题
Worker 日志显示：`[Errno 111] Connect call failed ('162.14.115.79', 5000)`

## 原因
腾讯云服务器安全组未开放 5000 端口

## 解决方案

### 方案 1：配置腾讯云安全组（推荐）

1. 登录腾讯云控制台
   https://console.cloud.tencent.com/cvm/security

2. 找到当前实例的安全组

3. 添加入站规则：
   ```
   端口：5000
   协议：TCP
   来源：0.0.0.0/0
   动作：允许
   ```

4. 保存配置

5. 验证（在 Mac 上执行）：
   ```bash
   curl http://162.14.115.79:5000/health
   ```

### 方案 2：SSH 隧道（临时测试）

在 Mac 上执行：
```bash
# 建立 SSH 隧道（保持终端打开）
ssh -L 5000:localhost:5000 root@162.14.115.79 -N
```

然后 Worker 会自动通过隧道连接！

### 方案 3：使用 ngrok 内网穿透

在服务器上执行：
```bash
# 安装 ngrok
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list
apt update
apt install ngrok

# 启动
ngrok http 5000
```

会生成一个公网 URL，Worker 连接那个 URL 即可！

## 验证

配置完成后，在 Mac 上执行：
```bash
# 测试 HTTP 连接
curl http://162.14.115.79:5000/health

# 应该返回：
# {"status":"healthy",...}
```

如果成功，Worker 会自动连接！
