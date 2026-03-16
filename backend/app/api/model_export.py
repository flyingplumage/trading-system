"""
模型导出 API
支持 ONNX、TorchScript 等格式导出
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.schemas.schemas import Response
from app.services.model_export import model_exporter
from app.api.dependencies import require_model_read, require_model_create

router = APIRouter(prefix="/api/models/export", tags=["models-export"])


@router.post("/onnx", response_model=Response)
async def export_to_onnx(
    model_id: str,
    output_name: Optional[str] = None,
    opset_version: int = 11,
    current_user: dict = Depends(require_model_create)
):
    """
    导出模型为 ONNX 格式
    
    Args:
        model_id: 模型 ID
        output_name: 输出文件名 (可选)
        opset_version: ONNX opset 版本 (默认 11)
    """
    try:
        from app.services.model import model_service
        
        # 获取模型路径
        model_info = model_service.get_model(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        model_path = model_info.get('file_path')
        if not model_path:
            raise HTTPException(status_code=404, detail="模型文件不存在")
        
        # 导出
        export_info = model_exporter.export_to_onnx(
            model_path=model_path,
            output_name=output_name,
            opset_version=opset_version
        )
        
        return Response(
            success=True,
            message="模型已导出为 ONNX 格式",
            data=export_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/torchscript", response_model=Response)
async def export_to_torchscript(
    model_id: str,
    output_name: Optional[str] = None,
    current_user: dict = Depends(require_model_create)
):
    """
    导出模型为 TorchScript 格式
    
    Args:
        model_id: 模型 ID
        output_name: 输出文件名 (可选)
    """
    try:
        from app.services.model import model_service
        
        # 获取模型路径
        model_info = model_service.get_model(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        model_path = model_info.get('file_path')
        if not model_path:
            raise HTTPException(status_code=404, detail="模型文件不存在")
        
        # 导出
        export_info = model_exporter.export_to_torchscript(
            model_path=model_path,
            output_name=output_name
        )
        
        return Response(
            success=True,
            message="模型已导出为 TorchScript 格式",
            data=export_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=Response)
async def list_exports(current_user: dict = Depends(require_model_read)):
    """列出所有导出的模型"""
    exports = model_exporter.list_exports()
    
    return Response(
        success=True,
        message="OK",
        data=exports
    )
