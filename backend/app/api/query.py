# backend/app/api/query.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    topk: int = 5
    contextLen: int = 512
    temperature: float = 0.7

class QueryResponse(BaseModel):
    answer: str
    docs: List[str]
    metadata: Dict[str, Any] = {}

@router.post("/query/", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="问题不能为空")
        
        logger.info(f"收到查询请求: {request.question}")
        
        vector_service = VectorService()
        search_results = await vector_service.search_documents(
            query=request.question,
            top_k=request.topk
        )
        
        if not search_results:
            return QueryResponse(
                answer="很抱歉，我在知识库中没有找到与您问题相关的内容。请尝试换个问题或上传更多相关文档。",
                docs=[],
                metadata={"source": "no_results"}
            )
        
        retrieved_docs = []
        doc_contents = []
        
        for result in search_results:
            doc_text = result.get('content', '')
            doc_source = result.get('source', 'unknown')
            
            if len(doc_text) > request.contextLen:
                doc_text = doc_text[:request.contextLen] + "..."
            
            retrieved_docs.append(f"[{doc_source}] {doc_text}")
            doc_contents.append(doc_text)
        
        context = "\n\n".join(doc_contents)
        
        llm_service = LLMService()
        answer = await llm_service.generate_answer(
            question=request.question,
            context=context,
            temperature=request.temperature
        )
        
        return QueryResponse(
            answer=answer,
            docs=retrieved_docs,
            metadata={
                "source": "rag",
                "retrieved_count": len(search_results),
                "context_length": len(context)
            }
        )
        
    except Exception as e:
        logger.error(f"查询处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询处理失败: {str(e)}")

@router.get("/query/health")
async def query_health():
    try:
        vector_service = VectorService()
        vector_status = await vector_service.health_check()
        
        llm_service = LLMService()
        llm_status = await llm_service.health_check()
        
        return {
            "status": "healthy",
            "vector_service": vector_status,
            "llm_service": llm_status
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
