#!/usr/bin/env python3
"""
SQLite 连接池管理
- 连接池管理（最大 10 连接）
- 上下文管理器
- 读写分离支持
"""

import sqlite3
import threading
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from queue import Queue, Empty
import logging

logger = logging.getLogger(__name__)

# 数据库路径
DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "qframe.db"


class SQLiteConnectionPool:
    """SQLite 连接池管理器"""
    
    def __init__(self, db_path: str = None, max_connections: int = 10, 
                 pool_name: str = "default"):
        """
        初始化连接池
        
        Args:
            db_path: 数据库文件路径
            max_connections: 最大连接数
            pool_name: 连接池名称
        """
        self.db_path = str(db_path) if db_path else str(DATABASE_PATH)
        self.max_connections = max_connections
        self.pool_name = pool_name
        
        # 确保数据库目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 连接池
        self._pool: Queue = Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._created_connections = 0
        
        # 统计信息
        self._stats = {
            'total_created': 0,
            'total_acquired': 0,
            'total_released': 0,
            'current_active': 0,
            'max_active': 0
        }
        
        logger.info(f"[ConnectionPool] 初始化：{pool_name}, max={max_connections}, db={self.db_path}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """创建新的数据库连接"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,  # 允许跨线程使用（由池管理）
            timeout=30.0              # 锁等待超时 30 秒
        )
        
        # 优化配置
        self._configure_connection(conn)
        
        with self._lock:
            self._created_connections += 1
            self._stats['total_created'] += 1
        
        logger.debug(f"[ConnectionPool] 创建新连接，总创建数：{self._created_connections}")
        return conn
    
    def _configure_connection(self, conn: sqlite3.Connection):
        """配置连接优化参数"""
        cursor = conn.cursor()
        
        # 启用 WAL 模式（只需执行一次，后续连接会继承）
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # 优化配置
        cursor.execute("PRAGMA synchronous=NORMAL")  # 平衡性能和安全性
        cursor.execute("PRAGMA cache_size=-64000")   # 64MB 缓存
        cursor.execute("PRAGMA temp_store=MEMORY")   # 临时表存内存
        cursor.execute("PRAGMA foreign_keys=ON")     # 启用外键
        
        cursor.close()
        
        logger.debug(f"[ConnectionPool] 连接配置完成 (WAL 模式)")
    
    def acquire(self, timeout: float = 5.0) -> sqlite3.Connection:
        """
        获取连接
        
        Args:
            timeout: 等待超时时间（秒）
        
        Returns:
            sqlite3 连接对象
        
        Raises:
            TimeoutError: 获取连接超时
        """
        try:
            # 尝试从池中获取
            conn = self._pool.get_nowait()
            
            # 检查连接是否有效
            if not self._is_connection_valid(conn):
                conn.close()
                conn = self._create_connection()
            
        except Empty:
            # 池为空，尝试创建新连接
            with self._lock:
                if self._created_connections < self.max_connections:
                    conn = self._create_connection()
                else:
                    # 达到最大连接数，等待
                    logger.debug(f"[ConnectionPool] 连接池满，等待可用连接...")
                    try:
                        conn = self._pool.get(timeout=timeout)
                        if not self._is_connection_valid(conn):
                            conn.close()
                            conn = self._create_connection()
                    except Empty:
                        raise TimeoutError(
                            f"获取数据库连接超时 ({timeout}s), "
                            f"池大小：{self.max_connections}, "
                            f"活跃：{self._stats['current_active']}"
                        )
        
        # 更新统计
        with self._lock:
            self._stats['total_acquired'] += 1
            self._stats['current_active'] += 1
            if self._stats['current_active'] > self._stats['max_active']:
                self._stats['max_active'] = self._stats['current_active']
        
        logger.debug(f"[ConnectionPool] 获取连接，活跃：{self._stats['current_active']}/{self.max_connections}")
        return conn
    
    def release(self, conn: sqlite3.Connection):
        """
        释放连接回池
        
        Args:
            conn: 要释放的连接
        """
        if conn is None:
            return
        
        try:
            # 检查连接是否有效
            if self._is_connection_valid(conn):
                # 回滚未提交的事务
                try:
                    conn.rollback()
                except:
                    pass
                
                # 归还到池中
                try:
                    self._pool.put_nowait(conn)
                except:
                    # 池满，关闭连接
                    conn.close()
                    with self._lock:
                        self._created_connections -= 1
            else:
                # 连接无效，关闭
                conn.close()
                with self._lock:
                    self._created_connections -= 1
            
            # 更新统计
            with self._lock:
                self._stats['total_released'] += 1
                self._stats['current_active'] -= 1
            
            logger.debug(f"[ConnectionPool] 释放连接，活跃：{self._stats['current_active']}/{self.max_connections}")
            
        except Exception as e:
            logger.error(f"[ConnectionPool] 释放连接失败：{e}")
    
    def _is_connection_valid(self, conn: sqlite3.Connection) -> bool:
        """检查连接是否有效"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
            return False
    
    def get_stats(self) -> dict:
        """获取连接池统计信息"""
        with self._lock:
            return self._stats.copy()
    
    def close_all(self):
        """关闭所有连接"""
        logger.info(f"[ConnectionPool] 关闭所有连接...")
        
        closed_count = 0
        while True:
            try:
                conn = self._pool.get_nowait()
                conn.close()
                closed_count += 1
            except Empty:
                break
        
        logger.info(f"[ConnectionPool] 已关闭 {closed_count} 个连接")
    
    @contextmanager
    def connection(self, timeout: float = 5.0):
        """
        上下文管理器获取连接
        
        Usage:
            with pool.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        conn = self.acquire(timeout=timeout)
        try:
            yield conn
        finally:
            self.release(conn)


# 全局连接池实例
_read_pool: Optional[SQLiteConnectionPool] = None
_write_pool: Optional[SQLiteConnectionPool] = None


def get_read_pool(max_connections: int = 10) -> SQLiteConnectionPool:
    """获取读连接池"""
    global _read_pool
    if _read_pool is None:
        _read_pool = SQLiteConnectionPool(pool_name="read", max_connections=max_connections)
    return _read_pool


def get_write_pool(max_connections: int = 5) -> SQLiteConnectionPool:
    """获取写连接池"""
    global _write_pool
    if _write_pool is None:
        _write_pool = SQLiteConnectionPool(pool_name="write", max_connections=max_connections)
    return _write_pool


@contextmanager
def get_db_connection(read_only: bool = False, timeout: float = 5.0):
    """
    获取数据库连接（上下文管理器）
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    
    Args:
        read_only: 是否只读连接（使用读池）
        timeout: 获取连接超时时间
    """
    if read_only:
        pool = get_read_pool()
    else:
        pool = get_write_pool()
    
    conn = pool.acquire(timeout=timeout)
    try:
        yield conn
    finally:
        pool.release(conn)


def init_pools(read_pool_size: int = 10, write_pool_size: int = 5):
    """初始化连接池"""
    global _read_pool, _write_pool
    _read_pool = SQLiteConnectionPool(pool_name="read", max_connections=read_pool_size)
    _write_pool = SQLiteConnectionPool(pool_name="write", max_connections=write_pool_size)
    logger.info(f"[ConnectionPool] 连接池初始化完成 (读：{read_pool_size}, 写：{write_pool_size})")


def close_pools():
    """关闭所有连接池"""
    if _read_pool:
        _read_pool.close_all()
    if _write_pool:
        _write_pool.close_all()


# 懒加载：在首次使用时初始化
# 移除自动初始化，避免模块导入时阻塞
# init_pools()
# logger.info("✅ 连接池模块加载完成")
