"""
PostgreSQL 数据库连接配置
使用 SQLAlchemy 异步连接池
"""

import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy import create_engine

# 数据库 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://quant:quant_password_2024@localhost:5432/qframe"
)

ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    "postgresql+asyncpg://quant:quant_password_2024@localhost:5432/qframe"
)

# 同步引擎（用于 Alembic 迁移等）
sync_engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# 异步引擎（用于 FastAPI 应用）
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Session 工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

SessionLocal = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base 模型
Base = declarative_base()


# 依赖注入：获取异步数据库会话
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖注入：获取数据库会话
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 依赖注入：获取同步数据库会话
def get_db_sync() -> Generator[Session, None, None]:
    """
    FastAPI 依赖注入：获取同步数据库会话
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# 初始化数据库表
async def init_db():
    """
    初始化数据库表（异步）
    
    Usage:
        @app.on_event("startup")
        async def startup():
            await init_db()
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_db_sync():
    """
    初始化数据库表（同步）
    """
    Base.metadata.create_all(bind=sync_engine)


# 健康检查
async def check_db_health() -> bool:
    """
    检查数据库连接健康状态
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception:
        return False


# 关闭连接池
async def close_db():
    """
    关闭数据库连接池
    
    Usage:
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
    """
    await async_engine.dispose()


def close_db_sync():
    """
    关闭同步数据库连接池
    """
    sync_engine.dispose()
