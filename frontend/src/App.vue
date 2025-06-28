<template>
  <div class="main-container">
    <!-- 顶部导航栏 -->
    <header class="header">
      <span class="logo">智多星</span>
      <div class="header-right">
        <el-tag type="success" effect="plain">本地加密已启用</el-tag>
        <!-- 可扩展用户信息、系统状态等 -->
      </div>
    </header>

    <div class="content">
      <!-- 左侧：知识库管理 -->
      <section class="left-panel">
        <el-card class="card">
          <div class="section-title">知识库管理</div>
          <!-- 文件上传 -->
          <el-upload
            class="upload-demo"
            drag
            action="http://localhost:8001/api/upload/"
            :show-file-list="true"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :before-upload="beforeUpload"
            multiple
          >
            <el-icon><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽或点击上传文件</div>
            <template #tip>
              <div class="el-upload__tip">支持 PDF、Markdown(.md/.markdown)、TXT 文件，最大 50MB</div>
            </template>
          </el-upload>
          <!-- 已上传文件列表 -->
          <el-table :data="uploadedFiles" style="width: 100%; margin-top: 16px;" v-if="uploadedFiles.length">
            <el-table-column prop="filename" label="文件名" />
            <el-table-column prop="status" label="状态" />
            <el-table-column label="操作">
              <template #default="scope">
                <el-button size="small" type="primary" @click="previewFile(scope.row)">预览</el-button>
                <el-button size="small" type="danger" @click="removeFile(scope.$index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 文件预览功能 -->
          <div v-if="previewState.show" class="file-preview" @click.self="closePreview">
            <div class="preview-modal">
              <div class="preview-header">
                <span class="preview-title">文件预览: {{ previewData.filename }}</span>
                <el-button size="small" @click="closePreview" type="info">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
              <div class="preview-content">
                <!-- PDF 预览 -->
                <iframe 
                  v-if="previewData.type === 'pdf'" 
                  :src="previewData.url" 
                  class="preview-iframe"
                ></iframe>
                <!-- 文本文件预览 -->
                <div v-else-if="previewData.type === 'text'" class="preview-text">
                  <!-- Markdown 文件预览 -->
                  <div v-if="isMarkdownFile(previewData.filename)" class="markdown-preview">
                    <!-- 模式切换按钮 -->
                    <div class="preview-toolbar">
                      <el-radio-group v-model="markdownViewMode" size="small">
                        <el-radio-button label="rendered">渲染模式</el-radio-button>
                        <el-radio-button label="source">源码模式</el-radio-button>
                      </el-radio-group>
                    </div>
                    <!-- 渲染模式 -->
                    <div 
                      v-if="markdownViewMode === 'rendered'" 
                      class="markdown-body" 
                      v-html="renderedMarkdown"
                    ></div>
                    <!-- 源码模式 -->
                    <pre 
                      v-else 
                      class="markdown-source"
                      v-html="highlightedMarkdown"
                    ></pre>
                  </div>
                  <!-- 普通文本文件预览 -->
                  <pre v-else class="text-content">{{ previewData.content }}</pre>
                </div>
                <!-- 加载中状态 -->
                <div v-else-if="previewData.loading" class="preview-loading">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>加载预览中...</span>
                </div>
                <!-- 错误状态 -->
                <div v-else-if="previewData.error" class="preview-error">
                  <el-icon><Warning /></el-icon>
                  <span>{{ previewData.error }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 数据库配置 -->
          <el-form :model="databaseConfig"  class="param-form">
            <!-- 数据库类型和路径在同一行 -->
            <div class="database-config-row">
              <el-form-item label="数据库类型" class="db-type-item">
                <el-select v-model="databaseConfig.db_type" placeholder="选择数据库类型" @change="handleDatabaseTypeChange">
                  <el-option label="Milvus Lite 版" value="milvus_lite" />
                  <el-option label="Milvus 标准版" value="milvus_standard" />
                </el-select>
              </el-form-item>
              
              <!-- Milvus Lite 配置 -->
              <el-form-item v-if="databaseConfig.db_type === 'milvus_lite'" label="数据库路径" class="db-path-item">
                <el-input v-model="databaseConfig.milvus_lite.db_path" placeholder="./milvus_lite.db" />
              </el-form-item>
              
              <!-- Milvus 标准版服务器配置 -->
              <el-form-item v-if="databaseConfig.db_type === 'milvus_standard'" label="服务器" class="db-path-item">
                <el-input 
                  :value="databaseConfig.milvus_standard.host + ':' + databaseConfig.milvus_standard.port" 
                  placeholder="localhost:19530" 
                  @input="handleServerInput"
                />
              </el-form-item>
              
              <div class="db-buttons">
                <el-button type="success" size="small" @click="testDatabaseConnection" :style="{ display: 'inline-block' }">测试连接</el-button>
                <el-button type="primary" size="small" @click="saveDatabaseConfig" :style="{ display: 'inline-block' }">保存配置</el-button>
              </div>
            </div>
            
            <!-- Milvus 标准版详细配置已移除，避免重复配置 -->
          </el-form>
          
          <!-- 参数设置 -->
          <el-form :model="embedParams" label-width="80px" class="param-form">
            <el-form-item label="嵌入模型">
              <el-select v-model="embedParams.model" placeholder="选择模型">
                <el-option label="Nomic-Embed-Text" value="nomic" />
                <el-option label="其他模型" value="other" />
              </el-select>
            </el-form-item>
            <el-form-item label="索引类型">
              <el-select v-model="embedParams.indexType" placeholder="选择索引">
                <el-option label="HNSW" value="hnsw" />
                <el-option label="IVF" value="ivf" />
              </el-select>
            </el-form-item>
            <el-form-item label="搜索阈值">
              <el-input-number v-model="embedParams.threshold" :min="0" :max="1" :step="0.01" />
            </el-form-item>
            
            <!-- 文档嵌入按钮 -->
            <div class="embed-button-container">
              <el-button 
                type="primary" 
                size="small"
                @click="handleDocumentEmbed" 
                :disabled="uploadedFiles.length === 0 || isEmbedding"
                :loading="isEmbedding"
                class="embed-button"
              >
                {{ isEmbedding ? '嵌入中...' : '文档嵌入' }}
              </el-button>
            </div>
          </el-form>
          
          <!-- 嵌入进度显示 -->
          <div v-if="embedProgress.show" class="embed-progress">
            <div class="progress-title">文档嵌入进度</div>
            <el-progress 
              :percentage="embedProgress.percentage" 
              :status="embedProgress.status"
              :format="embedProgressFormat"
            />
            <div class="progress-info">{{ embedProgress.currentStep }}</div>
          </div>
        </el-card>
      </section>

      <!-- 右侧：RAG 查询与评测 -->
      <section class="right-panel">
        <el-card class="card">
          <div class="section-title">RAG 查询</div>
          <!-- 查询输入与参数 - 改为垂直布局 -->
          <el-form :model="queryParams" label-width="100px" class="query-form">
            <el-form-item label="问题">
              <el-input v-model="queryParams.question" placeholder="请输入你的问题" />
            </el-form-item>
            <el-form-item label="Top-k">
              <el-input-number v-model="queryParams.topk" :min="1" :max="20" />
            </el-form-item>
            <el-form-item label="上下文长度">
              <el-input-number v-model="queryParams.contextLen" :min="100" :max="4096" />
            </el-form-item>
            <el-form-item label="温度">
              <el-input-number v-model="queryParams.temperature" :min="0" :max="2" :step="0.01" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleQuery">查询</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 查询结果 -->
          <el-card class="result-card" v-if="queryResult">
            <div class="result-title">答案</div>
            <div class="result-answer">{{ queryResult.answer }}</div>
            <div class="result-docs">
              <div class="result-doc-title">相关文档片段：</div>
              <ul>
                <li v-for="(doc, idx) in queryResult.docs" :key="idx">{{ doc }}</li>
              </ul>
            </div>
          </el-card>
        </el-card>

        <el-card class="card">
          <div class="section-title">效果评测</div>
          <!-- 测试集上传 -->
          <el-upload
            action="http://localhost:8001/api/upload_testset/"
            :show-file-list="false"
            :on-success="handleTestsetSuccess"
            :on-error="handleTestsetError"
            accept=".csv,.json"
          >
            <el-button>上传测试集（CSV/JSON）</el-button>
          </el-upload>
          <!-- 评测结果图表（占位） -->
          <div class="metrics">
            <el-tag>准确率: 95%</el-tag>
            <el-tag type="success">召回率: 90%</el-tag>
            <el-tag type="info">响应时间: 300ms</el-tag>
          </div>
        </el-card>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Loading, Close, Warning } from '@element-plus/icons-vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import 'github-markdown-css/github-markdown-light.css'

