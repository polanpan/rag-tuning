# backend/app/api/config.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from ..core.config import (
    settings, 
    get_database_config, 
    update_database_config, 
    get_db_type_display_name,
    is_milvus_lite
)
from ..services.vector_service import VectorService

router = APIRouter()

class DatabaseConfigResponse(BaseModel):
    """数据库配置响应"""
    db_type: str
    db_type_display: str
    is_lite: bool
    milvus_standard: Optional[Dict[str, Any]] = None
    milvus_lite: Optional[Dict[str, Any]] = None

class DatabaseConfigUpdate(BaseModel):
    """数据库配置更新请求"""
    db_type: Literal["milvus_standard", "milvus_lite"] = Field(..., description="数据库类型")
    milvus_standard: Optional[Dict[str, Any]] = Field(default=None, description="Milvus 标准版配置")
    milvus_lite: Optional[Dict[str, Any]] = Field(default=None, description="Milvus Lite 配置")

class DatabaseTestRequest(BaseModel):
    """数据库连接测试请求"""
    db_type: Literal["milvus_standard", "milvus_lite"]
    config: Dict[str, Any]

@router.get("/config/database", response_model=DatabaseConfigResponse)
async def get_database_config_api():
    """获取当前数据库配置"""
    try:
        db_config = get_database_config()
        
        return DatabaseConfigResponse(
            db_type=db_config.db_type,
            db_type_display=get_db_type_display_name(),
            is_lite=is_milvus_lite(),
            milvus_standard={
                "host": db_config.milvus_standard.host,
                "port": db_config.milvus_standard.port,
                "user": db_config.milvus_standard.user,
                "secure": db_config.milvus_standard.secure,
                "timeout": db_config.milvus_standard.timeout,
            },
            milvus_lite={
                "db_path": db_config.milvus_lite.db_path,
                "dim": db_config.milvus_lite.dim,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.post("/config/database")
async def update_database_config_api(config_update: DatabaseConfigUpdate):
    """更新数据库配置"""
    try:
        # 转换为字典格式
        update_data = {"db_type": config_update.db_type}
        
        if config_update.milvus_standard:
            update_data["milvus_standard"] = config_update.milvus_standard
        
        if config_update.milvus_lite:
            update_data["milvus_lite"] = config_update.milvus_lite
        
        # 更新配置
        success = update_database_config(update_data)
        
        if not success:
            raise HTTPException(status_code=400, detail="配置更新失败")
        
        # 重新获取配置并返回
        return await get_database_config_api()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@router.post("/config/database/test")
async def test_database_connection(test_request: DatabaseTestRequest):
    """测试数据库连接"""
    try:
        # 临时更新配置用于测试
        original_config = {
            "db_type": get_database_config().db_type
        }
        
        # 创建测试配置
        test_config = {
            "db_type": test_request.db_type,
            test_request.db_type: test_request.config
        }
        
        # 临时更新配置
        update_database_config(test_config)
        
        try:
            # 创建向量服务测试连接
            vector_service = VectorService()
            db_info = vector_service.get_database_info()
            
            return {
                "status": "success",
                "message": f"连接测试成功 - {db_info['db_type_display']}",
                "connection_status": db_info["connection_status"],
                "db_info": db_info
            }
        finally:
            # 恢复原始配置
            update_database_config(original_config)
            
    except Exception as e:
        return {
            "status": "failed",
            "message": f"连接测试失败: {str(e)}",
            "connection_status": "disconnected"
        }

@router.get("/config/database/info")
async def get_database_info():
    """获取数据库运行时信息"""
    try:
        vector_service = VectorService()
        db_info = vector_service.get_database_info()
        collection_stats = vector_service.get_collection_stats()
        
        return {
            "database_info": db_info,
            "collection_stats": collection_stats,
            "available_types": [
                {"value": "milvus_standard", "label": "Milvus 标准版", "description": "完整功能的分布式向量数据库"},
                {"value": "milvus_lite", "label": "Milvus Lite 版", "description": "轻量级单机版本，适合开发和小规模部署"}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库信息失败: {str(e)}")

@router.get("/config/models")
async def get_available_models():
    """获取可用的模型配置"""
    return {
        "embedding_models": settings.embedding_models,
        "default_embedding_model": settings.default_embedding_model,
        "index_types": settings.available_index_types,
        "default_index_type": settings.default_index_type,
        "search_config": {
            "default_search_threshold": settings.default_search_threshold,
            "default_top_k": settings.default_top_k
        }
    }