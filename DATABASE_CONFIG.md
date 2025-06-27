# 数据库配置切换说明

## 概述

项目现在支持在 **Milvus 标准版** 和 **Milvus Lite 版** 之间切换，满足不同场景的使用需求。

## 数据库类型对比

### Milvus 标准版
- **适用场景**: 生产环境、大数据量处理、分布式部署
- **特点**: 
  - 完整功能的分布式向量数据库
  - 支持集群部署和横向扩展
  - 高性能、高并发
  - 需要独立的 Milvus 服务器
  - **支持所有平台**（Windows/Linux/macOS）
- **配置项**:
  - 服务器地址 (host)
  - 端口号 (port)
  - 用户名/密码 (可选)
  - 连接超时时间

### Milvus Lite 版
- **适用场景**: 开发环境、小规模部署、快速原型
- **特点**:
  - 轻量级单机版本
  - 嵌入式部署，无需独立服务器
  - 快速启动，易于配置
  - 适合开发和测试
  - **⚠️ 仅支持 Linux/macOS，不支持 Windows**
- **配置项**:
  - 数据库文件路径 (db_path)
  - 向量维度 (dim)

## 使用方法

### 1. 前端界面切换

在左侧"知识库管理"区域的"数据库配置"部分：

1. **选择数据库类型**: 从下拉菜单选择"Milvus Lite 版"或"Milvus 标准版"
2. **配置参数**: 根据选择的类型配置对应参数
3. **测试连接**: 点击"测试连接"按钮验证配置
4. **保存配置**: 点击"保存配置"按钮应用更改

### 2. 环境变量配置

创建 `backend/.env` 文件进行配置：

```env
# 数据库类型选择
RAG_DATABASE__DB_TYPE=milvus_lite

# Milvus 标准版配置
RAG_DATABASE__MILVUS_STANDARD__HOST=localhost
RAG_DATABASE__MILVUS_STANDARD__PORT=19530
RAG_DATABASE__MILVUS_STANDARD__TIMEOUT=60

# Milvus Lite 配置
RAG_DATABASE__MILVUS_LITE__DB_PATH=./milvus_lite.db
RAG_DATABASE__MILVUS_LITE__DIM=384
```

### 3. API 接口

#### 获取当前配置
```bash
GET /api/config/database
```

#### 更新配置
```bash
POST /api/config/database
Content-Type: application/json

{
  "db_type": "milvus_lite",
  "milvus_lite": {
    "db_path": "./custom_path.db",
    "dim": 384
  }
}
```

#### 测试连接
```bash
POST /api/config/database/test
Content-Type: application/json

{
  "db_type": "milvus_lite",
  "config": {
    "db_path": "./test.db",
    "dim": 384
  }
}
```

## 部署建议

### 开发环境
- **Linux/macOS**: 推荐使用 **Milvus Lite 版**
  - 配置简单，启动快速
  - 无需额外服务器资源
- **Windows**: 使用 **Milvus 标准版**
  - 可通过 Docker 部署 Milvus 服务器
  - 或使用 WSL2 + Docker 环境

### 生产环境
- 推荐使用 **Milvus 标准版**
- 需要预先部署 Milvus 服务器
- 可支持大规模数据和高并发访问

## 数据迁移

切换数据库类型时，已存储的向量数据不会自动迁移。如需迁移：

1. 导出现有数据（如通过API获取所有文档）
2. 切换数据库配置
3. 重新执行文档嵌入过程

## 故障排除

### Milvus Lite 常见问题
- **Windows 不支持**: Milvus Lite 目前不支持 Windows 系统
  - 解决方案：使用 Milvus 标准版 + Docker
  - 或在 WSL2 环境下运行
- **权限错误**: 确保应用有权限在指定路径创建文件
- **磁盘空间**: 检查数据库文件路径是否有足够空间
- **包未安装**: 在支持的平台上安装 `milvus-lite` 包

### Milvus 标准版常见问题
- **连接失败**: 检查 Milvus 服务是否正常运行
- **端口占用**: 确认端口号配置正确且未被占用
- **网络问题**: 检查防火墙和网络连接

## 配置示例

### 本地开发配置
```json
{
  "db_type": "milvus_lite",
  "milvus_lite": {
    "db_path": "./data/milvus_dev.db",
    "dim": 384
  }
}
```

### 生产环境配置
```json
{
  "db_type": "milvus_standard",
  "milvus_standard": {
    "host": "milvus-server.example.com",
    "port": 19530,
    "timeout": 60,
    "secure": true
  }
}
```