// 组件加载时初始化
onMounted(() => {
  loadDatabaseConfig()
})

// 文件上传相关
const uploadedFiles = ref([])
const isEmbedding = ref(false)

// 嵌入进度
const embedProgress = ref({
  show: false,
  percentage: 0,
  status: '',
  currentStep: ''
})

const handleUploadSuccess = (response, file, fileList) => {
  ElMessage.success(`上传成功: ${response.filename}`)
  uploadedFiles.value.push({ 
    filename: response.filename, 
    status: '已上传',
    embedded: false 
  })
}

const handleUploadError = () => {
  ElMessage.error('上传失败，请重试')
}

const beforeUpload = (file) => {
  // 检查文件扩展名而不是MIME类型，因为某些文件的MIME类型可能不标准
  const fileName = file.name.toLowerCase()
  const allowedExtensions = ['.pdf', '.md', '.markdown', '.txt']
  
  const isValidFile = allowedExtensions.some(ext => fileName.endsWith(ext))
  
  if (!isValidFile) {
    ElMessage.error('仅支持 PDF、Markdown(.md/.markdown)、TXT 文件')
    return false
  }
  
  // 检查文件大小（可选，比如限制50MB）
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  
  return true
}

const removeFile = (idx) => {
  uploadedFiles.value.splice(idx, 1)
}

