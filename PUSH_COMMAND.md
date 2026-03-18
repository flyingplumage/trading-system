# 🚀 一键推送命令

由于当前环境无法交互式输入密码，请使用以下方法之一推送：

---

## 方法一：手动推送（推荐）

在本地终端执行：

```bash
cd /root/.openclaw/workspace/projects/trading-system-release

# 如果之前配置过 token，直接推送
git push origin main

# 或使用 token 推送（替换 YOUR_TOKEN）
git push https://YOUR_TOKEN@github.com/flyingplumage/trading-system.git main
```

---

## 方法二：使用保存的凭证

如果之前配置过凭证管理器：

```bash
# 清除旧凭证（如果需要）
git credential-manager erase

# 重新配置
git config --global credential.helper store

# 推送（会提示输入一次，之后自动保存）
git push origin main
```

---

## 方法三：切换到 SSH

```bash
# 切换到 SSH 模式
git remote set-url origin git@github.com:flyingplumage/trading-system.git

# 验证
git remote -v

# 推送（需要配置 SSH 密钥）
git push origin main
```

---

## 当前提交状态

```
最新提交：ec931b0 docs: 添加 GitHub 推送指南
待推送：96 个文件
仓库：https://github.com/flyingplumage/trading-system.git
```

---

## 快速复制命令

```bash
# 完整推送命令（替换 TOKEN）
export GITHUB_TOKEN=你的 token
cd /root/.openclaw/workspace/projects/trading-system-release
git push https://${GITHUB_TOKEN}@github.com/flyingplumage/trading-system.git main
```

---

**代码已准备就绪，请在有交互能力的终端执行推送！**
