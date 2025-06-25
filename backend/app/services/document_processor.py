# backend/app/services/document_processor.py
from typing import List, Dict, Any
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pathlib import Path
import asyncio

class DocumentProcessor:
    """基于 LangChain v0.3 的文档解析处理器"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 初始化文本分割器 (v0.3 语法)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
            keep_separator=False,
            is_separator_regex=False,
        )
    
    async def parse_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        使用 LangChain v0.3 解析文档并分块
        返回包含文本和元数据的字典列表
        """
        file_extension = Path(file_path).suffix.lower()
        filename = Path(file_path).name
        
        # 根据文件类型选择合适的加载器
        try:
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension == '.md':
                loader = UnstructuredMarkdownLoader(
                    file_path,
                    mode="single",
                    strategy="fast"
                )
            elif file_extension == '.txt':
                loader = TextLoader(
                    file_path, 
                    encoding='utf-8',
                    autodetect_encoding=True
                )
            else:
                raise ValueError(f"不支持的文件类型: {file_extension}")
            
            # 异步加载文档 (v0.3 支持异步操作)
            documents = await asyncio.to_thread(loader.load)
            
            # 分块处理
            chunks = await asyncio.to_thread(self.text_splitter.split_documents, documents)
            
            # 转换为标准格式
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # v0.3 中 Document 对象结构
                processed_chunks.append({
                    "text": chunk.page_content,
                    "metadata": {
                        "filename": filename,
                        "chunk_id": i,
                        "file_type": file_extension,
                        "source": file_path,
                        "chunk_size": len(chunk.page_content),
                        **chunk.metadata  # 包含原始元数据
                    }
                })
            
            return processed_chunks
            
        except Exception as e:
            raise RuntimeError(f"文档解析失败 {filename}: {str(e)}")
    
    async def parse_multiple_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        批量解析多个文档
        """
        all_chunks = []
        
        # 并发处理多个文档
        tasks = [self.parse_document(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"文档解析失败 {file_paths[i]}: {result}")
                continue
            all_chunks.extend(result)
        
        return all_chunks
    
    def get_document_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取文档统计信息"""
        if not chunks:
            return {"total_chunks": 0, "total_characters": 0, "average_chunk_size": 0}
        
        total_chars = sum(len(chunk["text"]) for chunk in chunks)
        return {
            "total_chunks": len(chunks),
            "total_characters": total_chars,
            "average_chunk_size": total_chars // len(chunks),
            "min_chunk_size": min(len(chunk["text"]) for chunk in chunks),
            "max_chunk_size": max(len(chunk["text"]) for chunk in chunks)
        }