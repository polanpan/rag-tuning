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
            <div class="el-upload__text">拖拽或点击上传 PDF/Markdown/TXT 文件</div>
          </el-upload>
          <!-- 已上传文件列表 -->
          <el-table :data="uploadedFiles" style="width: 100%; margin-top: 16px;" v-if="uploadedFiles.length">
            <el-table-column prop="filename" label="文件名" />
            <el-table-column prop="status" label="状态" />
            <el-table-column label="操作">
              <template #default="scope">
                <el-button size="small" type="danger" @click="removeFile(scope.$index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
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
            <el-form-item>
              <el-button 
                type="primary" 
                @click="handleDocumentEmbed" 
                :disabled="uploadedFiles.length === 0 || isEmbedding"
                :loading="isEmbedding"
              >
                {{ isEmbedding ? '文档嵌入中...' : '开始文档嵌入' }}
              </el-button>
            </el-form-item>
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
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

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
  const allowedTypes = [
    'application/pdf',
    'text/markdown',
    'text/plain'
  ]
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持 PDF、Markdown、TXT 文件')
    return false
  }
  return true
}

const removeFile = (idx) => {
  uploadedFiles.value.splice(idx, 1)
}

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
const handleQuery = () => {
  // TODO: 调用后端接口
  queryResult.value = {
    answer: '这是大模型生成的答案示例。',
    docs: ['文档片段1', '文档片段2']
  }
}

// 测试集上传
const handleTestsetSuccess = () => {
  ElMessage.success('测试集上传成功')
}
const handleTestsetError = () => {
  ElMessage.error('测试集上传失败')
}
</script>

<style scoped>
/* 全局重置与全屏适配 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.main-container {
  width: 100vw;
  height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
}

.logo {
  user-select: none;
  padding-left: 24px; /* 单独给logo添加左边距 */
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.content {
  flex: 1;
  display: flex;
  gap: 24px;
  padding: 0; /* 完全移除content的padding */
  overflow: hidden;
}

.left-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
  padding: 24px 0 24px 24px; /* 上下24px，右侧0，左侧24px */
}

.right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
  padding: 24px 24px 24px 0; /* 上下24px，右侧24px，左侧0 */
}

.card {
  flex-shrink: 0;
  height: fit-content;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #303133;
}

.param-form {
  margin-top: 24px;
}

/* RAG 查询表单 - 垂直布局 */
.query-form {
  /* 移除 flex-wrap，使用默认垂直布局 */
}

.query-form .el-form-item {
  margin-bottom: 20px; /* 增加组件间距 */
}

.query-form .el-input,
.query-form .el-input-number {
  width: 100%; /* 输入框占满宽度 */
  max-width: 300px; /* 限制最大宽度 */
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

.param-form .el-button {
  width: 100%;
}

/* 响应式适配 */
@media (max-width: 1024px) {
  .content {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }
  
  .left-panel {
    padding: 0 16px;
  }
  
  .right-panel {
    padding: 0 16px;
  }
  
  .left-panel, .right-panel {
    flex: none;
    overflow-y: visible;
  }
  
  .header {
    padding: 0 16px;
    font-size: 18px;
  }
  
  .logo {
    padding-left: 0;
  }
}

@media (max-width: 768px) {
  .header {
    height: 50px;
    font-size: 16px;
  }
  
  .content {
    padding: 12px;
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
  }
}
</style>