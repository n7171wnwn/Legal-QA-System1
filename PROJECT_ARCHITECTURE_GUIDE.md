# 智慧司法问答系统 - 项目架构与启动指南

## 📋 项目概述

智慧司法问答系统是一个基于 **Vue2 + SpringBoot** 的智能法律问答系统，集成了 **DeepSeek API** 实现 AI 驱动的法律问答功能。系统能够理解用户的法律问题，检索相关知识库，并生成准确、可信的法律答案。

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                     前端层 (Vue2)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │  首页    │  │ 智能问答  │  │ 知识库   │  │ 管理后台 ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
│       │              │              │            │      │
│       └──────────────┴──────────────┴────────────┘      │
│                        │                                 │
│                   Axios HTTP Client                      │
└────────────────────────┼─────────────────────────────────┘
                         │ HTTP/JSON
                         │
┌────────────────────────┼─────────────────────────────────┐
│                     后端层 (SpringBoot)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Controller 层                        │  │
│  │  AuthController | QuestionAnswerController      │  │
│  │  LegalArticleController | AdminController       │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Service 层                           │  │
│  │  QuestionAnswerService | DeepSeekService        │  │
│  │  LegalArticleService | UserService              │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Repository 层 (JPA)                 │  │
│  │  UserRepository | QuestionAnswerRepository      │  │
│  │  LegalArticleRepository | LegalCaseRepository  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────▼────┐                    ┌────▼────┐
    │  MySQL  │                    │DeepSeek │
    │Database │                    │   API   │
    └─────────┘                    └─────────┘
```

### 技术栈详解

#### 后端技术栈

| 技术                | 版本   | 用途                           |
| ------------------- | ------ | ------------------------------ |
| **Spring Boot**     | 2.7.14 | 核心框架，提供依赖注入、AOP 等 |
| **Spring Data JPA** | -      | 数据持久化，简化数据库操作     |
| **Spring Security** | -      | 安全认证与授权                 |
| **MySQL**           | 8.0+   | 关系型数据库                   |
| **JWT**             | 0.9.1  | 无状态身份认证                 |
| **OkHttp**          | 4.11.0 | HTTP 客户端，调用 DeepSeek API |
| **FastJSON**        | 2.0.40 | JSON 序列化/反序列化           |
| **Lombok**          | -      | 简化 Java 代码                 |

#### 前端技术栈

| 技术           | 版本    | 用途          |
| -------------- | ------- | ------------- |
| **Vue.js**     | 2.6.14  | 前端框架      |
| **Vue Router** | 3.5.4   | 路由管理      |
| **Vuex**       | 3.6.2   | 状态管理      |
| **Element UI** | 2.15.13 | UI 组件库     |
| **Axios**      | 1.4.0   | HTTP 请求库   |
| **ECharts**    | 5.4.2   | 数据可视化    |
| **Marked**     | 4.3.0   | Markdown 解析 |

---

## 🔧 核心功能模块

### 1. 用户认证模块

**功能：**

- 用户注册/登录
- JWT Token 认证
- 用户信息管理
- 头像上传

**相关文件：**

- `AuthController.java` - 认证控制器
- `UserService.java` - 用户服务
- `JwtUtil.java` - JWT 工具类
- `SecurityConfig.java` - 安全配置

### 2. 智能问答模块（核心）

**功能流程：**

```
用户提问
    ↓
问题分类（DeepSeek API）
    ↓
实体识别（法条、罪名、机构等）
    ↓
知识检索（从数据库检索相关法条、案例、概念）
    ↓
生成答案（DeepSeek API + 知识库上下文）
    ↓
可信度评估（DeepSeek API）
    ↓
保存问答记录
    ↓
