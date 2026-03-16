"""
K 线形态分析 API
识别和统计 K 线形态模式
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.schemas.schemas import Response
from app.services.candlestick import candlestick_pattern
from app.services.data import DataService
from app.api.dependencies import require_data_read

router = APIRouter(prefix="/api/analysis/candlestick", tags=["analysis"])

data_service = DataService()


@router.get("/patterns", response_model=Response)
async def detect_patterns(
    stock_code: str,
    limit: int = Query(default=100, ge=10, le=1000),
    current_user: dict = Depends(require_data_read)
):
    """
    检测 K 线形态
    
    Args:
        stock_code: 股票代码
        limit: 数据条数
    """
    try:
        # 获取股票数据
        df = data_service.get_price_data(stock_code)
        if df is None or len(df) == 0:
            raise HTTPException(status_code=404, detail="股票数据不存在")
        
        # 限制数据量
        df = df.tail(limit).reset_index(drop=True)
        
        # 检测形态
        result = candlestick_pattern.detect_all(df)
        
        # 获取最近的数据和形态信号
        recent_data = result.tail(20).to_dict('records')
        
        # 获取形态统计
        summary = candlestick_pattern.get_pattern_summary(result)
        
        return Response(
            success=True,
            message="形态检测完成",
            data={
                'stock_code': stock_code,
                'data_points': len(result),
                'recent_signals': recent_data,
                'pattern_summary': summary
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=Response)
async def get_pattern_summary(
    stock_code: str,
    window: int = Query(default=100, ge=10, le=1000),
    current_user: dict = Depends(require_data_read)
):
    """
    获取形态统计摘要
    
    Args:
        stock_code: 股票代码
        window: 统计窗口
    """
    try:
        # 获取股票数据
        df = data_service.get_price_data(stock_code)
        if df is None or len(df) == 0:
            raise HTTPException(status_code=404, detail="股票数据不存在")
        
        # 检测形态
        result = candlestick_pattern.detect_all(df)
        
        # 获取统计
        summary = candlestick_pattern.get_pattern_summary(result, window)
        
        return Response(
            success=True,
            message="OK",
            data={
                'stock_code': stock_code,
                'window': window,
                'summary': summary
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=Response)
async def search_patterns(
    pattern_name: str,
    stock_code: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
    current_user: dict = Depends(require_data_read)
):
    """
    搜索特定形态
    
    Args:
        pattern_name: 形态名称 (hammer, doji, engulfing_bull 等)
        stock_code: 股票代码 (可选，不传则搜索所有股票)
        limit: 结果数量限制
    """
    try:
        if pattern_name not in candlestick_pattern.patterns:
            raise HTTPException(
                status_code=400,
                detail=f"未知的形态：{pattern_name}。支持的形态：{list(candlestick_pattern.patterns.keys())}"
            )
        
        results = []
        
        if stock_code:
            # 搜索单只股票
            df = data_service.get_price_data(stock_code)
            if df is not None and len(df) > 0:
                result = candlestick_pattern.detect_all(df)
                pattern_col = f'pattern_{pattern_name}'
                
                if pattern_col in result.columns:
                    signals = result[result[pattern_col] == 1].tail(limit)
                    for idx, row in signals.iterrows():
                        results.append({
                            'stock_code': stock_code,
                            'date': row.get('trade_date', idx),
                            'close': row['close'],
                            'pattern': pattern_name
                        })
        else:
            # 搜索所有股票
            stocks = data_service.get_stock_list()
            for stock in stocks[:10]:  # 限制搜索 10 只股票
                stock_code = stock.get('ts_code') or stock.get('code')
                if stock_code:
                    df = data_service.get_price_data(stock_code)
                    if df is not None and len(df) > 0:
                        result = candlestick_pattern.detect_all(df)
                        pattern_col = f'pattern_{pattern_name}'
                        
                        if pattern_col in result.columns:
                            signals = result[result[pattern_col] == 1].tail(5)
                            for idx, row in signals.iterrows():
                                results.append({
                                    'stock_code': stock_code,
                                    'date': row.get('trade_date', idx),
                                    'close': row['close'],
                                    'pattern': pattern_name
                                })
        
        return Response(
            success=True,
            message=f"找到 {len(results)} 个 {pattern_name} 形态",
            data={
                'pattern': pattern_name,
                'count': len(results),
                'signals': results
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/list", response_model=Response)
async def list_patterns(current_user: dict = Depends(require_data_read)):
    """列出所有支持的 K 线形态"""
    patterns = {
        'hammer': {
            'name': '锤子线',
            'type': 'bullish_reversal',
            'description': '底部反转信号，下影线长，实体小'
        },
        'shooting_star': {
            'name': '流星线',
            'type': 'bearish_reversal',
            'description': '顶部反转信号，上影线长，实体小'
        },
        'engulfing_bull': {
            'name': '看涨吞并',
            'type': 'bullish_reversal',
            'description': '阳线吞并前一根阴线实体'
        },
        'engulfing_bear': {
            'name': '看跌吞并',
            'type': 'bearish_reversal',
            'description': '阴线吞并前一根阳线实体'
        },
        'doji': {
            'name': '十字星',
            'type': 'neutral',
            'description': '开盘价等于收盘价，市场犹豫'
        },
        'morning_star': {
            'name': '早晨之星',
            'type': 'bullish_reversal',
            'description': '三根 K 线组成的底部反转形态'
        },
        'evening_star': {
            'name': '黄昏之星',
            'type': 'bearish_reversal',
            'description': '三根 K 线组成的顶部反转形态'
        },
        'three_white_soldiers': {
            'name': '三白兵',
            'type': 'bullish_continuation',
            'description': '连续三根阳线，强势上涨'
        },
        'three_black_crows': {
            'name': '三乌鸦',
            'type': 'bearish_continuation',
            'description': '连续三根阴线，强势下跌'
        }
    }
    
    return Response(
        success=True,
        message="OK",
        data={
            'total_patterns': len(patterns),
            'patterns': patterns
        }
    )
