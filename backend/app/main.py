# backend/app/main.py
from fastapi import FastAPI
from app.api import upload, embed, config, query  # 新增query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(upload.router, prefix="/api")
app.include_router(embed.router, prefix="/api")
app.include_router(config.router, prefix="/api")  # 新增配置路由
app.include_router(query.router, prefix="/api")  # 新增查询路由

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"msg": "RAG Backend is running!"}