返回结果（答案 + 相关法条 + 相关案例 + 可信度）
```

**支持的问题类型：**

- 法条查询：查询具体法律条文
- 概念定义：解释法律概念
- 程序咨询：司法程序相关问题
- 案例分析：案例相关问题

**相关文件：**

- `QuestionAnswerController.java` - 问答控制器
- `QuestionAnswerService.java` - 问答服务（核心逻辑）
- `DeepSeekService.java` - DeepSeek API 调用服务

### 3. 法律知识库模块

**包含内容：**

- **法条库** (`legal_articles`)：法律法规条文
- **案例库** (`legal_cases`)：司法案例
- **概念库** (`legal_concepts`)：法律概念定义
- **知识库** (`knowledge_base`)：问答对知识

**功能：**

- 搜索法条、案例、概念
- 查看详细信息
- 关联推荐

**相关文件：**

- `LegalArticleController.java` - 法条控制器
- `LegalCaseController.java` - 案例控制器
- `LegalConceptController.java` - 概念控制器
- 对应的 Service 和 Repository

### 4. 管理后台模块

**功能：**

- 知识库管理（增删改查）
- 问答记录管理
- 数据统计（使用 ECharts 可视化）
- 用户管理

**相关文件：**

- `AdminController.java` - 管理控制器
- `views/admin/` - 管理后台前端页面

### 5. 流式输出模块

**功能：**

- 支持 SSE（Server-Sent Events）流式输出
- 实时显示 AI 生成答案的过程
- 提升用户体验

**实现：**

- `QuestionAnswerController.askQuestionStream()` - 流式问答接口

---

## 📊 数据库设计

### 核心表结构

#### 1. users（用户表）

```sql
- id: 主键
- username: 用户名（唯一）
- password: 密码（BCrypt加密）
- email: 邮箱
- phone: 手机号
- nickname: 昵称
- avatar: 头像URL
- user_type: 用户类型（0-普通用户，1-管理员）
```

#### 2. question_answers（问答记录表）

```sql
- id: 主键
- user_id: 用户ID
- question: 问题
- answer: 答案
- question_type: 问题类型
- confidence_score: 可信度评分（0-1）
- entities: 识别的实体（JSON）
- related_laws: 相关法条（JSON）
- related_cases: 相关案例（JSON）
- session_id: 会话ID（支持多轮对话）
- is_favorite: 是否收藏
```

#### 3. legal_articles（法条表）

```sql
- id: 主键
- title: 法律名称
- article_number: 条号
- content: 条文内容
- law_type: 法律类型（民法、刑法等）
- publish_org: 发布机构
- publish_date: 发布日期
```

#### 4. legal_cases（案例表）

```sql
- id: 主键
- title: 案例标题
- case_type: 案由
- content: 案例内容
- court_name: 审理法院
- judge_date: 判决日期
- dispute_point: 核心争议点
- judgment_result: 判决结果
```

#### 5. legal_concepts（概念表）

```sql
- id: 主键
- name: 概念名称（唯一）
- definition: 定义
- explanation: 详细解释
- law_type: 所属法律领域
```

#### 6. knowledge_base（知识库表）

```sql
- id: 主键
- question: 问题
- answer: 答案
- question_type: 问题类型
- tags: 标签
- usage_count: 使用次数
- quality_score: 质量评分
```

---

## 🚀 环境配置与启动指南

### 一、环境要求

#### 必需软件

| 软件        | 版本要求 | 下载地址                                                                                              |
| ----------- | -------- | ----------------------------------------------------------------------------------------------------- |
| **JDK**     | 1.8+     | [Oracle JDK](https://www.oracle.com/java/technologies/downloads/) 或 [OpenJDK](https://adoptium.net/) |
| **Maven**   | 3.6+     | [Apache Maven](https://maven.apache.org/download.cgi)                                                 |
| **Node.js** | 14+      | [Node.js 官网](https://nodejs.org/)                                                                   |
| **MySQL**   | 8.0+     | [MySQL 官网](https://dev.mysql.com/downloads/mysql/)                                                  |

#### 验证安装

```powershell
# 检查Java版本
java -version

# 检查Maven版本
mvn -version

# 检查Node.js版本
node -v

# 检查npm版本
npm -v

# 检查MySQL版本
mysql --version
```

---

### 二、数据库配置

#### 1. 创建数据库

```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE legal_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE legal_qa;
```

#### 2. 导入完整数据库（推荐，包含示例数据）

**如果您想快速开始并使用包含示例数据的完整数据库，可以使用导出的完整数据库文件：**

**方法一：使用命令行导入（推荐）**

**重要：** 请在项目根目录（包含 `backend` 和 `frontend` 文件夹的目录）下执行命令

```powershell
# Windows PowerShell
# 首先进入项目根目录
cd <项目根目录路径>

# 导入数据库（会提示输入MySQL密码）
mysql -u root -p legal_qa < backend/src/main/resources/db/migration/legal_qa_complete.sql
```

**Linux/Mac：**

```bash
# 进入项目根目录
cd <项目根目录路径>

