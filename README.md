
## ⚙️ 配置说明

### 后端配置 (.env)
```env
# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 模型配置
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# 安全配置
SECRET_KEY=your-secret-key
ENABLE_ENCRYPTION=true
```

### 前端配置
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true
      }
    }
  }
})
```

## 🔧 使用指南

### 1. 文档上传与嵌入
1. 在左侧"知识库管理"区域拖拽或点击上传 PDF/Markdown/TXT 文件
2. 配置嵌入参数（模型、索引类型、搜索阈值）
3. 点击"开始文档嵌入"按钮
4. 观察嵌入进度和状态更新

### 2. 智能问答 todo
1. 在右侧"RAG 查询"区域输入问题
2. 调整查询参数（Top-k、上下文长度、温度）
3. 点击"查询"按钮获得答案
4. 查看检索到的相关文档片段

### 3. 效果评估 todo
1. 上传测试集（CSV/JSON 格式）
2. 查看准确率、召回率等指标
3. 进行 A/B 测试对比不同配置

## 🔮 未来规划

- [ ] 支持更多文档格式（Word、Excel、PPT）
- [ ] 集成更多嵌入模型（Nomic-Embed-Text）
- [ ] 支持多语言处理
- [ ] 增加知识图谱功能
- [ ] 提供 API SDK
- [ ] 支持分布式部署
- [ ] 增加更多评测指标
- [ ] 开发移动端应用

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

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com

---

**智多星** - 让知识检索更智能，让数据更安全 🌟