// 数据库配置
const databaseConfig = ref({
  db_type: 'milvus_lite',
  milvus_standard: {
    host: 'localhost',
    port: 19530,
    timeout: 60
  },
  milvus_lite: {
    db_path: './milvus_lite.db',
    dim: 384
  }
})

// 嵌入参数
const embedParams = ref({
  model: 'nomic',
  indexType: 'hnsw',
  threshold: 0.5
})

// 文档嵌入处理
const handleDocumentEmbed = async () => {
  if (uploadedFiles.value.length === 0) {
    ElMessage.warning('请先上传文件')
    return
  }
  
  isEmbedding.value = true
  embedProgress.value = {
    show: true,
    percentage: 0,
    status: '',
    currentStep: '准备开始嵌入...'
  }
  
  try {
    // 获取所有未嵌入的文件
    const filesToEmbed = uploadedFiles.value
      .filter(file => !file.embedded)
      .map(file => file.filename)
    
    const response = await fetch('http://localhost:8001/api/embed/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filenames: filesToEmbed,
        embed_model: embedParams.value.model,
        index_type: embedParams.value.indexType,
        search_threshold: embedParams.value.threshold
      })
    })
    
    if (!response.ok) {
      throw new Error('嵌入请求失败')
    }
    
    const result = await response.json()
    
    // 模拟进度更新（实际项目中可以用 WebSocket 或轮询）
    await simulateEmbedProgress()
    
    // 更新文件状态
    uploadedFiles.value.forEach(file => {
      if (filesToEmbed.includes(file.filename)) {
        file.status = '已嵌入'
        file.embedded = true
      }
    })
    
    ElMessage.success('文档嵌入完成！')
    
  } catch (error) {
    console.error('嵌入失败:', error)
    ElMessage.error('文档嵌入失败，请重试')
    embedProgress.value.status = 'exception'
  } finally {
    isEmbedding.value = false
  }
}

