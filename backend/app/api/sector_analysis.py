"""
板块分析 API
分析行业板块、概念板块的表现
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from app.schemas.schemas import Response
from app.services.sector import sector_analyzer
from app.api.dependencies import require_data_read

router = APIRouter(prefix="/api/analysis/sector", tags=["analysis"])


@router.get("/list", response_model=Response)
async def get_sector_list(
    sector_type: str = Query(default='industry', enum=['industry', 'concept', 'region']),
    current_user: dict = Depends(require_data_read)
):
    """
    获取板块列表
    
    Args:
        sector_type: 板块类型 (industry=行业/concept=概念/region=地区)
    """
    sectors = sector_analyzer.get_sector_list(sector_type)
    
    return Response(
        success=True,
        message="OK",
        data={
            'sector_type': sector_type,
            'type_name': sector_analyzer.sector_types.get(sector_type, ''),
            'count': len(sectors),
            'sectors': sectors
        }
    )


@router.get("/{sector_code}/stocks", response_model=Response)
async def get_sector_stocks(
    sector_code: str,
    current_user: dict = Depends(require_data_read)
):
    """
    获取板块成分股
    
    Args:
        sector_code: 板块代码
    """
    stocks = sector_analyzer.get_sector_stocks(sector_code)
    
    return Response(
        success=True,
        message="OK",
        data={
            'sector_code': sector_code,
            'stock_count': len(stocks),
            'stocks': stocks
        }
    )


@router.get("/{sector_code}/performance", response_model=Response)
async def get_sector_performance(
    sector_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_data_read)
):
    """
    分析板块表现
    
    Args:
        sector_code: 板块代码
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
    """
    performance = sector_analyzer.analyze_sector_performance(
        sector_code=sector_code,
        start_date=start_date,
        end_date=end_date
    )
    
    return Response(
        success=True,
        message="板块表现分析完成",
        data=performance
    )


@router.get("/ranking", response_model=Response)
async def get_sector_ranking(
    sector_type: str = Query(default='industry', enum=['industry', 'concept', 'region']),
    metric: str = Query(default='return_1d', enum=['return_1d', 'return_5d', 'return_20d', 'volume_ratio']),
    top_n: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(require_data_read)
):
    """
    获取板块排名
    
    Args:
        sector_type: 板块类型
        metric: 排名指标
        top_n: 返回前 N 个
    """
    ranking = sector_analyzer.get_sector_ranking(
        sector_type=sector_type,
        metric=metric,
        top_n=top_n
    )
    
    return Response(
        success=True,
        message="板块排名",
        data={
            'sector_type': sector_type,
            'metric': metric,
            'top_n': top_n,
            'ranking': ranking
        }
    )


@router.get("/correlation", response_model=Response)
async def get_sector_correlation(
    sectors: str = Query(..., description="板块代码列表，逗号分隔"),
    window: int = Query(default=20, ge=5, le=100),
    current_user: dict = Depends(require_data_read)
):
    """
    计算板块相关性
    
    Args:
        sectors: 板块代码列表 (逗号分隔)
        window: 计算窗口
    """
    sector_codes = [s.strip() for s in sectors.split(',')]
    
    if len(sector_codes) < 2:
        raise HTTPException(status_code=400, detail="至少需要 2 个板块")
    
    correlation = sector_analyzer.get_sector_correlation(
        sector_codes=sector_codes,
        window=window
    )
    
    return Response(
        success=True,
        message="相关性分析完成",
        data=correlation
    )


@router.get("/rotation", response_model=Response)
async def get_sector_rotation(
    window: int = Query(default=5, ge=1, le=20),
    current_user: dict = Depends(require_data_read)
):
    """
    获取板块轮动分析
    
    Args:
        window: 分析窗口 (天)
    """
    rotation = sector_analyzer.get_sector_rotation(window=window)
    
    return Response(
        success=True,
        message="板块轮动分析完成",
        data=rotation
    )


@router.get("/hot", response_model=Response)
async def get_hot_sectors(
    top_n: int = Query(default=5, ge=1, le=20),
    current_user: dict = Depends(require_data_read)
):
    """
    获取热门板块
    
    Args:
        top_n: 返回前 N 个热门板块
    """
    ranking = sector_analyzer.get_sector_ranking(
        sector_type='industry',
        metric='return_5d',
        top_n=top_n
    )
    
    return Response(
        success=True,
        message="热门板块",
        data={
            'hot_sectors': ranking,
            'metric': 'return_5d'
        }
    )
