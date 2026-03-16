# Tushare 数据集成指南

## 1. 获取 Tushare Token

1. 访问 https://tushare.pro 注册账号
2. 登录后进入个人中心：https://tushare.pro/user/token
3. 复制你的 API Token

## 2. 配置 Token

### 方式 1：环境变量（推荐）

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export TUSHARE_TOKEN="your_token_here"

# 或者在当前会话设置
export TUSHARE_TOKEN="your_token_here"
```

### 方式 2：修改配置文件

编辑 `backend/configs/tushare_config.yaml`：

```yaml
tushare:
  token: "your_token_here"
```

## 3. 使用 API

### 3.1 查看数据状态

```bash
curl http://localhost:5000/api/tushare/status
```

响应示例：
```json
{
  "success": true,
  "data": {
    "status": "running",
    "total_stocks": 0,
    "feature_files": 0,
    "total_records": 0
  }
}
```

### 3.2 更新股票池

```bash
curl -X POST http://localhost:5000/api/tushare/pool/update
```

### 3.3 获取股票池

```bash
curl http://localhost:5000/api/tushare/pool
```

### 3.4 更新单只股票

```bash
curl -X POST http://localhost:5000/api/tushare/update/000001.SZ
```

### 3.5 批量更新所有股票

```bash
# 更新全部（可能需要较长时间）
curl -X POST http://localhost:5000/api/tushare/update/all

# 限制更新数量（测试用）
curl -X POST "http://localhost:5000/api/tushare/update/all?limit=10"
```

## 4. 增量更新逻辑

系统自动实现增量更新：

1. **首次更新**：下载最近 1 年的日线数据
2. **后续更新**：只下载上次更新之后的新数据
3. **自动去重**：合并时自动去除重复记录
4. **限流保护**：每 10 次请求暂停 1 秒，避免触发 API 限制

## 5. 数据存储结构

```
backend/shared/data/
├── raw/                    # 原始数据缓存（可选）
├── features/               # 特征数据（Parquet 格式）
│   ├── 000001_SZ.parquet
│   ├── 600519_SH.parquet
│   └── ...
└── pool/
    └── stock_pool.yaml     # 股票池配置
```

## 6. 定时更新（可选）

### 使用 Cron

添加定时任务（每天下午 4 点盘后更新）：

```bash
crontab -e

# 添加以下行
0 16 * * * curl -X POST http://localhost:5000/api/tushare/update/all
```

### 使用系统定时器

创建 systemd service（Linux）：

```ini
# /etc/systemd/system/tushare-update.service
[Unit]
Description=Tushare Daily Update
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -X POST http://localhost:5000/api/tushare/update/all
WorkingDirectory=/root/.openclaw/workspace/projects/trading-system/backend
```

## 7. 注意事项

1. **Token 安全**：不要将 Token 提交到 Git 仓库
2. **API 限制**：免费用户有积分限制，注意控制请求频率
3. **数据质量**：Tushare 数据可能存在延迟，实盘前请验证
4. **存储空间**：全量 A 股数据约需 1-2GB 磁盘空间

## 8. 故障排查

### 问题：Token 无效

```
Tushare API 错误：token 无效
```

**解决**：检查 Token 是否正确，确认账号已激活

### 问题：API 限流

```
Tushare API 错误：访问次数超过限制
```

**解决**：降低更新频率，或升级 Tushare 会员

### 问题：数据目录权限

```
PermissionError: [Errno 13] Permission denied
```

**解决**：
```bash
chmod -R 755 /root/.openclaw/workspace/projects/trading-system/backend/shared/data
```
