"""
WebSocket API
实时推送训练进度、系统状态
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import List, Optional
from app.services.websocket_manager import manager, broadcaster
import json

router = APIRouter(tags=["websocket"])

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    topics: str = Query(default="", description="订阅的主题，逗号分隔 (training,system,backtest)")
):
    """
    WebSocket 连接端点
    
    订阅主题:
    - training: 训练进度
    - system: 系统状态
    - backtest: 回测结果
    """
    await manager.connect(websocket)
    
    # 解析订阅主题
    topic_list = [t.strip() for t in topics.split(',') if t.strip()]
    if topic_list:
        manager.subscribe(websocket, topic_list)
        await manager.send_personal(
            websocket,
            {
                'type': 'connected',
                'topics': topic_list,
                'message': f'已订阅主题：{", ".join(topic_list)}'
            }
        )
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get('type')
                
                if msg_type == 'subscribe':
                    # 订阅主题
                    new_topics = message.get('topics', [])
                    manager.subscribe(websocket, new_topics)
                    await manager.send_personal(
                        websocket,
                        {
                            'type': 'subscribed',
                            'topics': list(manager.subscribed_topics.get(websocket, set()))
                        }
                    )
                
                elif msg_type == 'unsubscribe':
                    # 取消订阅
                    remove_topics = message.get('topics', [])
                    manager.unsubscribe(websocket, remove_topics)
                    await manager.send_personal(
                        websocket,
                        {
                            'type': 'unsubscribed',
                            'topics': list(manager.subscribed_topics.get(websocket, set()))
                        }
                    )
                
                elif msg_type == 'ping':
                    # 心跳
                    await manager.send_personal(
                        websocket,
                        {'type': 'pong', 'timestamp': message.get('timestamp')}
                    )
                
            except json.JSONDecodeError:
                await manager.send_personal(
                    websocket,
                    {'type': 'error', 'message': '无效的 JSON 格式'}
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"[WebSocket] 客户端断开连接")

@router.get("/ws/info")
async def get_websocket_info():
    """获取 WebSocket 服务信息"""
    return {
        'status': 'running',
        'active_connections': len(manager.active_connections),
        'endpoint': '/ws',
        'topics': ['training', 'system', 'backtest'],
        'example': 'ws://localhost:5000/ws?topics=training,system'
    }