// 模拟嵌入进度
const simulateEmbedProgress = () => {
  return new Promise((resolve) => {
    const steps = [
      { percentage: 20, step: '解析文档内容...' },
      { percentage: 50, step: '生成文本向量...' },
      { percentage: 80, step: '存储到向量数据库...' },
      { percentage: 100, step: '嵌入完成！' }
    ]
    
    let currentIndex = 0
    const updateProgress = () => {
      if (currentIndex < steps.length) {
        embedProgress.value.percentage = steps[currentIndex].percentage
        embedProgress.value.currentStep = steps[currentIndex].step
        currentIndex++
        setTimeout(updateProgress, 1000)
      } else {
        resolve()
      }
    }
    updateProgress()
  })
}

const embedProgressFormat = (percentage) => {
  return `${percentage}%`
}

// 查询相关
const queryParams = ref({
  question: '',
  topk: 5,
  contextLen: 512,
  temperature: 0.7
})
const queryResult = ref(null)
const handleQuery = async () => {
  if (!queryParams.value.question.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  try {
    ElMessage.info('正在查询中...')
    
    const response = await fetch('http://localhost:8001/api/query/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: queryParams.value.question,
        topk: queryParams.value.topk,
        contextLen: queryParams.value.contextLen,
        temperature: queryParams.value.temperature
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || '查询失败')
    }
    
    const result = await response.json()
    queryResult.value = {
      answer: result.answer,
      docs: result.docs,
      metadata: result.metadata
    }
    
    ElMessage.success('查询完成！')
    
  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error(`查询失败: ${error.message}`)
    queryResult.value = null
  }
}

// 测试集上传
const handleTestsetSuccess = () => {
  ElMessage.success('测试集上传成功')
}
const handleTestsetError = () => {
  ElMessage.error('测试集上传失败')
}

// 文件预览相关
const previewState = ref({
  show: false
})
const previewData = ref({
  filename: '',
  type: '',
  url: '',
  content: '',
  loading: false,
  error: null
})

// Markdown 预览相关
const markdownViewMode = ref('rendered')

// 配置 marked
marked.setOptions({
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  },
  langPrefix: 'hljs language-',
  breaks: true,
  gfm: true
})

// 数据库配置相关方法
const loadDatabaseConfig = async () => {
  try {
    const response = await fetch('http://localhost:8001/api/config/database')
    if (response.ok) {
      const config = await response.json()
      databaseConfig.value.db_type = config.db_type
      databaseConfig.value.milvus_standard = config.milvus_standard
      databaseConfig.value.milvus_lite = config.milvus_lite
    }
  } catch (error) {
    console.error('加载数据库配置失败:', error)
  }
}

const handleDatabaseTypeChange = () => {
  console.log('数据库类型切换为:', databaseConfig.value.db_type)
}

// 处理服务器输入（host:port格式）
const handleServerInput = (value) => {
  const parts = value.split(':')
  if (parts.length === 2) {
    databaseConfig.value.milvus_standard.host = parts[0].trim()
    const port = parseInt(parts[1].trim())
    if (!isNaN(port)) {
      databaseConfig.value.milvus_standard.port = port
    }
  } else if (parts.length === 1) {
    databaseConfig.value.milvus_standard.host = parts[0].trim()
  }
}

const testDatabaseConnection = async () => {
  try {
    const config = databaseConfig.value.db_type === 'milvus_standard' 
      ? databaseConfig.value.milvus_standard 
      : databaseConfig.value.milvus_lite
    
    const response = await fetch('http://localhost:8001/api/config/database/test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        db_type: databaseConfig.value.db_type,
        config: config
      })
    })
    
    const result = await response.json()
    
    if (result.status === 'success') {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('测试数据库连接失败:', error)
    ElMessage.error('测试连接失败，请检查网络连接')
  }
}