# 导入数据库
mysql -u root -p legal_qa < backend/src/main/resources/db/migration/legal_qa_complete.sql
```

**方法二：使用 MySQL 客户端工具（如 Navicat、MySQL Workbench）**

1. 打开 MySQL 客户端工具
2. 连接到 MySQL 服务器
3. 选择或创建 `legal_qa` 数据库
4. 执行 SQL 文件：
   - Navicat: 右键数据库 → 运行 SQL 文件 → 选择 `legal_qa_complete.sql`
   - MySQL Workbench: File → Open SQL Script → 选择文件 → 执行

**方法三：使用 MySQL 命令行导入**

```sql
-- 登录MySQL
mysql -u root -p

-- 使用数据库
USE legal_qa;

-- 导入SQL文件（需要在项目根目录下执行，或使用完整路径）
source backend/src/main/resources/db/migration/legal_qa_complete.sql;
```

**注意：** 如果使用 `source` 命令，需要在项目根目录下执行，或者使用文件的完整绝对路径。

**导入的数据库包含：**

- ✅ 完整的表结构（6 个表）
- ✅ 示例用户数据（admin/123456）
- ✅ 法条数据（legal_articles）
- ✅ 案例数据（legal_cases）
- ✅ 法律概念数据（legal_concepts）
- ✅ 知识库数据（knowledge_base）
- ✅ 问答记录示例（question_answers）

**注意事项：**

- 如果数据库已存在，导入前建议先备份现有数据
- 导入会覆盖现有数据，请谨慎操作
- 导入时间取决于数据量大小（通常几秒到几分钟）

#### 3. 仅初始化表结构（不含数据）

**如果您只想创建表结构而不导入数据，可以使用：**

```powershell
# 执行数据库初始化脚本（仅表结构）
mysql -u root -p legal_qa < backend/src/main/resources/db/migration/schema.sql
```

**方法二：自动创建（JPA 自动建表）**

如果使用 JPA 自动建表，确保 `application.yml` 中配置：

```yaml
spring:
  jpa:
    hibernate:
      ddl-auto: update # 自动更新表结构
```

**注意：** 使用 JPA 自动建表只会创建表结构，不会插入初始数据。

---

### 三、后端配置

#### 1. 修改数据库连接配置

编辑 `backend/src/main/resources/application.yml`：

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/legal_qa?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai
    username: root # 修改为你的MySQL用户名
    password: 123456 # 修改为你的MySQL密码
    driver-class-name: com.mysql.cj.jdbc.Driver
```

#### 2. 配置 DeepSeek API Key

**方法一：在配置文件中直接配置**

```yaml
deepseek:
  api:
    url: https://api.deepseek.com/v1/chat/completions
    api-key: sk-your-api-key-here # 替换为你的DeepSeek API Key
    model: deepseek-chat
    timeout: 120000 # 120秒超时
```

**方法二：使用环境变量（推荐，更安全）**

```yaml
deepseek:
  api:
    api-key: ${DEEPSEEK_API_KEY:sk-default-key} # 优先使用环境变量
```

然后在系统环境变量中设置：

```powershell
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-your-api-key-here"

# 或在系统环境变量中永久设置
```

#### 3. 其他配置（可选）

```yaml
# JWT配置
jwt:
  secret: legal-qa-system-secret-key-2024 # 生产环境请修改为复杂密钥
  expiration: 86400000 # Token过期时间（24小时）

# 文件上传配置
file:
  upload:
    path: ./uploads/ # 上传文件保存路径
    max-size: 10MB # 最大文件大小
```

---

### 四、前端配置

#### 1. 检查代理配置

确认 `frontend/vue.config.js` 中的代理配置正确：

```javascript
module.exports = {
  devServer: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8080", // 后端地址
        changeOrigin: true,
        ws: true,
        secure: false,
      },
    },
  },
};
```

---

### 五、启动项目

#### 方式一：手动启动（推荐用于开发）

**步骤 1：启动后端**

```powershell
# 进入后端目录
cd backend

# 清理并编译（首次运行）
mvn clean install

# 启动后端服务
mvn spring-boot:run
```

**等待看到以下信息表示启动成功：**

```
Started LegalQaApplication in X.XXX seconds
```

