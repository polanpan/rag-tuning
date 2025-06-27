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

    async def store_vectors(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        存储文档块到向量数据库
        
        Args:
            chunks: 文档块列表，每个块包含 'text' 和 'metadata' 字段
            
        Returns:
            List[str]: 存储的向量ID列表
        """
        if not self.vector_store:
            raise Exception("向量存储未初始化")
        
        if not chunks:
            return []
        
        try:
            # 将chunks转换为LangChain Document对象
            documents = []
            for chunk in chunks:
                doc = Document(
                    page_content=chunk.get('text', ''),
                    metadata=chunk.get('metadata', {})
                )
                documents.append(doc)
            
            # 为每个文档生成唯一ID
            vector_ids = [str(uuid.uuid4()) for _ in documents]
            
            # 批量添加文档到向量存储
            await asyncio.to_thread(
                self.vector_store.add_documents,
                documents,
                ids=vector_ids
            )
            
            print(f"成功存储 {len(documents)} 个文档块到向量数据库")
            return vector_ids
            
        except Exception as e:
            print(f"存储向量失败: {e}")
            raise Exception(f"向量存储失败: {str(e)}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取向量集合的统计信息
        
        Returns:
            Dict: 包含集合统计信息的字典
        """
        try:
            if not self.vector_store:
                return {
                    "collection_name": self.collection_name,
                    "total_entities": 0,
                    "status": "disconnected",
                    "error": "向量存储未初始化"
                }
            
            # 获取集合信息
            try:
                collection = Collection(self.collection_name)
                collection.load()
                
                # 获取实体数量
                total_entities = collection.num_entities
                
                # 获取集合schema信息
                schema_info = {
                    "fields": [
                        {
                            "name": field.name,
                            "type": field.dtype.name,
                            "description": field.description
                        }
                        for field in collection.schema.fields
                    ]
                }
                
                return {
                    "collection_name": self.collection_name,
                    "total_entities": total_entities,
                    "status": "connected",
                    "schema": schema_info,
                    "index_type": self.index_type,
                    "embedding_model": self.model_name,
                    "database_type": get_db_type_display_name()
                }
                
            except Exception as e:
                # 如果集合不存在或其他错误，返回基本信息
                return {
                    "collection_name": self.collection_name,
                    "total_entities": 0,
                    "status": "empty",
                    "index_type": self.index_type,
                    "embedding_model": self.model_name,
                    "database_type": get_db_type_display_name(),
                    "message": "集合为空或尚未创建"
                }
                
        except Exception as e:
            print(f"获取集合统计信息失败: {e}")
            return {
                "collection_name": self.collection_name,
                "total_entities": 0,
                "status": "error",
                "error": str(e)
            }

    async def search_similar(self, query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 搜索查询字符串
            k: 返回结果数量
            filter_dict: 元数据过滤条件
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.vector_store:
            raise Exception("向量存储未初始化")
        
        try:
            # 构建搜索参数
            search_kwargs = {"k": k}
            if filter_dict:
                search_kwargs["filter"] = filter_dict
            
            # 执行相似性搜索
            results = await asyncio.to_thread(
                self.vector_store.similarity_search_with_score,
                query,
                **search_kwargs
            )
            
            # 格式化结果
            formatted_results = []
            for doc, score in results:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                    "similarity": 1.0 - float(score)  # 转换为相似度
                }
                formatted_results.append(result)
            
            print(f"搜索完成，返回 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            print(f"搜索失败: {e}")
            raise Exception(f"向量搜索失败: {str(e)}")

    async def delete_collection(self) -> bool:
        """
        删除整个集合
        
        Returns:
            bool: 删除是否成功
        """
        try:
            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                print(f"集合 {self.collection_name} 已删除")
                return True
            else:
                print(f"集合 {self.collection_name} 不存在")
                return False
        except Exception as e:
            print(f"删除集合失败: {e}")
            return False

    async def clear_collection(self) -> bool:
        """
        清空集合中的所有数据
        
        Returns:
            bool: 清空是否成功
        """
        try:
            if utility.has_collection(self.collection_name):
                collection = Collection(self.collection_name)
                # 删除所有实体
                collection.delete(expr="pk >= 0")
                print(f"集合 {self.collection_name} 已清空")
                return True
            else:
                print(f"集合 {self.collection_name} 不存在")
                return False
        except Exception as e:
            print(f"清空集合失败: {e}")
            return False

    def get_retriever(self, search_type: str = "similarity", search_kwargs: Optional[Dict] = None) -> VectorStoreRetriever:
        """
        获取向量存储检索器
        
        Args:
            search_type: 搜索类型 ("similarity", "mmr", "similarity_score_threshold")
            search_kwargs: 搜索参数
            
        Returns:
            VectorStoreRetriever: LangChain检索器对象
        """
        if not self.vector_store:
            raise Exception("向量存储未初始化")
        
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )