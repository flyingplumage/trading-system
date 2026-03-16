"""
WebSocket 管理器
实时推送训练进度、系统状态等
"""

import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket
import threading
import time


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscribed_topics: Dict[WebSocket, Set[str]] = {}
        self.lock = threading.Lock()
    
    async def connect(self, websocket: WebSocket):
        """接受 WebSocket 连接"""
        await websocket.accept()
        with self.lock:
            self.active_connections.add(websocket)
            self.subscribed_topics[websocket] = set()
        print(f"[WebSocket] 新连接，当前连接数：{len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        with self.lock:
            self.active_connections.discard(websocket)
            self.subscribed_topics.pop(websocket, None)
        print(f"[WebSocket] 连接断开，当前连接数：{len(self.active_connections)}")
    
    def subscribe(self, websocket: WebSocket, topics: List[str]):
        """订阅主题"""
        with self.lock:
            if websocket in self.subscribed_topics:
                self.subscribed_topics[websocket].update(topics)
    
    def unsubscribe(self, websocket: WebSocket, topics: List[str]):
        """取消订阅主题"""
        with self.lock:
            if websocket in self.subscribed_topics:
                self.subscribed_topics[websocket] -= set(topics)
    
    async def broadcast(self, message: dict, topic: str = None):
        """
        广播消息
        
        Args:
            message: 消息内容
            topic: 主题 (None 则广播给所有连接)
        """
        message['topic'] = topic
        message['timestamp'] = time.time()
        message_json = json.dumps(message)
        
        disconnected = set()
        
        with self.lock:
            for connection in self.active_connections.copy():
                # 如果没有指定主题，或连接订阅了该主题
                if topic is None or topic in self.subscribed_topics.get(connection, set()):
                    try:
                        await connection.send_text(message_json)
                    except Exception as e:
                        print(f"[WebSocket] 发送失败：{e}")
                        disconnected.add(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """发送个人消息"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"[WebSocket] 个人消息发送失败：{e}")
            self.disconnect(websocket)


# 全局管理器实例
manager = ConnectionManager()


class TrainingProgressBroadcaster:
    """训练进度广播器"""
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.running = False
        self.thread = None
    
    def start(self):
        """启动广播器"""
        if self.thread and self.thread.is_alive():
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止广播器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _broadcast_loop(self):
        """广播循环"""
        # 这里可以定期检查并广播系统状态
        while self.running:
            time.sleep(10)  # 每 10 秒广播一次心跳
    
    async def broadcast_training_progress(self, task_id: int, progress: float, metrics: dict):
        """广播训练进度"""
        await self.manager.broadcast(
            {
                'type': 'training_progress',
                'task_id': task_id,
                'progress': progress,
                'metrics': metrics
            },
            topic='training'
        )
    
    async def broadcast_training_complete(self, task_id: int, result: dict):
        """广播训练完成"""
        await self.manager.broadcast(
            {
                'type': 'training_complete',
                'task_id': task_id,
                'result': result
            },
            topic='training'
        )
    
    async def broadcast_training_failed(self, task_id: int, error: str):
        """广播训练失败"""
        await self.manager.broadcast(
            {
                'type': 'training_failed',
                'task_id': task_id,
                'error': error
            },
            topic='training'
        )


# 全局广播器实例
broadcaster = TrainingProgressBroadcaster(manager)
