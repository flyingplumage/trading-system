"""数据服务 API（使用服务层）"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.schemas.schemas import Response
from app.services.data import DataService
from app.services.exceptions import NotFoundError, InternalError
from app.api.dependencies import require_data_read

router = APIRouter(prefix="/api/data", tags=["data"])

# 服务实例
data_service = DataService()


@router.get("/stocks", response_model=Response)
async def get_stock_list(current_user: dict = Depends(require_data_read)):
    """获取股票列表"""
    try:
        stocks = data_service.get_stock_list()
        return Response(success=True, message="OK", data=stocks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price/{stock_code}", response_model=Response)
async def get_price_data(stock_code: str, start_date: str = None, end_date: str = None, current_user: dict = Depends(require_data_read)):
    """获取股票价格数据"""
    try:
        df = data_service.get_price_data(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date
        )
        return Response(success=True, message="OK", data=df.to_dict('records'))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/{stock_code}", response_model=Response)
async def get_feature_data(stock_code: str, start_date: str = None, end_date: str = None, current_user: dict = Depends(require_data_read)):
    """获取特征数据（含技术指标）"""
    try:
        df = data_service.get_price_data(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date
        )
        return Response(success=True, message="OK", data=df.to_dict('records'))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files", response_model=Response)
async def list_data_files(current_user: dict = Depends(require_data_read)):
    """获取数据文件列表"""
    try:
        files = data_service.list()
        return Response(success=True, message="OK", data=files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Response)
async def get_data_stats(current_user: dict = Depends(require_data_read)):
    """获取数据统计"""
    try:
        summary = data_service.get_data_summary()
        
        # 补充统计信息
        files = data_service.list()
        stats = {
            **summary,
            'total_files': len(files),
            'total_size_mb': sum(f.get('size', 0) for f in files) / 1024 / 1024
        }
        
        return Response(success=True, message="OK", data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
