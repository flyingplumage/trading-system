#!/usr/bin/env python3
"""
SQLite 写入队列
- 序列化写入操作
- 线程安全
- 超时处理
"""

import sqlite3
import threading
import queue
import time
from typing import Any, Callable, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from .connection_pool import get_write_pool


@dataclass
class WriteOperation:
    """写入操作封装"""
    operation_id: str
    func: Callable
    args: tuple
    kwargs: dict
    result_queue: queue.Queue
    created_at: float
    timeout: float
    
    def is_expired(self) -> bool:
        """检查操作是否超时"""
        return time.time() - self.created_at > self.timeout


class WriteQueue:
    """
    写入队列管理器
    
    所有写入操作序列化执行，避免 SQLite 并发写入冲突
    """
    
    def __init__(self, max_queue_size: int = 1000, 
                 batch_size: int = 10,
                 flush_interval: float = 1.0):
        """
        初始化写入队列
        
        Args:
            max_queue_size: 队列最大容量
            batch_size: 批量处理大小
            flush_interval: 强制刷新间隔（秒）
        """
        self.max_queue_size = max_queue_size
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # 写入队列
        self._queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        
        # 工作线程
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._started = False
        
        # 统计信息
        self._stats = {
            'total_submitted': 0,
            'total_processed': 0,
            'total_failed': 0,
            'total_timeout': 0,
            'queue_size': 0,
            'last_flush': None
        }
        
        # 锁
        self._lock = threading.Lock()
        
        logger.info(f"[WriteQueue] 初始化：max_size={max_queue_size}, batch={batch_size}")
    
    def start(self):
        """启动工作线程"""
        if self._started:
            logger.warning("[WriteQueue] 已经在运行")
            return
        
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        self._started = True
        
        logger.info("[WriteQueue] 工作线程已启动")
    
    def stop(self, wait: bool = True, timeout: float = 5.0):
        """停止工作线程"""
        logger.info("[WriteQueue] 停止工作线程...")
        
        self._stop_event.set()
        
        if wait and self._worker_thread:
            self._worker_thread.join(timeout=timeout)
        
        self._started = False
        logger.info("[WriteQueue] 工作线程已停止")
    
    def submit(self, func: Callable, args: tuple = (), kwargs: dict = None,
               timeout: float = 30.0, operation_id: str = None) -> queue.Queue:
        """
        提交写入操作
        
        Args:
            func: 写入函数
            args: 函数参数
            kwargs: 关键字参数
            timeout: 操作超时时间
            operation_id: 操作 ID（可选）
        
        Returns:
            结果队列（用于获取执行结果）
        
        Raises:
            queue.Full: 队列已满
        """
        if kwargs is None:
            kwargs = {}
        
        result_queue = queue.Queue()
        
        if operation_id is None:
            operation_id = f"op_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        operation = WriteOperation(
            operation_id=operation_id,
            func=func,
            args=args,
            kwargs=kwargs,
            result_queue=result_queue,
            created_at=time.time(),
            timeout=timeout
        )
        
        # 放入队列（阻塞直到有空间）
        self._queue.put(operation, block=True, timeout=timeout)
        
        with self._lock:
            self._stats['total_submitted'] += 1
            self._stats['queue_size'] = self._queue.qsize()
        
        logger.debug(f"[WriteQueue] 提交操作：{operation_id}, 队列大小：{self._stats['queue_size']}")
        
        return result_queue
    
    def submit_sync(self, func: Callable, args: tuple = (), kwargs: dict = None,
                    timeout: float = 30.0) -> Any:
        """
        同步提交写入操作（等待结果）
        
        Args:
            func: 写入函数
            args: 函数参数
            kwargs: 关键字参数
            timeout: 操作超时时间
        
        Returns:
            函数执行结果
        
        Raises:
            TimeoutError: 操作超时
            Exception: 执行异常
        """
        result_queue = self.submit(func, args, kwargs, timeout)
        
        # 等待结果
        try:
            result = result_queue.get(timeout=timeout)
            
            if isinstance(result, Exception):
                raise result
            
            return result
            
        except queue.Empty:
            with self._lock:
                self._stats['total_timeout'] += 1
            raise TimeoutError(f"写入操作超时 ({timeout}s)")
    
    def _worker_loop(self):
        """工作线程主循环"""
        logger.info("[WriteQueue] 工作线程开始运行")
        
        batch = []
        last_flush = time.time()
        
        while not self._stop_event.is_set():
            try:
                # 尝试获取操作（非阻塞）
                try:
                    operation = self._queue.get(timeout=0.1)
                    batch.append(operation)
                except queue.Empty:
                    operation = None
                
                # 检查是否需要刷新
                now = time.time()
                should_flush = (
                    len(batch) >= self.batch_size or
                    (batch and now - last_flush >= self.flush_interval) or
                    self._stop_event.is_set()
                )
                
                if should_flush and batch:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = now
                    
                    with self._lock:
                        self._stats['last_flush'] = datetime.now().isoformat()
                        self._stats['queue_size'] = self._queue.qsize()
                
            except Exception as e:
                logger.error(f"[WriteQueue] 工作线程错误：{e}")
                # 清空当前批次
                for op in batch:
                    op.result_queue.put_nowait(e)
                batch = []
        
        # 处理剩余操作
        if batch:
            logger.info(f"[WriteQueue] 处理剩余 {len(batch)} 个操作...")
            self._flush_batch(batch)
        
        logger.info("[WriteQueue] 工作线程退出")
    
    def _flush_batch(self, batch: list):
        """批量处理写入操作"""
        logger.debug(f"[WriteQueue] 处理批次：{len(batch)} 个操作")
        
        # 获取数据库连接
        pool = get_write_pool()
        conn = pool.acquire(timeout=5.0)
        
        try:
            for operation in batch:
                # 检查是否超时
                if operation.is_expired():
                    operation.result_queue.put_nowait(
                        TimeoutError(f"操作超时：{operation.operation_id}")
                    )
                    with self._lock:
                        self._stats['total_timeout'] += 1
                    continue
                
                try:
                    # 执行写入操作
                    result = operation.func(conn, *operation.args, **operation.kwargs)
                    operation.result_queue.put_nowait(result)
                    
                    with self._lock:
                        self._stats['total_processed'] += 1
                        
                except Exception as e:
                    logger.error(f"[WriteQueue] 操作失败 {operation.operation_id}: {e}")
                    operation.result_queue.put_nowait(e)
                    
                    with self._lock:
                        self._stats['total_failed'] += 1
            
            # 提交事务
            conn.commit()
            
        except Exception as e:
            logger.error(f"[WriteQueue] 批次处理失败：{e}")
            conn.rollback()
            
            # 通知所有操作失败
            for operation in batch:
                operation.result_queue.put_nowait(e)
        
        finally:
            pool.release(conn)
    
    def get_stats(self) -> dict:
        """获取队列统计信息"""
        with self._lock:
            stats = self._stats.copy()
            stats['is_running'] = self._started
            stats['worker_alive'] = self._worker_thread.is_alive() if self._worker_thread else False
            return stats
    
    def clear(self):
        """清空队列"""
        logger.info("[WriteQueue] 清空队列...")
        
        cleared = 0
        while True:
            try:
                operation = self._queue.get_nowait()
                operation.result_queue.put_nowait(
                    Exception("队列已清空")
                )
                cleared += 1
            except queue.Empty:
                break
        
        logger.info(f"[WriteQueue] 已清空 {cleared} 个操作")
        return cleared


# 全局写入队列实例
_write_queue: Optional[WriteQueue] = None


def get_write_queue() -> WriteQueue:
    """获取全局写入队列"""
    global _write_queue
    if _write_queue is None:
        _write_queue = WriteQueue()
        _write_queue.start()
    return _write_queue


def submit_write(func: Callable, args: tuple = (), kwargs: dict = None,
                 timeout: float = 30.0) -> queue.Queue:
    """
    提交写入操作（便捷函数）
    
    Usage:
        result_queue = submit_write(my_write_func, args=(arg1,))
        result = result_queue.get()
    """
    return get_write_queue().submit(func, args, kwargs, timeout)


def execute_write_sync(func: Callable, args: tuple = (), kwargs: dict = None,
                       timeout: float = 30.0) -> Any:
    """
    同步执行写入操作（便捷函数）
    
    Usage:
        result = execute_write_sync(my_write_func, args=(arg1,))
    """
    return get_write_queue().submit_sync(func, args, kwargs, timeout)


def stop_write_queue():
    """停止写入队列"""
    global _write_queue
    if _write_queue:
        _write_queue.stop()
        _write_queue = None


# 自动启动（模块导入时）
get_write_queue()
logger.info("✅ 写入队列模块加载完成")
