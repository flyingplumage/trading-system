#!/bin/bash
# Worker 连接诊断脚本

SERVER_IP="162.14.115.79"
WS_PORT="5000"

echo "============================================================"
echo "🔍 Worker 连接诊断"
echo "============================================================"
echo ""

echo "1. 检查容器网络..."
docker inspect iris-worker --format='{{.NetworkSettings.IPAddress}}' 2>/dev/null || echo "❌ 容器未运行"

echo ""
echo "2. 测试容器内 DNS 解析..."
docker exec iris-worker ping -c 2 $SERVER_IP 2>&1 | head -5 || echo "❌ 无法执行"

echo ""
echo "3. 测试容器内 HTTP 连接..."
docker exec iris-worker python3 -c "
import requests
try:
    r = requests.get('http://$SERVER_IP:$WS_PORT/health', timeout=5)
    print(f'✅ HTTP 连接成功：{r.status_code}')
    print(r.text)
except Exception as e:
    print(f'❌ HTTP 连接失败：{e}')
" 2>&1 || echo "❌ 无法执行"

echo ""
echo "4. 测试容器内 WebSocket 连接..."
docker exec iris-worker python3 -c "
import asyncio, websockets, json
async def test():
    try:
        async with websockets.connect('ws://$SERVER_IP:$WS_PORT/ws/worker', additional_headers={'Worker-ID': 'diagnose'}, open_timeout=5) as ws:
            print('✅ WebSocket 连接成功')
            await ws.send(json.dumps({'type': 'handshake', 'worker_id': 'diagnose'}))
            resp = await ws.recv()
            print(f'📨 响应：{resp}')
    except Exception as e:
        print(f'❌ WebSocket 连接失败：{e}')
asyncio.run(test())
" 2>&1 || echo "❌ 无法执行"

echo ""
echo "5. 查看 Worker 日志..."
docker logs iris-worker --tail 30 2>&1 | tail -15

echo ""
echo "============================================================"
echo "💡 如果步骤 3 和 4 都失败，说明容器无法访问服务器"
echo "   可能是 Docker 网络或防火墙问题"
echo ""
echo "   解决方案："
echo "   1. 检查 Mac 防火墙设置"
echo "   2. 检查 Docker 网络配置"
echo "   3. 尝试使用 host 网络模式"
echo "============================================================"
