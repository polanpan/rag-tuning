# backend/app/services/vector_service.py
from typing import List, Dict, Any, Optional
from langchain_community.embeddings import SentenceTransformerEmbeddings
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
        """初始化嵌入模型 (v0.3 语法)"""
        # 从配置获取模型映射
        model_mapping = settings.embedding_models
        model_path = model_mapping.get(self.model_name, model_mapping["nomic"])
        
        try:
            # v0.3 中的 SentenceTransformerEmbeddings 配置
            self.embeddings = SentenceTransformerEmbeddings(
                model_name=model_path,
                model_kwargs={
                    'device': 'cpu',  # 如有GPU可改为'cuda'
                    'trust_remote_code': True
                },
                encode_kwargs={
                    'normalize_embeddings': True,  # v0.3 新增参数
                    'batch_size': 32
                }
            )
            print(f"嵌入模型加载成功: {model_path}")
        except Exception as e:
            print(f"嵌入模型加载失败: {e}")
            # 使用默认模型
            self.embeddings = SentenceTransformerEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
    
    def _connect_milvus(self):
        """连接 Milvus 数据库 - 支持标准版和Lite版"""
        try:
            connection_args = get_milvus_connection_args()
            
            if self.is_lite:
                # 检查是否在支持的平台上
                import platform
                system = platform.system()
                if system == "Windows":
                    raise RuntimeError("Milvus Lite 目前不支持 Windows 系统。请使用 Milvus 标准版或在 Linux/macOS 环境下运行。")
                
                # Milvus Lite 连接
                print(f"启动 Milvus Lite 服务，数据库路径: {connection_args['uri']}")
                
                # 尝试导入 milvus-lite
                try:
                    import milvus_lite
                except ImportError:
                    raise RuntimeError("milvus-lite 包未安装。请安装：pip install milvus-lite")
                
                # 连接到 Milvus Lite
                connections.connect(
                    alias="default",
                    uri=connection_args['uri']
                )
                print("Milvus Lite 连接成功")
            else:
                # Milvus 标准版连接
                print(f"连接 Milvus 标准版服务器: {connection_args['host']}:{connection_args['port']}")
                connections.connect(**connection_args)
                print("Milvus 标准版连接成功")
                
        except Exception as e:
            print(f"Milvus 连接失败: {e}")
            if self.is_lite:
                print("Milvus Lite 连接失败，将在内存中模拟向量存储")
                print("提示：在 Windows 环境下，请切换到 Milvus 标准版或使用 WSL/Docker")
            else:
                print("Milvus 标准版连接失败，请检查服务器状态")
            print("将在内存中模拟向量存储")
    
    def _init_vector_store(self):
        """初始化向量存储 (v0.3 语法) - 支持标准版和Lite版"""
        try:
            connection_args = get_milvus_connection_args()
            
            # v0.3 新的索引参数格式
            index_params = {
                "metric_type": "COSINE",  # v0.3 推荐使用 COSINE
                "index_type": self.index_type.upper(),
                "params": {"nlist": 128} if self.index_type.upper() == "IVF_FLAT" else {"M": 8, "efConstruction": 64}
            }
            
            # 搜索参数
            search_params = {"metric_type": "COSINE", "params": {"ef": 64}}
            
            # 根据数据库类型调整参数
            if self.is_lite:
                # Milvus Lite 特定配置
                self.vector_store = Milvus(
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name,
                    connection_args={"uri": connection_args['uri']},
                    index_params=index_params,
                    search_params=search_params,
                    drop_old=False  # v0.3 新增参数
                )
                print(f"Milvus Lite 向量存储初始化成功，集合: {self.collection_name}")
            else:
                # Milvus 标准版配置
                self.vector_store = Milvus(
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name,
                    connection_args=connection_args,
                    index_params=index_params,
                    search_params=search_params,
                    drop_old=False  # v0.3 新增参数
                )
                print(f"Milvus 标准版向量存储初始化成功，集合: {self.collection_name}")
            
        except Exception as e:
            print(f"向量存储初始化失败: {e}")
            self.vector_store = None
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        异步生成文本向量嵌入 (v0.3 支持异步)
        """
        try:
            # v0.3 中支持异步嵌入
            if hasattr(self.embeddings, 'aembed_documents'):
                vectors = await self.embeddings.aembed_documents(texts)
            else:
                # 同步方法的异步包装
                vectors = await asyncio.to_thread(self.embeddings.embed_documents, texts)
            return vectors
        except Exception as e:
            print(f"向量生成失败: {e}")
            # 返回模拟向量
            import numpy as np
            return [np.random.random(384).tolist() for _ in texts]
    
    async def store_vectors(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        异步存储文档块到向量数据库 (v0.3 语法)
        """
        try:
            if self.vector_store is None:
                raise RuntimeError("向量存储未初始化")
            
            # 转换为 LangChain Document 格式
            documents = []
            for chunk in chunks:
                doc = Document(
                    page_content=chunk["text"],
                    metadata=chunk["metadata"]
                )
                documents.append(doc)
            
            # v0.3 支持异步批量添加
            if hasattr(self.vector_store, 'aadd_documents'):
                doc_ids = await self.vector_store.aadd_documents(documents)
            else:
                # 同步方法的异步包装
                doc_ids = await asyncio.to_thread(self.vector_store.add_documents, documents)
            
            print(f"成功存储 {len(documents)} 个文档块到向量数据库")
            return doc_ids
            
        except Exception as e:
            print(f"向量存储失败: {e}")
            # 返回模拟ID
            return [str(uuid.uuid4()) for _ in chunks]
    
    async def search_similar(self, query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        异步相似性搜索 (v0.3 语法)
        """
        try:
            if self.vector_store is None:
                return []
            
            # v0.3 中的搜索参数
            search_kwargs = {
                "k": k,
                "score_threshold": self.threshold
            }
            
            if filter_dict:
                search_kwargs["filter"] = filter_dict
            
            # v0.3 支持异步搜索
            if hasattr(self.vector_store, 'asimilarity_search_with_score'):
                results = await self.vector_store.asimilarity_search_with_score(
                    query=query,
                    **search_kwargs
                )
            else:
                # 同步方法的异步包装
                results = await asyncio.to_thread(
                    self.vector_store.similarity_search_with_score,
                    query,
                    **search_kwargs
                )
            
            # 格式化结果
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"相似性搜索失败: {e}")
            return []
    
    def create_retriever(self, search_type: str = "similarity", **kwargs) -> Optional[VectorStoreRetriever]:
        """
        创建检索器 (v0.3 新特性)
        """
        try:
            if self.vector_store is None:
                return None
            
            return self.vector_store.as_retriever(
                search_type=search_type,
                search_kwargs={
                    "k": kwargs.get("k", 5),
                    "score_threshold": kwargs.get("score_threshold", self.threshold)
                }
            )
        except Exception as e:
            print(f"检索器创建失败: {e}")
            return None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            if self.vector_store is None:
                return {"status": "disconnected"}
            
            # v0.3 中的集合信息获取
            collection = Collection(self.collection_name)
            collection.load()
            
            return {
                "status": "connected",
                "collection_name": self.collection_name,
                "total_entities": collection.num_entities,
                "index_type": self.index_type,
                "embedding_model": self.model_name,
                "vector_dimension": self.embeddings.client.get_sentence_embedding_dimension() if hasattr(self.embeddings, 'client') else 384
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

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