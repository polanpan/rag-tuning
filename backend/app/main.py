# backend/app/main.py
from fastapi import FastAPI
from app.api import upload, embed  # 新增embed
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(upload.router, prefix="/api")
app.include_router(embed.router, prefix="/api")  # 新增

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