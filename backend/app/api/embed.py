# backend/app/api/embed.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import asyncio
from ..services.document_processor import DocumentProcessor
from ..services.vector_service import VectorService

router = APIRouter()

class EmbedRequest(BaseModel):
    filenames: List[str] = Field(..., description="要嵌入的文件名列表")
    embed_model: str = Field(default="nomic", description="嵌入模型名称")
    index_type: str = Field(default="hnsw", description="索引类型")
    search_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="搜索阈值")
    chunk_size: int = Field(default=500, gt=0, description="文本块大小")
    chunk_overlap: int = Field(default=50, ge=0, description="文本块重叠大小")

class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    k: int = Field(default=5, gt=0, le=50, description="返回结果数量")
    filter_metadata: Optional[dict] = Field(default=None, description="元数据过滤条件")

@router.post("/embed/")
async def embed_documents(request: EmbedRequest):
    """
    使用 LangChain v0.3 进行文档嵌入：解析文档、生成向量、存储到Milvus
    """
    try:
        # 初始化处理器（使用 LangChain v0.3）
        doc_processor = DocumentProcessor(
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        vector_service = VectorService(
            model_name=request.embed_model,
            index_type=request.index_type,
            threshold=request.search_threshold
        )
        
        # 获取上传文件目录
        upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../uploaded_files"))
        
        # 构建文件路径列表
        file_paths = []
        for filename in request.filenames:
            file_path = os.path.join(upload_dir, filename)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
            file_paths.append(file_path)
        
        # 1. 使用 LangChain v0.3 批量解析文档
        all_chunks = await doc_processor.parse_multiple_documents(file_paths)
        
        # 2. 获取整体统计信息
        overall_stats = doc_processor.get_document_stats(all_chunks)
        
        # 3. 异步存储到向量数据库
        vector_ids = await vector_service.store_vectors(all_chunks)
        
        # 4. 按文件分组统计
        file_results = {}
        for chunk in all_chunks:
            filename = chunk["metadata"]["filename"]
            if filename not in file_results:
                file_results[filename] = {
                    "filename": filename,
                    "chunks_count": 0,
                    "total_characters": 0,
                    "status": "success"
                }
            file_results[filename]["chunks_count"] += 1
            file_results[filename]["total_characters"] += len(chunk["text"])
        
        # 5. 获取向量存储统计信息
        collection_stats = vector_service.get_collection_stats()
        
        return {
            "status": "success",
            "message": f"成功嵌入 {len(request.filenames)} 个文件，共 {len(all_chunks)} 个文本块",
            "overall_stats": overall_stats,
            "file_results": list(file_results.values()),
            "collection_stats": collection_stats,
            "embedding_config": {
                "model": request.embed_model,
                "index_type": request.index_type,
                "chunk_size": request.chunk_size,
                "chunk_overlap": request.chunk_overlap
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"嵌入处理失败: {str(e)}")

@router.post("/search/")
async def search_documents(request: SearchRequest):
    """
    在向量数据库中搜索相似文档
    """
    try:
        vector_service = VectorService()
        
        # 执行相似性搜索
        results = await vector_service.search_similar(
            query=request.query,
            k=request.k,
            filter_dict=request.filter_metadata
        )
        
        return {
            "status": "success",
            "query": request.query,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/collection/stats")
async def get_collection_stats():
    """获取向量集合统计信息"""
    try:
        vector_service = VectorService()
        stats = vector_service.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")