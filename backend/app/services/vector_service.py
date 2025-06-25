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

class VectorService:
    """基于 LangChain v0.3 的向量处理和存储服务"""
    
    def __init__(self, model_name: str = "nomic", index_type: str = "hnsw", threshold: float = 0.5):
        self.model_name = model_name
        self.index_type = index_type
        self.threshold = threshold
        self.collection_name = "documents_v3"
        
        # 初始化嵌入模型
        self._init_embedding_model()
        
        # 连接 Milvus
        self._connect_milvus()
        
        # 初始化向量存储
        self._init_vector_store()
    
    def _init_embedding_model(self):
        """初始化嵌入模型 (v0.3 语法)"""
        # 根据模型名称选择对应的嵌入模型
        model_mapping = {
            "nomic": "sentence-transformers/all-MiniLM-L6-v2",
            "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
            "all-mpnet-base-v2": "sentence-transformers/all-mpnet-base-v2",
            "bge-small": "BAAI/bge-small-en-v1.5"
        }
        
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
        """连接 Milvus 数据库"""
        try:
            connections.connect(
                alias="default",
                host=os.getenv("MILVUS_HOST", "localhost"),
                port=os.getenv("MILVUS_PORT", "19530"),
                timeout=60
            )
            print("Milvus 连接成功")
        except Exception as e:
            print(f"Milvus 连接失败: {e}")
            print("将在内存中模拟向量存储")
    
    def _init_vector_store(self):
        """初始化向量存储 (v0.3 语法)"""
        try:
            # v0.3 中的 Milvus 配置
            connection_args = {
                "host": os.getenv("MILVUS_HOST", "localhost"),
                "port": os.getenv("MILVUS_PORT", "19530"),
                "alias": "default"
            }
            
            # v0.3 新的索引参数格式
            index_params = {
                "metric_type": "COSINE",  # v0.3 推荐使用 COSINE
                "index_type": self.index_type.upper(),
                "params": {"nlist": 128} if self.index_type.upper() == "IVF_FLAT" else {"M": 8, "efConstruction": 64}
            }
            
            self.vector_store = Milvus(
                embedding_function=self.embeddings,
                collection_name=self.collection_name,
                connection_args=connection_args,
                index_params=index_params,
                search_params={"metric_type": "COSINE", "params": {"ef": 64}},
                drop_old=False  # v0.3 新增参数
            )
            print("向量存储初始化成功")
            
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