const saveDatabaseConfig = async () => {
  try {
    const response = await fetch('http://localhost:8001/api/config/database', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(databaseConfig.value)
    })
    
    if (response.ok) {
      ElMessage.success('数据库配置保存成功！')
    } else {
      const error = await response.json()
      ElMessage.error(`保存失败: ${error.detail}`)
    }
  } catch (error) {
    console.error('保存数据库配置失败:', error)
    ElMessage.error('保存配置失败，请重试')
  }
}

// 判断是否为 Markdown 文件
const isMarkdownFile = (filename) => {
  if (!filename) return false
  const ext = filename.toLowerCase()
  return ext.endsWith('.md') || ext.endsWith('.markdown')
}

// 渲染 Markdown 内容
const renderedMarkdown = computed(() => {
  if (!previewData.value.content || !isMarkdownFile(previewData.value.filename)) {
    return ''
  }
  try {
    return marked(previewData.value.content)
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return '<p>Markdown 渲染失败</p>'
  }
})

// 高亮 Markdown 源码
const highlightedMarkdown = computed(() => {
  if (!previewData.value.content) return ''
  try {
    return hljs.highlight(previewData.value.content, { language: 'markdown' }).value
  } catch (error) {
    console.error('语法高亮失败:', error)
    return previewData.value.content
  }
})

const previewFile = async (file) => {
  try {
    // 重置预览数据
    previewData.value = {
      filename: file.filename,
      type: '',
      url: '',
      content: '',
      loading: true,
      error: null
    }
    previewState.value.show = true
    
    // 获取文件内容进行预览
    const response = await fetch(`http://localhost:8001/api/preview/${file.filename}`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const result = await response.json()
    
    // 更新预览数据
    previewData.value.loading = false
    previewData.value.type = result.type
    
    if (result.type === 'pdf') {
      previewData.value.url = `http://localhost:8001/api/file/${file.filename}`
    } else if (result.type === 'text') {
      previewData.value.content = result.content || '文件内容为空'
    }
    
  } catch (error) {
    console.error('预览错误:', error)
    previewData.value.loading = false
    previewData.value.error = '无法加载文件内容，请检查文件是否存在'
    ElMessage.error('文件预览失败')
  }
}

const closePreview = () => {
  previewState.value.show = false
  markdownViewMode.value = 'rendered' // 重置为渲染模式
  previewData.value = {
    filename: '',
    type: '',
    url: '',
    content: '',
    loading: false,
    error: null
  }
}
</script>

<style scoped>
/* 全局重置与全屏适配 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow-x: hidden;
}

#app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  max-width: 100vw; /* 自适应宽度 */
}

.main-container {
  width: 100vw;
  height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

.header {
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #409eff;
  color: #fff;
  font-size: 22px;
  font-weight: bold;
  padding: 0 32px 0 0; /* 只给右侧padding，左侧为0 */
  flex-shrink: 0;
  letter-spacing: 2px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin: 0;
}

.logo {
  user-select: none;
  padding-left: 16px; /* 减少logo左边距，让整体更贴近边缘 */
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.content {
  flex: 1;
  display: flex;
  gap: 2vw; /* 改为视口宽度的2% */
  padding: 0;
  overflow: hidden;
  margin: 0;
}

.left-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2vh; /* 改为视口高度的2% */
  overflow-y: auto;
  padding: 2vh 0 2vh 2vw; /* 使用视口单位替代固定像素 */
}

.right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2vh; /* 改为视口高度的2% */
  overflow-y: auto;
  padding: 2vh 2vw 2vh 0; /* 使用视口单位替代固定像素 */
}

.card {
  flex-shrink: 0;
  height: fit-content;
}

.section-title {
  font-size: 1.2rem; /* 改为相对单位 */
  font-weight: 600;
  margin-bottom: 1rem; /* 改为相对单位 */
  color: #303133;
}

