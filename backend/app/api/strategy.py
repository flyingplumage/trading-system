"""策略管理 API"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import os
import tempfile
from app.schemas.schemas import Response
from app.strategy.uploader import StrategyUploader
from app.strategy.pipeline import StrategyPipeline

router = APIRouter(prefix="/api/strategy", tags=["strategy"])

uploader = StrategyUploader()

@router.post("/upload", response_model=Response)
async def upload_strategy(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form("")
):
    """上传策略包"""
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # 上传策略
        metadata = uploader.upload(tmp_path, name, description)
        
        # 清理临时文件
        os.unlink(tmp_path)
        
        return Response(
            success=True,
            message="策略上传成功",
            data=metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=Response)
async def list_strategies():
    """列出所有策略"""
    strategies = uploader.list_strategies()
    return Response(success=True, message="OK", data=strategies)

@router.get("/{strategy_id}", response_model=Response)
async def get_strategy(strategy_id: str):
    """获取策略详情"""
    strategy = uploader.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    return Response(success=True, message="OK", data=strategy)

@router.post("/{strategy_id}/execute", response_model=Response)
async def execute_strategy(
    strategy_id: str,
    exp_id: str = Form(...),
    task_id: int = Form(...),
    steps: int = Form(100000)
):
    """执行策略 Pipeline"""
    try:
        strategy = uploader.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        strategy_dir = uploader.upload_dir / strategy_id
        
        # 创建 Pipeline
        pipeline = StrategyPipeline(strategy_id, str(strategy_dir))
        
        # 执行 Pipeline (后台任务)
        from app.db import database
        from datetime import datetime
        
        def run_pipeline():
            pipeline.execute(exp_id, task_id, steps)
        
        import threading
        thread = threading.Thread(target=run_pipeline)
        thread.start()
        
        return Response(
            success=True,
            message="策略 Pipeline 已启动",
            data={'strategy_id': strategy_id, 'stages': ['training', 'backtest', 'optimization']}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
