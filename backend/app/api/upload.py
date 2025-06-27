import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path

router = APIRouter()

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../uploaded_files"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    return JSONResponse(content={"filename": file.filename, "msg": "Upload successful"})

@router.get("/preview/{filename}")
async def preview_file(filename: str):
    """
    获取文件内容用于预览
    """
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 检查文件类型
    file_ext = Path(filename).suffix.lower()
    
    if file_ext == '.pdf':
        # PDF 文件直接返回文件路径，前端用iframe显示
        return JSONResponse(content={
            "type": "pdf",
            "filename": filename,
            "url": f"/api/file/{filename}"
        })
    
    elif file_ext in ['.txt', '.md', '.markdown']:
        # 文本文件读取内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return JSONResponse(content={
                "type": "text",
                "filename": filename,
                "content": content
            })
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                return JSONResponse(content={
                    "type": "text",
                    "filename": filename,
                    "content": content
                })
            except UnicodeDecodeError:
                return JSONResponse(content={
                    "type": "text",
                    "filename": filename,
                    "content": "文件编码不支持，无法预览"
                })
    
    else:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

@router.get("/file/{filename}")
async def get_file(filename: str):
    """
    直接访问文件，用于PDF预览等
    """
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 根据文件类型设置合适的 media_type，避免触发下载
    file_ext = Path(filename).suffix.lower()
    
    if file_ext == '.pdf':
        media_type = 'application/pdf'
    elif file_ext in ['.txt', '.md', '.markdown']:
        media_type = 'text/plain'
    else:
        media_type = 'application/octet-stream'
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={"Content-Disposition": "inline"}  # 设置为inline避免下载
    ) 