.param-form {
  margin-top: 2vh; /* 改为视口高度的2% */
}

/* 数据库配置行样式 */
.database-config-row {
  display: flex;
  align-items: flex-end;
  gap: 1%;
  margin-bottom: 1.5vh; /* 改为视口单位 */
  flex-wrap: wrap;
  min-height: 3vh; /* 改为视口高度的3% */
}

.db-type-item {
  flex: 0 0 auto;
  min-width: 200px;
  width: auto;
  margin-bottom: 0 !important;
}

.db-type-item .el-form-item__label {
  white-space: nowrap !important;
  min-width: fit-content !important;
}

.db-type-item .el-select {
  width: 100%;
  min-width: 200px; /* 确保下拉框有足够宽度显示内容 */
}

.db-path-item {
  flex: 2;
  min-width: 250px;
  margin-bottom: 0 !important;
}

.db-path-item .el-form-item__label {
  white-space: nowrap !important;
  min-width: fit-content !important;
}

.db-path-item .el-input {
  width: 100%;
  min-width: 250px; /* 确保输入框有足够宽度 */
}

.db-path-item .el-input .el-input__inner {
  text-overflow: clip; /* 不使用省略号，显示完整内容 */
  white-space: nowrap;
  overflow: visible; /* 允许内容溢出显示 */
}

.db-buttons {
  display: flex !important; /* 强制显示按钮组 */
  /* gap: 8px; */
  flex: 0 0 auto;
  align-items: center;
  /* min-width: 180px; 确保按钮组有足够空间 */
  visibility: visible; /* 确保可见性 */
}

.db-buttons .el-button {
  white-space: nowrap;
  height: 32px;
  flex: 0 0 auto;
  display: inline-block !important; /* 强制显示按钮 */
  visibility: visible !important; /* 确保可见 */
}

/* 确保表单项标签对齐 */
.database-config-row .el-form-item__label {
  height: auto;
  line-height: 1.2;
  padding-bottom: 8px;
  white-space: nowrap !important; /* 强制防止标签文字换行 */
  min-width: fit-content; /* 确保标签有足够宽度 */
  flex-shrink: 0; /* 防止标签被压缩 */
}

.database-config-row .el-form-item__content {
  line-height: 1;
  min-width: 0; /* 允许内容收缩 */
}

/* RAG 查询表单 - 垂直布局 */
.query-form {
  /* 移除 flex-wrap，使用默认垂直布局 */
}

.query-form .el-form-item {
  margin-bottom: 1.5vh; /* 改为视口高度的1.5% */
}

.query-form .el-input,
.query-form .el-input-number {
  width: 100%;
  max-width: 25vw; /* 改为视口宽度的25% */
  min-width: 200px; /* 设置最小宽度确保可用性 */
}

.result-card {
  margin-top: 24px;
  background: #f9f9f9;
}

.result-title {
  font-weight: bold;
  margin-bottom: 8px;
  color: #303133;
}

.result-answer {
  margin-bottom: 12px;
  color: #606266;
  line-height: 1.6;
}

.result-doc-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: 500;
}

.result-docs ul {
  list-style: none;
  padding-left: 0;
}

.result-docs li {
  padding: 8px 12px;
  margin: 4px 0;
  background: #fff;
  border-radius: 4px;
  border-left: 3px solid #409eff;
  color: #606266;
  font-size: 14px;
}

