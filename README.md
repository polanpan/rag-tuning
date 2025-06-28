# 智多星 - RAG本地知识库系统

> 🌟 基于 LangChain + Milvus + Vue3 的企业级RAG知识库解决方案

一个功能完整的本地RAG（检索增强生成）知识库系统，支持文档上传、向量化存储、智能问答和效果评估。所有数据处理均在本地完成，确保数据隐私和安全。

## ✨ 功能特性

### 🔍 核心功能
- **📚 知识库构建**：支持PDF、Markdown、TXT文档上传和解析
- **🧠 向量化存储**：基于Sentence Transformers的文档嵌入和Milvus向量数据库
- **💬 智能问答**：RAG检索 + 大语言模型生成，支持DeepSeek和Ollama
- **📊 效果评估**：离线测试集评估，提供准确率、召回率等指标
- **👀 文档预览**：支持PDF和Markdown文件的在线预览

### 🛡️ 技术特性
- **🔒 数据安全**：本地部署，数据不出域
- **⚡ 高性能**：Milvus向量数据库，毫秒级检索
- **🔧 易扩展**：模块化设计，支持多种模型和数据库
- **🎨 现代UI**：Vue3 + Element Plus，响应式设计
- **🐍 标准API**：FastAPI后端，RESTful接口

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面层     │    │    接口层       │    │    服务层       │
│   Vue3 + EP    │◄──►│   FastAPI      │◄──►│   LangChain    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    数据层       │    │    模型层       │    │    配置层       │
│   Milvus DB    │◄──►│  Transformers  │◄──►│   Pydantic     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 环境要求

### 系统要求
- **操作系统**：Windows 10/11, macOS, Linux
- **Python**：3.8+
- **Node.js**：16+
- **内存**：8GB+ 推荐
- **存储**：10GB+ 可用空间

### 依赖服务
- **Milvus**：向量数据库（支持Lite版和标准版）
- **DeepSeek API**：大语言模型服务（可选）
- **Ollama**：本地大模型服务（可选）

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd rag-tuning
```

### 2. 后端设置

#### Windows环境
```powershell
# 切换到后端目录
cd backend

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
python -m uvicorn app.main:app --reload --port 8001
```

#### Linux/macOS环境
```bash
# 切换到后端目录
cd backend

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
python -m uvicorn app.main:app --reload --port 8001
```

### 3. 前端设置
```bash
# 切换到前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问系统
- **前端界面**：http://localhost:5173
- **后端API**：http://localhost:8001
- **API文档**：http://localhost:8001/docs

## ⚙️ 配置说明

### 后端配置
创建 `backend/.env` 文件：

```env
# 数据库配置
RAG_DATABASE__DB_TYPE=milvus_standard  # 或 milvus_lite
RAG_DATABASE__MILVUS_STANDARD__HOST=localhost
RAG_DATABASE__MILVUS_STANDARD__PORT=19530

# LLM配置
RAG_LLM_MODEL_TYPE=deepseek  # 或 ollama
RAG_DEEPSEEK_API_KEY=your-deepseek-api-key
RAG_OLLAMA_URL=http://localhost:11434

# 嵌入模型配置
RAG_DEFAULT_EMBEDDING_MODEL=nomic
RAG_DEFAULT_INDEX_TYPE=hnsw
RAG_DEFAULT_SEARCH_THRESHOLD=0.5
```

### 前端配置
`frontend/vite.config.ts` 已配置代理，无需额外设置。

## 🔧 使用指南

### 1. 数据库配置
1. 在左侧面板选择数据库类型（Milvus标准版或Lite版）
2. 配置连接参数（主机、端口等）
3. 点击"测试连接"验证配置
4. 点击"保存配置"保存设置

### 2. 文档上传与嵌入
1. 在"知识库管理"区域拖拽或点击上传文档
2. 支持格式：PDF、Markdown(.md/.markdown)、TXT
3. 配置嵌入参数：
   - **嵌入模型**：选择向量化模型
   - **索引类型**：HNSW（推荐）或IVF
   - **搜索阈值**：相似度过滤阈值
4. 点击"文档嵌入"开始处理
5. 观察嵌入进度和状态

### 3. 智能问答 ✅
1. 在"RAG查询"区域输入问题
2. 调整查询参数：
   - **Top-k**：检索文档数量（1-20）
   - **上下文长度**：单个文档最大字符数
   - **温度**：模型创造性参数（0-2）
3. 点击"查询"按钮
4. 查看生成的答案和相关文档片段

### 4. 文档预览
1. 在文件列表中点击"预览"按钮
2. PDF文件：iframe内嵌显示
3. Markdown文件：支持渲染模式和源码模式切换
4. 文本文件：直接显示内容

### 5. 效果评估（开发中）
1. 上传测试集（CSV/JSON格式）
2. 查看评估指标（准确率、召回率、响应时间）
3. 进行A/B测试对比不同配置

## 📊 API接口

### 核心接口
- `POST /api/upload/` - 文档上传
- `POST /api/embed/` - 文档嵌入
- `POST /api/query/` - RAG查询 ✅
- `GET /api/preview/{filename}` - 文档预览
- `POST /api/config/database` - 数据库配置

### 健康检查
- `GET /api/query/health` - 查询服务状态 ✅
- `GET /api/config/database/test` - 数据库连接测试

## 🔮 开发进度

### ✅ 已完成
- [x] 项目架构设计
- [x] 文档上传功能
- [x] 文档嵌入处理（LangChain v0.3）
- [x] 向量数据库集成（Milvus）
- [x] 文档预览功能（PDF + Markdown）
- [x] **RAG查询系统**
- [x] **多模型支持（DeepSeek + Ollama）**
- [x] **智能降级处理**
- [x] 数据库配置管理
- [x] 响应式UI设计

### 🚧 开发中
- [ ] 效果评估模块
- [ ] 实时监控功能
- [ ] 数据加密和隐私保护

### 📋 未来规划
- [ ] 支持更多文档格式（Word、Excel、PPT）
- [ ] 集成更多嵌入模型（Nomic-Embed-Text）
- [ ] 支持多语言处理
- [ ] 增加知识图谱功能
- [ ] 提供API SDK
- [ ] 支持分布式部署
- [ ] 移动端应用

## 🛠️ 技术栈

### 后端
- **框架**：FastAPI 0.115.0
- **AI框架**：LangChain 0.3.7
- **向量数据库**：Milvus 2.4.10
- **嵌入模型**：Sentence Transformers 3.0.1
- **HTTP客户端**：aiohttp 3.10.5
- **配置管理**：Pydantic Settings 2.6.0

### 前端
- **框架**：Vue 3 + TypeScript
- **UI组件**：Element Plus
- **构建工具**：Vite
- **Markdown渲染**：marked + highlight.js

### 数据库
- **向量存储**：Milvus（标准版/Lite版）
- **元数据**：SQLite（内置）

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - AI应用开发框架
- [Milvus](https://github.com/milvus-io/milvus) - 向量数据库
- [FastAPI](https://github.com/tiangolo/fastapi) - 现代Web框架
- [Vue.js](https://github.com/vuejs/vue) - 渐进式JavaScript框架
- [Element Plus](https://github.com/element-plus/element-plus) - Vue 3 UI组件库
- [DeepSeek](https://www.deepseek.com/) - 大语言模型服务
- [Ollama](https://ollama.ai/) - 本地大模型运行时

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com

---

**智多星** - 让知识检索更智能，让数据更安全 🌟 