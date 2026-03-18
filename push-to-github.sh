#!/bin/bash

# GitHub 推送脚本
# 使用方法：./push-to-github.sh

set -e

echo "🚀 准备推送到 GitHub..."
echo ""

# 检查是否在正确的目录
if [ ! -f ".git/config" ]; then
    echo "❌ 错误：当前目录不是 Git 仓库"
    exit 1
fi

# 获取远程仓库地址
REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE" ]; then
    echo "❌ 错误：未配置远程仓库"
    exit 1
fi

echo "📦 远程仓库：$REMOTE"
echo ""

# 方法 1：使用环境变量（推荐用于 CI/CD）
if [ -n "$GITHUB_TOKEN" ]; then
    echo "✅ 使用 GITHUB_TOKEN 推送..."
    TOKEN_URL=$(echo "$REMOTE" | sed 's|https://|https://x-access-token:'$GITHUB_TOKEN'@|')
    git push "$TOKEN_URL" main
    exit 0
fi

# 方法 2：使用 Git 凭证管理器
echo "请选择认证方式："
echo "1. 使用 Git 凭证管理器（推荐）"
echo "2. 使用个人访问令牌"
echo "3. 使用 SSH"
echo ""
read -p "请选择 [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "📝 配置 Git 凭证管理器..."
        git config --global credential.helper store
        echo "✅ 凭证管理器已配置"
        echo ""
        echo "🚀 开始推送（将要求输入用户名和密码）..."
        git push origin main
        ;;
    2)
        echo ""
        echo "📝 请输入 GitHub Personal Access Token"
        echo "获取令牌：https://github.com/settings/tokens"
        echo ""
        read -p "Token: " -s token
        echo ""
        TOKEN_URL=$(echo "$REMOTE" | sed 's|https://|https://'$token'@|')
        echo "🚀 开始推送..."
        git push "$TOKEN_URL" main
        ;;
    3)
        echo ""
        echo "📝 切换到 SSH 模式..."
        SSH_REMOTE=$(echo "$REMOTE" | sed 's|https://github.com/|git@github.com:|')
        git remote set-url origin "$SSH_REMOTE"
        echo "✅ 远程仓库已更新：$SSH_REMOTE"
        echo ""
        echo "🚀 开始推送（确保已配置 SSH 密钥）..."
        git push origin main
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 推送完成！"
echo "🌐 查看仓库：$REMOTE"