**后端服务地址：** `http://localhost:8080/api`

**步骤 2：启动前端（新开一个终端）**

```powershell
# 进入前端目录
cd frontend

# 安装依赖（首次运行需要）
npm install

# 启动前端开发服务器
npm run serve
```

**等待看到以下信息表示启动成功：**

```
App running at:
- Local:   http://localhost:3000/
```

**前端服务地址：** `http://localhost:3000`

---

#### 方式二：使用 PowerShell 脚本启动（Windows）

**创建启动脚本 `start-backend.ps1`：**

```powershell
# start-backend.ps1
cd backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "mvn spring-boot:run"
```

**创建启动脚本 `start-frontend.ps1`：**

```powershell
# start-frontend.ps1
cd frontend
if (-not (Test-Path node_modules)) {
    Write-Host "Installing dependencies..."
    npm install
}
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run serve"
```

**执行启动：**

```powershell
.\start-backend.ps1
.\start-frontend.ps1
```

---

#### 方式三：一键启动（处理端口占用）

**创建 `start-all.ps1`：**

```powershell
# start-all.ps1
# 清理端口占用
$conn8080 = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
if ($conn8080) {
    $procId = $conn8080.OwningProcess
    Write-Host "Killing process $procId on port 8080"
    Stop-Process -Id $procId -Force
}

$conn3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($conn3000) {
    $procId = $conn3000.OwningProcess
    Write-Host "Killing process $procId on port 3000"
    Stop-Process -Id $procId -Force
}

# 启动后端
Write-Host "Starting backend..."
$backendPath = Join-Path $PSScriptRoot "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; mvn spring-boot:run"

# 等待后端启动
Start-Sleep -Seconds 5

# 启动前端
Write-Host "Starting frontend..."
$frontendPath = Join-Path $PSScriptRoot "frontend"
if (-not (Test-Path (Join-Path $frontendPath "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Set-Location $frontendPath
    npm install
}
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run serve"

Write-Host "`nBoth services are starting..."
Write-Host "Backend: http://localhost:8080/api"
Write-Host "Frontend: http://localhost:3000"
```

**执行：**

```powershell
.\start-all.ps1
```

---

### 六、验证启动

#### 1. 检查后端

**方法一：访问 API**

```powershell
# 测试法条查询接口
Invoke-WebRequest -Uri "http://localhost:8080/api/legal/article/all" -UseBasicParsing
```

**方法二：浏览器访问**

```
http://localhost:8080/api/legal/article/all
```

**成功响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [...]
}
```

#### 2. 检查前端

**浏览器访问：**

```
http://localhost:3000
```

**应该看到：**

- 首页正常显示
- 可以访问登录页面
- 可以访问智能问答页面

---

## 🔍 常见问题排查

### 问题 1：后端启动失败

**可能原因：**

1. 端口 8080 被占用
2. 数据库连接失败
3. MySQL 服务未启动

**解决方案：**

```powershell
# 检查端口占用
netstat -ano | findstr :8080

# 检查MySQL服务
Get-Service | Where-Object {$_.Name -like "*mysql*"}

# 测试数据库连接
mysql -u root -p -e "USE legal_qa; SHOW TABLES;"
```

### 问题 2：前端启动失败

**可能原因：**

1. 端口 3000 被占用
2. node_modules 未安装
3. Node.js 版本过低

**解决方案：**

```powershell
# 检查端口占用
netstat -ano | findstr :3000

# 重新安装依赖
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install

# 检查Node.js版本
node -v  # 需要 >= 14.0.0
```

### 问题 3：前后端连接失败

**可能原因：**

1. 后端未启动
2. 代理配置错误
3. CORS 配置问题

**解决方案：**

- 检查后端是否在 `http://localhost:8080` 运行
- 检查 `vue.config.js` 中的代理配置
- 检查浏览器控制台的网络请求

### 问题 4：DeepSeek API 调用失败

**可能原因：**

1. API Key 无效或过期
2. 网络连接问题
3. API 额度用完

**解决方案：**

- 检查 `application.yml` 中的 API Key 配置
- 测试网络连接：`ping api.deepseek.com`
- 检查 DeepSeek 账户余额

---

## 📝 项目结构说明