.metrics {
  margin-top: 16px;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.embed-progress {
  margin-top: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.progress-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}

.progress-info {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
  text-align: center;
}



/* 响应式适配 */
@media (max-width: 1024px) {
  .content {
    flex-direction: column;
    gap: 2vh; /* 改为视口单位 */
    padding: 1vh 1vw; /* 改为视口单位 */
  }
  
  .left-panel {
    padding: 0 2vw; /* 改为视口单位 */
  }
  
  .right-panel {
    padding: 0 2vw; /* 改为视口单位 */
  }
  
  .left-panel, .right-panel {
    flex: none;
    overflow-y: visible;
  }
  
  .header {
    padding: 0 2vw; /* 改为视口单位 */
    font-size: 1.1rem; /* 改为相对单位 */
  }
  
  .logo {
    padding-left: 0;
  }
  
  .preview-modal {
    width: 95%;
    height: 90%;
  }
  
  /* 数据库配置在中等屏幕下的适配 */
  .database-config-row {
    gap: 2%;
    flex-wrap: wrap;
  }
  
  .db-type-item, .db-path-item {
    min-width: 180px;
    flex: 1 1 auto;
  }
  
  .db-buttons {
    display: flex !important; /* 确保按钮组在中等屏幕下也显示 */
    flex: 0 0 auto;
    min-width: 160px;
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .header {
    height: 7vh; /* 改为视口高度的7% */
    font-size: 1rem; /* 改为相对单位 */
  }
  
  .content {
    padding: 1vh 1vw; /* 改为视口单位 */
  }
  
  .left-panel, .right-panel {
    padding: 0;
  }
  
  .logo {
    padding-left: 0;
  }
  
  .query-form .el-input,
  .query-form .el-input-number {
    max-width: 100%;
    min-width: 150px; /* 确保最小可用宽度 */
  }
  
  .preview-modal {
    width: 98%;
    height: 95%;
  }
  
  .preview-header {
    padding: 1vh 2vw; /* 改为视口单位 */
  }
  
  .preview-title {
    font-size: 0.9rem; /* 改为相对单位 */
  }
  
  /* 小屏幕下数据库配置的特殊处理 */
  .database-config-row {
    flex-direction: column;
    gap: 1vh;
    align-items: stretch;
  }
  
  .db-type-item, .db-path-item, .db-buttons {
    width: 100%;
    min-width: auto;
  }
  
  .db-type-item .el-form-item__label,
  .db-path-item .el-form-item__label {
    white-space: nowrap !important; /* 小屏幕下也确保不换行 */
    overflow: visible !important;
  }
  
  .db-buttons {
    display: flex !important; /* 确保按钮组显示 */
    justify-content: center;
    margin-top: 1vh;
    gap: 8px; /* 确保按钮间距 */
    align-items: center; /* 垂直居中 */
  }
}

.file-preview {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.preview-modal {
  background: #fff;
  border-radius: 8px;
  width: 85%;
  height: 85%;
  max-width: 1200px;
  max-height: 800px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.preview-header {
  background: #f5f7fa;
  padding: 16px 20px;
  border-radius: 8px 8px 0 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e4e7ed;
}

.preview-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.preview-content {
  flex: 1;
  padding: 20px;
  overflow: auto;
  background: #fff;
  border-radius: 0 0 8px 8px;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 4px;
}

.preview-text {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.text-content {
  margin: 0;
  padding: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.6;
  color: #606266;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  background: transparent;
  border: none;
  flex: 1;
}

/* Markdown 预览样式 */
.markdown-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview-toolbar {
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #f8f9fa;
  flex-shrink: 0;
}

.markdown-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #fff;
  font-size: 14px;
  line-height: 1.6;
}

.markdown-source {
  flex: 1;
  margin: 0;
  padding: 20px;
  overflow-y: auto;
  background: #f6f8fa;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  border: none;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 自定义 Markdown 样式覆盖 */
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body h1 {
  font-size: 2em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body h2 {
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body code {
  background-color: rgba(175, 184, 193, 0.2);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 85%;
}

.markdown-body pre {
  background-color: #f6f8fa;
  border-radius: 6px;
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
}

.markdown-body blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin: 0 0 16px 0;
}

.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

.markdown-body table th,
.markdown-body table td {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}

.markdown-body table th {
  background-color: #f6f8fa;
  font-weight: 600;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 12px;
  color: #909399;
}

.preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 12px;
  color: #909399;
}

.embed-button-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.embed-button {
  width: auto;
}
</style>