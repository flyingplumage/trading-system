#!/bin/bash
# 量化训练系统 - Docker 一键部署
# 适用于 Mac / Linux

set -e

PROJECT_DIR=~/.openclaw/workspace/projects/trading-system-release

echo "=========================================="
echo "  量化训练系统 Docker 一键部署"
echo "=========================================="
echo ""

# 1. 检查 Docker
echo "[1/5] 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker Desktop"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

docker --version
docker compose version
echo "✅ Docker 检查通过"

# 2. 进入项目目录
echo ""
echo "[2/5] 进入项目目录..."
cd "$PROJECT_DIR" || {
    echo "❌ 项目目录不存在：$PROJECT_DIR"
    exit 1
}
echo "✅ 项目目录：$PROJECT_DIR"

# 3. 创建数据目录
echo ""
echo "[3/5] 创建数据目录..."
mkdir -p backend/data backend/shared
echo "✅ 数据目录已创建"

# 4. 创建环境变量
echo ""
echo "[4/5] 创建环境变量..."
cat > .env << EOF
DATABASE_URL=postgresql://quant:quant_password_2024@postgres:5432/qframe
JWT_SECRET=quant_jwt_secret_$(date +%s)
API_HOST=0.0.0.0
API_PORT=5000
CORS_ORIGINS='["http://localhost:3000","http://localhost"]'
EOF
echo "✅ .env 已创建"

# 5. 构建并启动
echo ""
echo "[5/5] 构建并启动服务 (首次约 5-10 分钟)..."
docker compose -f docker-compose-full.yml up -d --build

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 10

# 验证
echo ""
echo "=========================================="
echo "  验证服务..."
echo "=========================================="
docker compose -f docker-compose-full.yml ps

echo ""
echo "测试后端..."
curl -s http://localhost:5000/health && echo " ✅ 后端正常" || echo " ❌ 后端异常"

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "📍 服务地址:"
echo "  后端 API: http://localhost:5000"
echo "  前端：http://localhost:3000"
echo "  PostgreSQL: localhost:5432"
echo ""
echo "📊 常用命令:"
echo "  查看日志：docker compose -f docker-compose-full.yml logs -f"
echo "  停止服务：docker compose -f docker-compose-full.yml down"
echo "  重启服务：docker compose -f docker-compose-full.yml restart"
echo ""
echo "🔑 默认凭据:"
echo "  数据库：quant / quant_password_2024 / qframe"
echo ""
echo "=========================================="
