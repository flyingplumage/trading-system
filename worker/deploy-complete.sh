#!/bin/bash
# Iris Worker 完整一键部署脚本 v65
# 包含所有修复：Docker 卷挂载/任务卡片/依赖卡片/禁止缓存

set -e

SERVER_IP="${SERVER_IP:-162.14.115.79}"
WS_PORT="${WS_PORT:-5000}"
WORK_DIR=~/iris-worker-data

echo "============================================================"
echo "🚀 Iris Worker v65 完整一键部署"
echo "============================================================"
echo ""

# 1. 停止旧容器
echo "[1/8] 停止旧容器..."
docker stop iris-worker 2>/dev/null || true
docker rm iris-worker 2>/dev/null || true
echo "✅ 旧容器已清理"

# 2. 删除旧镜像
echo ""
echo "[2/8] 删除旧镜像..."
docker images | grep iris-worker | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true
echo "✅ 旧镜像已清理"

# 3. 创建数据目录
echo ""
echo "[3/8] 创建数据目录..."
mkdir -p "$WORK_DIR"
echo "✅ 数据目录：$WORK_DIR"

# 4. 下载 Worker 代码
echo ""
echo "[4/8] 下载 Worker 代码..."
curl -sSL "http://$SERVER_IP:$WS_PORT/files/worker.py" -o "$WORK_DIR/worker.py"

if [ ! -s "$WORK_DIR/worker.py" ]; then
    echo "❌ 下载失败，请检查服务器 $WS_PORT 端口是否开放"
    exit 1
fi

VERSION=$(grep "Iris Worker v" "$WORK_DIR/worker.py" | head -1 | grep -o "v[0-9]*" || echo "unknown")
echo "✅ Worker 代码已下载 ($VERSION)"

# 5. 构建 Docker 镜像
echo ""
echo "[5/8] 构建 Docker 镜像..."

# 检查是否有 python 镜像
PYTHON_IMAGE=""
if docker images | grep -q "python"; then
    PYTHON_IMAGE=$(docker images | grep python | head -1 | awk '{print $1":"$2}')
    echo "✅ 使用已有镜像：$PYTHON_IMAGE"
else
    # 尝试多个镜像源
    echo "⚠️ 尝试拉取 python 镜像..."
    MIRRORS=(
        "docker.m.daocloud.io/python:3.12-slim"
        "dockerhub.azk8s.cn/python:3.12-slim"
        "registry.docker-cn.com/library/python:3.12-slim"
        "python:3.12-slim"
    )
    
    for mirror in "${MIRRORS[@]}"; do
        echo "  尝试：$mirror"
        if docker pull "$mirror" 2>/dev/null; then
            PYTHON_IMAGE="$mirror"
            echo "  ✅ 拉取成功"
            break
        fi
    done
    
    if [ -z "$PYTHON_IMAGE" ]; then
        echo ""
        echo "❌ 所有镜像源都失败，请手动执行："
        echo "   docker pull docker.m.daocloud.io/python:3.12-slim"
        exit 1
    fi
fi

cat > "$WORK_DIR/Dockerfile" << DOCKERFILE
FROM $PYTHON_IMAGE
WORKDIR /app
RUN pip install --no-cache-dir flask psutil websockets requests
EXPOSE 8080
CMD ["python", "/data/worker.py"]
DOCKERFILE

cd "$WORK_DIR"
docker build --no-cache -t iris-worker:v65 . 2>&1 | tail -5
echo "✅ 镜像构建完成 (iris-worker:v65)"

# 6. 启动容器（使用绝对路径挂载卷）
echo ""
echo "[6/8] 启动容器..."

# 获取绝对路径
ABS_WORK_DIR=$(cd "$WORK_DIR" && pwd)

docker run -d \
  --name iris-worker \
  -p 8080:8080 \
  -v "$ABS_WORK_DIR:/data:rw" \
  -e SERVER_IP="$SERVER_IP" \
  -e WS_PORT="$WS_PORT" \
  -e WORKER_PORT="8080" \
  --restart unless-stopped \
  iris-worker:v65

echo "✅ 容器已启动"

# 7. 等待启动
echo ""
echo "[7/8] 等待容器启动..."
sleep 8

# 8. 验证
echo ""
echo "[8/8] 验证部署..."

# 检查容器状态
if docker ps | grep -q iris-worker; then
    echo "✅ 容器运行正常"
else
    echo "❌ 容器未运行"
    docker logs iris-worker --tail 20
    exit 1
fi

# 检查版本
PAGE_VERSION=$(curl -s http://localhost:8080/ | grep "Iris Worker v" | head -1 | grep -o "v[0-9]*" || echo "unknown")
echo "✅ 页面版本：$PAGE_VERSION"

# 检查 server_tasks
TASK_COUNT=$(curl -s http://localhost:8080/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('server_tasks',[])))" 2>/dev/null || echo "0")
echo "✅ 任务数：$TASK_COUNT"

# 检查任务卡片
if curl -s http://localhost:8080/ | grep -q "tasks-card"; then
    echo "✅ 任务卡片 HTML 已就绪"
else
    echo "⚠️ 任务卡片 HTML 未找到"
fi

# 检查依赖卡片
if curl -s http://localhost:8080/ | grep -q "deps-detail-card"; then
    echo "✅ 依赖卡片 HTML 已就绪"
else
    echo "⚠️ 依赖卡片 HTML 未找到"
fi

# 完成
echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📊 监控面板：http://localhost:8080/"
echo "📁 数据目录：$WORK_DIR"
echo "🐳 容器名称：iris-worker"
echo "📦 镜像版本：iris-worker:v65"
echo ""
echo "💡 重要提示："
echo "   1. 请彻底清除浏览器缓存后访问"
echo "   2. Chrome: Cmd+Shift+Delete → 清除缓存 → Cmd+Q 关闭 → 重新打开"
echo "   3. Safari: 开发→清空缓存 → Cmd+Q 关闭 → 重新打开"
echo ""
echo "🔧 常用命令："
echo "   docker logs iris-worker          # 查看日志"
echo "   docker stop iris-worker          # 停止容器"
echo "   docker restart iris-worker       # 重启容器"
echo "   docker rm iris-worker            # 删除容器"
echo ""

# 显示容器日志
echo "📋 最近日志:"
docker logs iris-worker --tail 5
