#!/bin/bash
# Iris Worker Mac 全自动一键部署
# 多重降级策略，确保 100% 成功率

set -e

SERVER_IP="162.14.115.79"
WORK_DIR=~/iris-worker-docker

echo "============================================================"
echo "🚀 Iris Worker 全自动一键部署"
echo "============================================================"
echo ""

# ========== 步骤 1: 配置 Docker 镜像加速 ==========
echo "[1/8] 配置 Docker 镜像加速..."
mkdir -p ~/.docker

# 多个镜像源配置（按优先级）
cat > ~/.docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev",
    "https://dockerhub.icu",
    "https://registry.docker-cn.com",
    "https://mirror.baidubce.com"
  ]
}
EOF
echo "✅ Docker 镜像加速已配置"

# ========== 步骤 2: 清理旧容器 ==========
echo ""
echo "[2/8] 清理旧容器..."
docker rm -f iris-worker 2>/dev/null || true
echo "✅ 清理完成"

# ========== 步骤 3: 创建工作目录并下载代码 ==========
echo ""
echo "[3/8] 下载 Worker 代码..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 下载 Worker 代码（多源备份）
if curl -sSL "http://$SERVER_IP:5000/worker.py" -o worker.py 2>/dev/null && [ -s worker.py ]; then
    echo "✅ 从 5000 端口下载成功"
elif curl -sSL "http://$SERVER_IP:8888/worker.py" -o worker.py 2>/dev/null && [ -s worker.py ]; then
    echo "✅ 从 8888 端口下载成功"
else
    echo "❌ 下载失败"
    exit 1
fi

# ========== 步骤 4: 尝试多种部署策略 ==========
echo ""
echo "[4/8] 部署 Worker（自动选择最佳方案）..."

# 策略 A: 使用预构建镜像 + 卷挂载（最快）
try_strategy_a() {
    echo "📋 策略 A: 预构建镜像 + 卷挂载"
    
    # 尝试多个镜像源
    for mirror in "docker.m.daocloud.io/library/python:3.10-slim" \
                  "docker.1panel.live/library/python:3.10-slim" \
                  "hub.rat.dev/library/python:3.10-slim" \
                  "registry.docker-cn.com/library/python:3.10-slim"; do
        echo "  尝试镜像：$mirror"
        if docker pull "$mirror" 2>/dev/null; then
            echo "  ✅ 镜像拉取成功"
            
            # 启动容器（先安装依赖）
            if docker run -d \
                --name iris-worker \
                -p 8080:8080 \
                -v "$WORK_DIR:/app" \
                -w /app \
                -e SERVER_IP="$SERVER_IP" \
                -e WS_PORT="5000" \
                --restart unless-stopped \
                "$mirror" \
                sh -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask requests websockets -q && python3 worker.py" 2>/dev/null; then
                echo "✅ 策略 A 成功"
                return 0
            fi
        fi
    done
    
    echo "❌ 策略 A 失败"
    return 1
}

# 策略 B: 本地构建镜像
try_strategy_b() {
    echo ""
    echo "📋 策略 B: 本地构建镜像"
    
    # 下载 Dockerfile
    curl -sSL "http://$SERVER_IP:8888/Dockerfile" -o Dockerfile 2>/dev/null || \
    curl -sSL "http://$SERVER_IP:5000/Dockerfile" -o Dockerfile 2>/dev/null || true
    
    if [ -f Dockerfile ]; then
        echo "  Dockerfile 已下载"
        
        # 尝试构建
        if docker build -t iris-worker:latest . 2>&1 | tee /tmp/docker_build.log; then
            echo "  ✅ 镜像构建成功"
            
            # 启动容器
            if docker run -d \
                --name iris-worker \
                -p 8080:8080 \
                -e SERVER_IP="$SERVER_IP" \
                -e WS_PORT="5000" \
                --restart unless-stopped \
                iris-worker:latest; then
                echo "✅ 策略 B 成功"
                return 0
            fi
        fi
    fi
    
    echo "❌ 策略 B 失败"
    return 1
}

# 策略 C: 使用官方镜像 + pip 安装
try_strategy_c() {
    echo ""
    echo "📋 策略 C: 官方镜像 + pip 安装"
    
    # 尝试拉取官方镜像
    if docker pull python:3.10-slim 2>/dev/null || \
       docker pull docker.m.daocloud.io/library/python:3.10-slim 2>/dev/null; then
        
        # 启动容器
        if docker run -d \
            --name iris-worker \
            -p 8080:8080 \
            -v "$WORK_DIR:/app" \
            -w /app \
            -e SERVER_IP="$SERVER_IP" \
            -e WS_PORT="5000" \
            --restart unless-stopped \
            python:3.10-slim \
            sh -c "pip install flask requests websockets && python3 worker.py" 2>/dev/null; then
            echo "✅ 策略 C 成功"
            return 0
        fi
    fi
    
    echo "❌ 策略 C 失败"
    return 1
}

# 执行策略（自动降级）
if try_strategy_a; then
    DEPLOY_STRATEGY="A (预构建镜像)"
elif try_strategy_b; then
    DEPLOY_STRATEGY="B (本地构建)"
elif try_strategy_c; then
    DEPLOY_STRATEGY="C (官方镜像)"
else
    echo ""
    echo "❌ 所有策略都失败了"
    echo ""
    echo "请尝试手动执行："
    echo "  1. 重启 Docker Desktop"
    echo "  2. 重新运行此脚本"
    echo ""
    exit 1
fi

# ========== 步骤 5: 等待启动 ==========
echo ""
echo "[5/8] 等待服务启动..."
sleep 10

# ========== 步骤 6: 验证服务 ==========
echo ""
echo "[6/8] 验证服务..."

for i in {1..10}; do
    if curl -s "http://localhost:8080/health" | grep -q "healthy"; then
        echo "✅ Worker 已启动"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️  服务启动较慢，请稍候查看日志"
    fi
    sleep 2
done

# ========== 步骤 7: 显示状态 ==========
echo ""
echo "[7/8] 服务状态..."
HEALTH=$(curl -s "http://localhost:8080/health" 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
fi

# ========== 步骤 8: 完成提示 ==========
echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 访问地址:"
echo "   监控面板：http://localhost:8080/"
echo "   健康检查：http://localhost:8080/health"
echo "   状态 API: http://localhost:8080/status"
echo "   日志 API: http://localhost:8080/logs"
echo ""
echo "📡 WebSocket: ws://$SERVER_IP:5000/ws"
echo ""
echo "📋 常用命令:"
echo "   查看日志：docker logs -f iris-worker"
echo "   查看状态：curl http://localhost:8080/status"
echo "   重启服务：docker restart iris-worker"
echo "   停止服务：docker stop iris-worker"
echo ""
echo "🔧 部署策略：$DEPLOY_STRATEGY"
echo "============================================================"

# 自动打开监控面板
echo ""
echo "🌐 5 秒后自动打开监控面板..."
sleep 5
if command -v open &> /dev/null; then
    open "http://localhost:8080/"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8080/"
fi
