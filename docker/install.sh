#!/bin/bash
# PostgreSQL Docker 环境安装脚本
# 适用于 Ubuntu 24.04

set -e

echo "=========================================="
echo "  PostgreSQL Docker 环境安装"
echo "=========================================="

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    echo "sudo $0"
    exit 1
fi

# 1. 安装 Docker
echo ""
echo "[1/4] 安装 Docker..."
apt update
apt install -y docker.io docker-compose-plugin

# 2. 启动 Docker 服务
echo ""
echo "[2/4] 启动 Docker 服务..."
systemctl enable docker
systemctl start docker
systemctl status docker --no-pager

# 3. 验证安装
echo ""
echo "[3/4] 验证安装..."
docker --version
docker compose version

# 4. 配置量化系统 PostgreSQL
echo ""
echo "[4/4] 配置量化系统 PostgreSQL..."
cd /root/.openclaw/workspace/projects/trading-system-release/docker

# 复制环境变量
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
else
    echo "⚠️ .env 文件已存在，跳过"
fi

# 启动服务
echo ""
echo "启动 PostgreSQL 服务..."
docker compose up -d

# 等待服务就绪
echo "等待服务启动..."
sleep 5

# 验证
echo ""
echo "验证服务..."
docker compose ps

echo ""
echo "=========================================="
echo "  ✅ 安装完成！"
echo "=========================================="
echo ""
echo "服务信息:"
echo "  PostgreSQL: localhost:5432"
echo "  账号：quant"
echo "  密码：quant_password_2024"
echo "  数据库：qframe"
echo ""
echo "pgAdmin:"
echo "  地址：http://localhost:5050"
echo "  账号：admin@qframe.local"
echo "  密码：admin_password_2024"
echo ""
echo "连接测试:"
echo "  docker exec -it quant-postgres psql -U quant -d qframe"
echo ""
echo "查看日志:"
echo "  docker compose logs -f"
echo ""
