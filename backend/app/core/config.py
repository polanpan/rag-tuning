# backend/app/core/config.py
from typing import Optional, Literal
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os
from pathlib import Path

class MilvusStandardConfig(BaseModel):
    """Milvus 标准版配置"""
    host: str = Field(default="localhost", description="Milvus服务器地址")
    port: int = Field(default=19530, description="Milvus服务器端口")
    user: Optional[str] = Field(default=None, description="用户名")
    password: Optional[str] = Field(default=None, description="密码")
    secure: bool = Field(default=False, description="是否使用安全连接")
    timeout: int = Field(default=60, description="连接超时时间")

class MilvusLiteConfig(BaseModel):
    """Milvus Lite 配置"""
    db_path: str = Field(default="./milvus_lite.db", description="数据库文件路径")
    dim: int = Field(default=384, description="向量维度")
    
class DatabaseConfig(BaseModel):
    """数据库配置"""
    # 数据库类型选择
    db_type: Literal["milvus_standard", "milvus_lite"] = Field(
        default="milvus_standard",  # Windows下默认使用标准版
        description="数据库类型: milvus_standard(标准版) 或 milvus_lite(轻量版)"
    )
    
    # Milvus 标准版配置
    milvus_standard: MilvusStandardConfig = Field(default_factory=MilvusStandardConfig)
    
    # Milvus Lite 配置
    milvus_lite: MilvusLiteConfig = Field(default_factory=MilvusLiteConfig)

class AppConfig(BaseSettings):
    """应用配置"""
    # 基本配置
    app_name: str = Field(default="RAG Knowledge Base", description="应用名称")
    debug: bool = Field(default=True, description="调试模式")
    
    # 数据库配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # 文件上传配置
    upload_dir: str = Field(default="./uploaded_files", description="文件上传目录")
    max_file_size: int = Field(default=50 * 1024 * 1024, description="最大文件大小(字节)")
    allowed_extensions: list = Field(
        default=[".pdf", ".md", ".markdown", ".txt"], 
        description="允许的文件扩展名"
    )
    
    # 嵌入模型配置
    default_embedding_model: str = Field(default="nomic", description="默认嵌入模型")
    embedding_models: dict = Field(
        default={
            "nomic": "sentence-transformers/all-MiniLM-L6-v2",
            "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
            "all-mpnet-base-v2": "sentence-transformers/all-mpnet-base-v2",
            "bge-small": "BAAI/bge-small-en-v1.5"
        },
        description="可用的嵌入模型映射"
    )
    
    # 索引配置
    default_index_type: str = Field(default="hnsw", description="默认索引类型")
    available_index_types: list = Field(
        default=["hnsw", "ivf_flat", "ivf_sq8", "flat"],
        description="可用的索引类型"
    )
    
    # 搜索配置
    default_search_threshold: float = Field(default=0.5, description="默认搜索阈值")
    default_top_k: int = Field(default=5, description="默认返回结果数量")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8", 
        "case_sensitive": False,
        "env_prefix": "RAG_",
        "env_nested_delimiter": "__",
        "extra": "ignore"  # 忽略额外的环境变量
    }

# 全局配置实例
settings = AppConfig()

def get_database_config() -> DatabaseConfig:
    """获取数据库配置"""
    return settings.database

def get_milvus_connection_args() -> dict:
    """根据配置类型获取Milvus连接参数"""
    db_config = get_database_config()
    
    if db_config.db_type == "milvus_standard":
        # 标准版连接参数
        connection_args = {
            "host": db_config.milvus_standard.host,
            "port": db_config.milvus_standard.port,
            "timeout": db_config.milvus_standard.timeout
        }
        
        # 添加认证信息（如果有）
        if db_config.milvus_standard.user:
            connection_args["user"] = db_config.milvus_standard.user
        if db_config.milvus_standard.password:
            connection_args["password"] = db_config.milvus_standard.password
        if db_config.milvus_standard.secure:
            connection_args["secure"] = db_config.milvus_standard.secure
            
        return connection_args
    
    elif db_config.db_type == "milvus_lite":
        # Lite版连接参数
        db_path = db_config.milvus_lite.db_path
        
        # 确保数据库目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        return {
            "uri": db_path,
            "alias": "default"
        }
    
    else:
        raise ValueError(f"不支持的数据库类型: {db_config.db_type}")

def is_milvus_lite() -> bool:
    """判断是否使用Milvus Lite"""
    return get_database_config().db_type == "milvus_lite"

def get_db_type_display_name() -> str:
    """获取数据库类型的显示名称"""
    db_type = get_database_config().db_type
    return {
        "milvus_standard": "Milvus 标准版",
        "milvus_lite": "Milvus Lite 版"
    }.get(db_type, db_type)

# 配置更新函数
def update_database_config(new_config: dict) -> bool:
    """动态更新数据库配置"""
    try:
        global settings
        
        # 验证配置
        if "db_type" in new_config:
            if new_config["db_type"] not in ["milvus_standard", "milvus_lite"]:
                raise ValueError("数据库类型必须是 'milvus_standard' 或 'milvus_lite'")
        
        # 更新配置
        if "db_type" in new_config:
            settings.database.db_type = new_config["db_type"]
        
        if "milvus_standard" in new_config:
            for key, value in new_config["milvus_standard"].items():
                setattr(settings.database.milvus_standard, key, value)
        
        if "milvus_lite" in new_config:
            for key, value in new_config["milvus_lite"].items():
                setattr(settings.database.milvus_lite, key, value)
        
        return True
    except Exception as e:
        print(f"配置更新失败: {e}")
        return False