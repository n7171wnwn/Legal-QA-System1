# 案例数据导入和显示优化总结

## 完成的工作

### 1. 创建案例导入脚本

**文件**: `backend/scripts/import_cases_data.py`

这是一个专门用于导入案例数据的 Python 脚本，功能包括：

- ✅ 自动扫描 `E:\Laws\Laws\案例` 目录下的所有 markdown 文件
- ✅ 解析案例文件，提取以下信息：
  - 标题（从文件第一行或文件名）
  - 案由（从标题或内容中提取）
  - 审理法院（从内容中提取）
  - 判决日期（从内容中提取）
  - 核心争议点（从"争议焦点"等章节提取）
  - 判决结果（从"裁判结果"等章节提取）
  - 完整案例内容（包括基本案情、案例分析、典型意义等）
  - 法律领域（根据子文件夹自动确定）
- ✅ 自动去重（基于标题）
- ✅ 错误处理和统计信息

### 2. 创建便捷脚本

**文件**: `backend/scripts/import_cases.bat`

Windows 批处理文件，方便一键运行导入脚本。

### 3. 创建使用文档

**文件**: `backend/scripts/IMPORT_CASES_GUIDE.md`

详细的使用指南，包括：
- 安装依赖
- 使用方法
- 数据映射说明
- 常见问题解答

### 4. 优化前端显示

**文件**: `frontend/src/views/Knowledge.vue`

优化了案例详情对话框的显示：

- ✅ 更清晰的信息布局
- ✅ 结构化显示案例内容（支持 markdown 格式转换）
- ✅ 更好的样式和可读性
- ✅ 按章节展示（基本案情、案例分析、典型意义等）

## 使用方法

### 快速开始

1. **安装依赖**（如果还没安装）：
   ```bash
   cd backend/scripts
   pip install pymysql
   ```

2. **运行导入脚本**：
   - Windows: 双击 `import_cases.bat`
   - 或命令行：
     ```bash
     python import_cases_data.py --repo-path E:\Laws\Laws --password hjj060618
     ```

3. **查看结果**：
   - 访问前端知识库页面
   - 切换到"案例"标签
   - 点击案例卡片查看详情

## 数据流程

```
E:\Laws\Laws\案例\
  ├── 劳动人事\
  │   ├── 加班费的仲裁时效应当如何认定.md
  │   └── ...
  ├── 民法典\
  │   └── ...
  └── ...
         ↓
  [import_cases_data.py]
         ↓
  MySQL legal_cases 表
         ↓
  [后端 API]
         ↓
  [前端 Knowledge.vue]
         ↓
  用户查看案例详情
```

## 数据库表结构

案例数据存储在 `legal_cases` 表中，字段包括：

- `id` - 主键
- `title` - 案例标题（必填）
- `case_type` - 案由
- `content` - 案例内容（TEXT，最大约 65KB）
- `court_name` - 审理法院
- `judge_date` - 判决日期
- `dispute_point` - 核心争议点（TEXT，最大约 65KB）
- `judgment_result` - 判决结果（TEXT，最大约 65KB）
- `law_type` - 法律领域
- `create_time` - 创建时间

## 注意事项

1. **内容长度限制**：
   - 脚本会自动截断超过 5000 字符的内容
   - 如果需要存储更长的内容，需要修改数据库表结构（使用 MEDIUMTEXT 或 LONGTEXT）

2. **字段提取**：
   - 某些字段（如案由、法院）可能无法从所有案例中提取
   - 这些字段可以为 NULL，不影响案例的导入和显示

3. **文件格式**：
   - 脚本只处理 `.md` 文件
   - 会自动跳过 `_index.md` 文件

## 后续优化建议

1. **内容长度**：如果案例内容经常超过 5000 字符，可以考虑：
   - 修改数据库表结构，使用 MEDIUMTEXT 或 LONGTEXT
   - 修改脚本中的长度限制

2. **字段提取**：可以进一步优化正则表达式，提高字段提取的准确率

3. **批量更新**：如果需要更新已存在的案例，可以添加更新逻辑

4. **前端优化**：
   - 可以添加案例内容的搜索高亮
   - 可以添加案例的收藏功能
   - 可以添加案例的打印功能

## 相关文件

- `backend/scripts/import_cases_data.py` - 案例导入脚本
- `backend/scripts/import_cases.bat` - Windows 批处理文件
- `backend/scripts/IMPORT_CASES_GUIDE.md` - 使用指南
- `frontend/src/views/Knowledge.vue` - 前端显示页面
- `backend/src/main/java/com/legal/entity/LegalCase.java` - 案例实体类
- `backend/src/main/java/com/legal/service/LegalCaseService.java` - 案例服务类
- `backend/src/main/java/com/legal/controller/LegalCaseController.java` - 案例控制器

