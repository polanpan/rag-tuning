rag-tuning/
│
├─ backend/           # 后端（FastAPI、向量化、Milvus接口等）
│   ├─ app/
│   │   ├─ api/       # 路由与接口
│   │   ├─ core/      # 配置、工具
│   │   ├─ models/    # 数据模型
│   │   ├─ services/  # 业务逻辑
│   │   ├─ vector/    # 向量化与Milvus相关
│   │   └─ main.py    # FastAPI入口
│   ├─ tests/         # 后端测试
│   └─ requirements.txt
│
├─ frontend/          # 前端（Vue3）
│   ├─ src/
│   ├─ public/
│   ├─ package.json
│   └─ ...
│
├─ docs/              # 项目文档
│
├─ scripts/           # 启动、部署脚本
│
├─ README.md
└─ .gitignore