```
Legal-QA-System/
├── backend/                    # 后端SpringBoot项目
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/legal/
│   │   │   │   ├── config/          # 配置类
│   │   │   │   │   ├── CorsConfig.java          # CORS跨域配置
│   │   │   │   │   ├── DeepSeekConfig.java      # DeepSeek API配置
│   │   │   │   │   ├── SecurityConfig.java      # Spring Security配置
│   │   │   │   │   └── WebConfig.java           # Web配置
│   │   │   │   ├── controller/      # 控制器层（REST API）
│   │   │   │   │   ├── AdminController.java     # 管理后台API
│   │   │   │   │   ├── AuthController.java      # 认证API
│   │   │   │   │   ├── LegalArticleController.java  # 法条API
│   │   │   │   │   ├── LegalCaseController.java     # 案例API
│   │   │   │   │   ├── LegalConceptController.java # 概念API
│   │   │   │   │   └── QuestionAnswerController.java # 问答API
│   │   │   │   ├── dto/             # 数据传输对象
│   │   │   │   │   ├── ApiResponse.java         # 统一响应格式
│   │   │   │   │   ├── LoginRequest.java        # 登录请求
│   │   │   │   │   └── RegisterRequest.java     # 注册请求
│   │   │   │   ├── entity/         # 实体类（对应数据库表）
│   │   │   │   │   ├── User.java                # 用户实体
│   │   │   │   │   ├── QuestionAnswer.java     # 问答记录实体
│   │   │   │   │   ├── LegalArticle.java        # 法条实体
│   │   │   │   │   ├── LegalCase.java           # 案例实体
│   │   │   │   │   ├── LegalConcept.java        # 概念实体
│   │   │   │   │   └── KnowledgeBase.java       # 知识库实体
│   │   │   │   ├── repository/     # 数据访问层（JPA Repository）
│   │   │   │   │   ├── UserRepository.java
│   │   │   │   │   ├── QuestionAnswerRepository.java
│   │   │   │   │   ├── LegalArticleRepository.java
│   │   │   │   │   ├── LegalCaseRepository.java
│   │   │   │   │   ├── LegalConceptRepository.java
│   │   │   │   │   └── KnowledgeBaseRepository.java
│   │   │   │   ├── service/        # 业务逻辑层
│   │   │   │   │   ├── DeepSeekService.java      # DeepSeek API服务（核心）
│   │   │   │   │   ├── QuestionAnswerService.java # 问答服务（核心）
│   │   │   │   │   ├── UserService.java          # 用户服务
│   │   │   │   │   ├── LegalArticleService.java  # 法条服务
│   │   │   │   │   ├── LegalCaseService.java     # 案例服务
│   │   │   │   │   ├── LegalConceptService.java  # 概念服务
│   │   │   │   │   └── KnowledgeBaseService.java # 知识库服务
│   │   │   │   ├── util/           # 工具类
│   │   │   │   │   ├── JwtUtil.java             # JWT工具
│   │   │   │   │   └── PasswordHashGenerator.java # 密码生成工具
│   │   │   │   └── LegalQaApplication.java      # 主启动类
│   │   │   └── resources/
│   │   │       ├── application.yml               # 应用配置
│   │   │       └── db/migration/                 # 数据库迁移脚本
│   │   │           ├── schema.sql                # 数据库表结构
│   │   │           └── insert_knowledge_base_data.sql # 初始数据
│   │   └── pom.xml                # Maven依赖配置
│   └── README.md
├── frontend/                      # 前端Vue2项目
│   ├── src/
│   │   ├── api/                   # API接口封装
│   │   │   ├── api.js             # API方法定义
│   │   │   └── request.js        # Axios请求封装
│   │   ├── assets/                # 静态资源
│   │   ├── components/            # 公共组件
│   │   │   └── NavBar.vue        # 导航栏组件
│   │   ├── router/                # 路由配置
│   │   │   └── index.js          # 路由定义
│   │   ├── store/                 # Vuex状态管理
│   │   │   ├── index.js          # Store主文件
│   │   │   └── modules/
│   │   │       └── user.js       # 用户状态模块
│   │   ├── styles/                # 样式文件
│   │   │   └── global.css       # 全局样式
│   │   ├── views/                 # 页面组件
│   │   │   ├── admin/            # 管理后台页面
│   │   │   │   ├── Dashboard.vue # 仪表盘
│   │   │   │   ├── Knowledge.vue # 知识库管理
│   │   │   │   ├── Layout.vue    # 布局组件
│   │   │   │   └── QA.vue        # 问答管理
│   │   │   ├── Chat.vue          # 智能问答页面
│   │   │   ├── Home.vue          # 首页
│   │   │   ├── Knowledge.vue     # 法律知识库页面
│   │   │   ├── Login.vue         # 登录/注册页面
│   │   │   └── Profile.vue       # 个人中心
│   │   ├── App.vue               # 根组件
│   │   └── main.js               # 入口文件
│   ├── public/
│   │   └── index.html            # HTML模板
│   ├── package.json              # NPM依赖配置
│   ├── vue.config.js             # Vue CLI配置
│   └── README.md
└── README.md                      # 项目说明文档
```

