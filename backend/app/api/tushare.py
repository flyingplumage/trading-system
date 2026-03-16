"""Tushare 数据管理 API"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from app.schemas.schemas import Response
from app.services.tushare_service import get_tushare_service

router = APIRouter(prefix="/api/tushare", tags=["tushare"])


@router.get("/status", response_model=Response)
async def get_tushare_status():
    """获取 Tushare 服务状态"""
    try:
        service = get_tushare_service()
        summary = service.get_data_summary()
        
        return Response(
            success=True,
            message="OK",
            data={
                'status': 'running',
                **summary
            }
        )
    except Exception as e:
        return Response(success=False, message=str(e), data={})


@router.post("/pool/update", response_model=Response)
async def update_stock_pool():
    """更新股票池"""
    try:
        service = get_tushare_service()
        stock_list = service.update_stock_pool()
        
        return Response(
            success=True,
            message=f"股票池更新完成，共 {len(stock_list)} 只股票",
            data={'count': len(stock_list)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pool", response_model=Response)
async def get_stock_pool():
    """获取股票池"""
    try:
        import yaml
        from pathlib import Path
        
        pool_file = Path(__file__).parent.parent.parent / "shared" / "data" / "pool" / "stock_pool.yaml"
        
        if not pool_file.exists():
            return Response(success=True, message="股票池为空", data={'stocks': []})
        
        with open(pool_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return Response(
            success=True,
            message="OK",
            data=config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/{ts_code}", response_model=Response)
async def update_stock(ts_code: str):
    """更新单只股票数据"""
    try:
        service = get_tushare_service()
        count = service.incremental_update(ts_code)
        
        return Response(
            success=True,
            message=f"更新完成：{ts_code}",
            data={'ts_code': ts_code, 'new_records': count}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/all", response_model=Response)
async def update_all_stocks(background_tasks: BackgroundTasks, limit: Optional[int] = None):
    """批量更新所有股票（后台任务）"""
    try:
        service = get_tushare_service()
        
        # 后台执行
        def run_update():
            stats = service.update_all_stocks(limit=limit)
            print(f"[API] 批量更新完成：{stats}")
        
        background_tasks.add_task(run_update)
        
        return Response(
            success=True,
            message="批量更新已启动（后台任务）",
            data={'limit': limit}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
