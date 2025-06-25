<!-- src/views/HomeView.vue -->
<template>
  <div>
    <header class="header">
      <span class="title">智多星</span>
    </header>
    <div class="home-upload">
      <el-upload
        class="upload-demo"
        drag
        action="http://localhost:8001/api/upload/"
        :show-file-list="false"
        :on-success="handleSuccess"
        :on-error="handleError"
        :before-upload="beforeUpload"
      >
        <el-icon><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、Markdown、TXT 文件</div>
        </template>
      </el-upload>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const handleSuccess = (response) => {
  ElMessage.success(`上传成功: ${response.filename}`)
}

const handleError = () => {
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
</script>

<style scoped>
.header {
  width: 100%;
  height: 56px;
  display: flex;
  align-items: center;
  background: #409eff;
  color: #fff;
  font-size: 22px;
  font-weight: bold;
  padding-left: 32px;
  box-sizing: border-box;
  letter-spacing: 2px;
}
.title {
  user-select: none;
}
.home-upload {
  max-width: 400px;
  margin: 80px auto;
}
</style>