---

## 🎯 核心业务流程

### 智能问答流程详解

```
1. 用户在前端输入问题
   ↓
2. 前端发送POST请求到 /api/qa/ask
   ↓
3. QuestionAnswerController接收请求
   ↓
4. QuestionAnswerService.processQuestion()处理：

   a) 问题分类
      → DeepSeekService.classifyQuestion()
      → 返回：法条查询/概念定义/程序咨询/案例分析

   b) 实体识别
      → DeepSeekService.extractEntities()
      → 返回：{法条: [...], 罪名: [...], 机构: [...]}

   c) 知识检索
      → retrieveKnowledge()
      → 从数据库检索相关法条、案例、概念

   d) 生成答案
      → DeepSeekService.generateAnswer(question, context)
      → 调用DeepSeek API，传入问题+知识库上下文

   e) 检索相关法条和案例
      → findRelatedLaws() / findRelatedCases()

   f) 可信度评估
      → DeepSeekService.evaluateConfidence()
      → 评估答案的可信度（0-1分）

   g) 保存问答记录
      → questionAnswerRepository.save()
   ↓
5. 返回结果给前端
   {
     answer: "生成的答案",
     questionType: "问题类型",
     confidenceScore: 0.95,
     relatedLaws: [...],
     relatedCases: [...],
     entities: {...}
   }
   ↓
6. 前端展示结果
```

---

## 🔐 安全机制

### 1. 身份认证

- **JWT Token**：无状态认证，Token 有效期 24 小时
- **密码加密**：使用 BCrypt 加密存储

### 2. 权限控制

- **普通用户**：可以提问、查看知识库
- **管理员**：可以管理知识库、查看统计数据

### 3. CORS 配置

- 允许跨域请求（开发环境）
- 生产环境建议配置具体的允许域名

---

## 📈 性能优化

### 1. 数据库优化

- 关键字段建立索引
- 使用 JPA 分页查询
- 连接池配置

### 2. API 优化

- HTTP 连接池复用
- 请求超时设置（120 秒）
- 自动重试机制（3 次）

### 3. 前端优化

- 路由懒加载
- 组件按需加载
- Axios 请求拦截和重试

---

## 🎓 学习建议

### 对于初学者

1. 先理解整体架构和流程
2. 从简单的 Controller 和 Service 开始阅读
3. 理解 JPA Repository 的使用
4. 学习 Vue Router 和 Vuex 的使用

### 对于进阶开发者

1. 深入研究 DeepSeekService 的实现
2. 理解问题分类和实体识别的 Prompt 设计
3. 优化知识检索算法
4. 改进可信度评估机制

---

## 📚 相关资源

- [Spring Boot 官方文档](https://spring.io/projects/spring-boot)
- [Vue.js 官方文档](https://v2.vuejs.org/)
- [DeepSeek API 文档](https://platform.deepseek.com/api-docs/)
- [Element UI 文档](https://element.eleme.cn/#/zh-CN)

---

## ✅ 启动检查清单

在启动项目前，请确认：

- [ ] JDK 1.8+ 已安装
- [ ] Maven 3.6+ 已安装
- [ ] Node.js 14+ 已安装
- [ ] MySQL 8.0+ 已安装并运行
- [ ] 数据库 `legal_qa` 已创建
- [ ] `application.yml` 中数据库配置正确
- [ ] DeepSeek API Key 已配置
- [ ] 端口 8080 和 3000 未被占用
- [ ] 前端依赖已安装（`npm install`）

---

**祝您使用愉快！如有问题，请查看项目 README 或联系维护者。**
