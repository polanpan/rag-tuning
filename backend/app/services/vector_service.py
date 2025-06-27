# backend/app/services/vector_service.py
from typing import List, Dict, Any, Optional
import warnings

# 抑制特定的LangChain弃用警告
warnings.filterwarnings("ignore", message=".*HuggingFaceEmbeddings.*deprecated.*", category=DeprecationWarning)

# 尝试导入嵌入模型
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings as NewHuggingFaceEmbeddings
    USE_NEW_EMBEDDINGS = True
    print("使用社区版 HuggingFaceEmbeddings")
except ImportError:
    from langchain_community.embeddings import SentenceTransformerEmbeddings
    USE_NEW_EMBEDDINGS = False
    print("回退到 SentenceTransformerEmbeddings")

from langchain_milvus import Milvus
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from pymilvus import connections, utility, Collection
import uuid
import os
import asyncio

# 导入配置模块
from ..core.config import (
    settings, 
    get_database_config, 
    get_milvus_connection_args, 
    is_milvus_lite, 
    get_db_type_display_name
)

class VectorService:
    """基于 LangChain v0.3 的向量处理和存储服务 - 支持Milvus标准版和Lite版"""
    
    def __init__(self, model_name: str = "nomic", index_type: str = "hnsw", threshold: float = 0.5):
        self.model_name = model_name
        self.index_type = index_type
        self.threshold = threshold
        self.collection_name = "documents_v3"
        
        # 获取数据库配置
        self.db_config = get_database_config()
        self.is_lite = is_milvus_lite()
        
        print(f"初始化向量服务 - 数据库类型: {get_db_type_display_name()}")
        
        # 初始化嵌入模型
        self._init_embedding_model()
        
        # 连接 Milvus
        self._connect_milvus()
        
        # 初始化向量存储
        self._init_vector_store()
    
    def _init_embedding_model(self):
        """初始化嵌入模型"""
        model_mapping = settings.embedding_models
        model_path = model_mapping.get(self.model_name, model_mapping["nomic"])
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                
                if USE_NEW_EMBEDDINGS:
                    self.embeddings = NewHuggingFaceEmbeddings(
                        model_name=model_path,
                        model_kwargs={'device': 'cpu', 'trust_remote_code': True},
                        encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
                    )
                    print(f"嵌入模型加载成功 (HuggingFace): {model_path}")
                else:
                    self.embeddings = SentenceTransformerEmbeddings(
                        model_name=model_path,
                        model_kwargs={'device': 'cpu', 'trust_remote_code': True},
                        encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
                    )
                    print(f"嵌入模型加载成功 (SentenceTransformer): {model_path}")
                    
        except Exception as e:
            print(f"嵌入模型加载失败: {e}")
            # 使用默认模型
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                if USE_NEW_EMBEDDINGS:
                    self.embeddings = NewHuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                else:
                    self.embeddings = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                print("使用默认嵌入模型")
    
    def _connect_milvus(self):
        """连接 Milvus 数据库 - 修复 alias 重复传递问题"""
        try:
            # 首先清理现有连接
            try:
                connections.disconnect("default")
                print("已断开现有连接")
            except:
                pass
            
            connection_args = get_milvus_connection_args()
            
            if self.is_lite:
                # Milvus Lite 连接
                connections.connect(alias="default", uri=connection_args['uri'])
                print("Milvus Lite 连接成功")
            else:
                # Milvus 标准版连接 - 修复：显式指定参数避免重复alias
                print(f"连接 Milvus 标准版服务器: {connection_args['host']}:{connection_args['port']}")
                connections.connect(
                    alias="default",
                    host=connection_args['host'],
                    port=connection_args['port'],
                    timeout=connection_args.get('timeout', 60),
                    user=connection_args.get('user'),
                    password=connection_args.get('password'),
                    secure=connection_args.get('secure', False)
                )
                print("Milvus 标准版连接成功")
                
        except Exception as e:
            print(f"Milvus 连接失败: {e}")
            print("将在内存中模拟向量存储")
    
    def _init_vector_store(self):
        """初始化向量存储 - 修复连接参数问题"""
        try:
            connection_args = get_milvus_connection_args()
            
            index_params = {
                "metric_type": "COSINE",
                "index_type": self.index_type.upper(),
                "params": {"nlist": 128} if self.index_type.upper() == "IVF_FLAT" else {"M": 8, "efConstruction": 64}
            }
            
            search_params = {"metric_type": "COSINE", "params": {"ef": 64}}
            
            if self.is_lite:
                milvus_connection_args = {"uri": connection_args['uri']}
            else:
                # 重新构建连接参数避免alias冲突
                milvus_connection_args = {
                    "host": connection_args['host'],
                    "port": connection_args['port']
                }
                if connection_args.get('user'):
                    milvus_connection_args["user"] = connection_args['user']
                if connection_args.get('password'):
                    milvus_connection_args["password"] = connection_args['password']
                if connection_args.get('secure'):
                    milvus_connection_args["secure"] = connection_args['secure']
                
            self.vector_store = Milvus(
                embedding_function=self.embeddings,
                collection_name=self.collection_name,
                connection_args=milvus_connection_args,
                index_params=index_params,
                search_params=search_params,
                drop_old=False
            )
            print(f"向量存储初始化成功，集合: {self.collection_name}")
            
        except Exception as e:
            print(f"向量存储初始化失败: {e}")
            self.vector_store = None

    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        return {
            "db_type": self.db_config.db_type,
            "db_type_display": get_db_type_display_name(),
            "is_lite": self.is_lite,
            "connection_status": "connected" if self.vector_store else "disconnected",
            "config": {
                "milvus_standard": {
                    "host": self.db_config.milvus_standard.host,
                    "port": self.db_config.milvus_standard.port,
                    "timeout": self.db_config.milvus_standard.timeout,
                } if not self.is_lite else None,
                "milvus_lite": {
                    "db_path": self.db_config.milvus_lite.db_path,
                    "dim": self.db_config.milvus_lite.dim,
                } if self.is_lite else None
            }
        }
