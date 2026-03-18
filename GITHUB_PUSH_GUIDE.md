# 📤 GitHub 推送指南

**仓库地址：** https://github.com/flyingplumage/trading-system.git

---

## 🔐 认证方式（三选一）

### 方式一：使用个人访问令牌（推荐）

#### 1. 生成令牌

1. 访问：https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 填写说明：`trading-system-deploy`
4. 选择权限：
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
5. 点击 **Generate token**
6. **复制令牌**（只显示一次，保存好！）

#### 2. 使用令牌推送

```bash
cd /root/.openclaw/workspace/projects/trading-system-release

# 替换 YOUR_TOKEN 为你的实际令牌
git push https://YOUR_TOKEN@github.com/flyingplumage/trading-system.git main
```

**示例：**
```bash
git push https://ghp_1234567890abcdefghijk@github.com/flyingplumage/trading-system.git main
```

---

### 方式二：使用 Git 凭证管理器

#### 1. 配置凭证管理器

```bash
# 启用凭证存储
git config --global credential.helper store

# 如果是 Ubuntu，可能需要安装
sudo apt install -y git-credential-manager
```

#### 2. 推送（会提示输入）

```bash
cd /root/.openclaw/workspace/projects/trading-system-release
git push origin main
```

**输入提示：**
```
Username for 'https://github.com': flyingplumage
Password for 'https://flyingplumage@github.com': [输入个人访问令牌]
```

**注意：** 密码处输入个人访问令牌，不是账号密码！

---

### 方式三：使用 SSH

#### 1. 生成 SSH 密钥

```bash
# 生成新密钥
ssh-keygen -t ed25519 -C "lyra@openclaw.ai"

# 查看公钥
cat ~/.ssh/id_ed25519.pub
```

#### 2. 添加公钥到 GitHub

1. 访问：https://github.com/settings/keys
2. 点击 **New SSH key**
3. 填写标题：`lyra-openclaw`
4. 粘贴公钥内容（`cat ~/.ssh/id_ed25519.pub` 的输出）
5. 点击 **Add SSH key**

#### 3. 切换到 SSH 模式

```bash
cd /root/.openclaw/workspace/projects/trading-system-release

# 修改远程仓库地址
git remote set-url origin git@github.com:flyingplumage/trading-system.git

# 验证
git remote -v
# 应该显示：
# origin  git@github.com:flyingplumage/trading-system.git (fetch)
# origin  git@github.com:flyingplumage/trading-system.git (push)
```

#### 4. 推送

```bash
git push origin main
```

---

## 🚀 快速推送（使用脚本）

```bash
cd /root/.openclaw/workspace/projects/trading-system-release

# 设置令牌环境变量
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# 运行推送脚本
./push-to-github.sh
```

---

## 📊 当前提交状态

**最近提交：**
```
edf4aae docs: 添加 GitHub 推送脚本
014781b feat: 完整量化训练系统发布
cfcb8e7 docs: 添加发布报告 v1.0.0
0fe34c2 release: v1.0.0 量化训练系统 - 生产就绪版本
```

**待推送文件：**
- ✅ 前端代码（Vue 3 + Naive UI）
- ✅ 后端代码（FastAPI）
- ✅ 测试用例
- ✅ Docker 配置
- ✅ 完整文档

**总计：** 95 个文件，已准备就绪

---

## ⚠️ 常见问题

### 1. 认证失败

**错误：** `remote: Invalid username or password`

**解决：**
- 确保使用个人访问令牌，不是账号密码
- 检查令牌权限是否包含 `repo`
- 检查令牌是否过期

### 2. 权限不足

**错误：** `ERROR: Permission to flyingplumage/trading-system.git denied`

**解决：**
- 确认你是仓库所有者或有推送权限
- 检查 SSH 密钥是否正确添加

### 3. 大文件警告

**错误：** `File is large but not tracked by Git LFS`

**解决：**
```bash
# 安装 Git LFS
git lfs install

# 跟踪大文件
git lfs track "*.pth"
git lfs track "*.pt"
git lfs track "*.onnx"

# 重新提交
git add .gitattributes
git commit -m "chore: 配置 Git LFS"
```

---

## 🎯 推送后操作

### 1. 验证推送

访问：https://github.com/flyingplumage/trading-system

确认：
- ✅ 代码已更新
- ✅ 提交记录正确
- ✅ README 显示正常

### 2. 创建 Release

1. 访问：https://github.com/flyingplumage/trading-system/releases
2. 点击 **Create a new release**
3. 填写：
   - Tag version: `v1.0.0`
   - Target: `main`
   - Title: `v1.0.0 - 生产就绪版本`
   - Description: 复制 `RELEASE_NOTES.md` 内容
4. 点击 **Publish release**

### 3. 配置 GitHub Actions（可选）

创建 `.github/workflows/ci.yml`：

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/
  
  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd frontend && npm install && npm run build
```

---

## 📚 相关文档

- [发布说明](./RELEASE_NOTES.md)
- [功能评估报告](./功能评估报告.md)
- [功能完善报告](./功能完善报告.md)
- [前端文档](./frontend/README.md)
- [后端文档](./backend/README.md)

---

**准备就绪，可以推送！** 🚀
