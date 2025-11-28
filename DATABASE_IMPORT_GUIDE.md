# 数据库导入指南

本指南将帮助您快速导入完整的 `legal_qa` 数据库，包括表结构和示例数据。

## 📍 重要提示

**项目根目录说明：**

- 项目根目录是包含 `backend` 和 `frontend` 两个文件夹的目录
- 在项目根目录下，您应该能看到 `README.md` 文件
- 所有相对路径都是相对于项目根目录的

**在执行导入命令前，请确保：**

1. 您已经进入项目根目录
2. 或者使用文件的完整绝对路径

## 📦 数据库文件位置

完整数据库导出文件位于（相对于项目根目录）：

```
backend/src/main/resources/db/migration/legal_qa_complete.sql
```

## 📊 数据库内容

导入的数据库包含以下内容：

| 表名               | 说明       | 数据量                       |
| ------------------ | ---------- | ---------------------------- |
| `users`            | 用户表     | 包含示例用户（admin/123456） |
| `legal_articles`   | 法条表     | 法律法规条文数据             |
| `legal_cases`      | 案例表     | 司法案例数据                 |
| `legal_concepts`   | 概念表     | 法律概念定义数据             |
| `knowledge_base`   | 知识库表   | 问答对知识数据               |
| `question_answers` | 问答记录表 | 问答历史记录                 |

## 🚀 导入步骤

### 前置条件

1. ✅ MySQL 8.0+ 已安装并运行
2. ✅ 已创建 `legal_qa` 数据库（如果未创建，见下方说明）

### 步骤 1：创建数据库（如果尚未创建）

```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE legal_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 退出MySQL
exit;
```

### 步骤 2：导入数据库

#### 方法一：使用命令行导入（推荐）

**重要提示：** 请先进入项目根目录（包含 `backend` 和 `frontend` 文件夹的目录）

**Windows PowerShell：**

```powershell
# 进入项目根目录（请根据您的实际路径修改）
cd <项目根目录路径>

# 例如：cd D:\Projects\Legal-QA-System-Clone-main
# 或者：cd C:\Users\YourName\Documents\legal_qa

# 导入数据库（会提示输入MySQL密码）
mysql -u root -p legal_qa < backend/src/main/resources/db/migration/legal_qa_complete.sql
```

**Windows CMD：**

```cmd
# 进入项目根目录
cd <项目根目录路径>

# 导入数据库
mysql -u root -p legal_qa < backend\src\main\resources\db\migration\legal_qa_complete.sql
```

**Linux/Mac：**

```bash
# 进入项目根目录
cd <项目根目录路径>

# 导入数据库
mysql -u root -p legal_qa < backend/src/main/resources/db/migration/legal_qa_complete.sql
```

**如何找到项目根目录？**

- 项目根目录是包含 `backend` 和 `frontend` 两个文件夹的目录
- 在项目根目录下，您应该能看到 `README.md` 文件

**如果 MySQL 不在 PATH 中，使用完整路径：**

```powershell
# Windows示例
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p legal_qa < backend\src\main\resources\db\migration\legal_qa_complete.sql
```

#### 方法二：使用 Navicat 导入

1. 打开 Navicat for MySQL
2. 连接到 MySQL 服务器
3. 右键点击 `legal_qa` 数据库（如果不存在则先创建）
4. 选择 **"运行 SQL 文件"** 或 **"Execute SQL File"**
5. 选择文件：`backend/src/main/resources/db/migration/legal_qa_complete.sql`
6. 点击 **"开始"** 执行
7. 等待导入完成

#### 方法三：使用 MySQL Workbench 导入

1. 打开 MySQL Workbench
2. 连接到 MySQL 服务器
3. 在左侧选择 `legal_qa` 数据库（如果不存在则先创建）
4. 菜单栏：**File** → **Open SQL Script**
5. 选择文件：`backend/src/main/resources/db/migration/legal_qa_complete.sql`
6. 点击执行按钮（⚡ 图标）或按 `Ctrl+Shift+Enter`
7. 等待导入完成

#### 方法四：在 MySQL 命令行中导入

```sql
-- 登录MySQL
mysql -u root -p

-- 使用数据库
USE legal_qa;

-- 导入SQL文件（需要在项目根目录下执行，或使用完整路径）
source backend/src/main/resources/db/migration/legal_qa_complete.sql;

-- 如果不在项目根目录，使用完整路径（请根据您的实际路径修改）
-- source /完整路径/backend/src/main/resources/db/migration/legal_qa_complete.sql;

-- 验证导入
SHOW TABLES;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM legal_articles;
```

## ✅ 验证导入

导入完成后，验证数据是否正确导入：

```sql
-- 登录MySQL
mysql -u root -p legal_qa

-- 查看所有表
SHOW TABLES;

-- 应该看到以下6个表：
-- knowledge_base
-- legal_articles
-- legal_cases
-- legal_concepts
-- question_answers
-- users

-- 检查数据量
SELECT
    'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'legal_articles', COUNT(*) FROM legal_articles
UNION ALL
SELECT 'legal_cases', COUNT(*) FROM legal_cases
UNION ALL
SELECT 'legal_concepts', COUNT(*) FROM legal_concepts
UNION ALL
SELECT 'knowledge_base', COUNT(*) FROM knowledge_base
UNION ALL
SELECT 'question_answers', COUNT(*) FROM question_answers;

-- 测试登录用户（密码：123456）
SELECT username, nickname, user_type FROM users WHERE username = 'admin';
```

## 🔐 默认账号信息

导入后可以使用以下账号登录系统：

| 用户名  | 密码     | 类型     | 说明         |
| ------- | -------- | -------- | ------------ |
| `admin` | `123456` | 管理员   | 拥有所有权限 |
| `user1` | `123456` | 普通用户 | 基础功能权限 |

**⚠️ 安全提示：** 生产环境请立即修改默认密码！

## ⚠️ 注意事项

### 1. 数据覆盖警告

- ⚠️ **导入会覆盖现有数据**：如果 `legal_qa` 数据库已存在数据，导入会清空并替换所有数据
- 💡 **建议**：导入前先备份现有数据库

### 2. 备份现有数据库（如果已有数据）

```powershell
# 导出现有数据库作为备份
mysqldump -u root -p legal_qa > legal_qa_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql
```

### 3. 字符编码

- 确保数据库使用 `utf8mb4` 字符集
- SQL 文件已包含字符集设置，导入时会自动应用

### 4. 导入时间

- 导入时间取决于数据量大小
- 通常需要几秒到几分钟
- 如果数据量很大（>100MB），请耐心等待

### 5. 权限问题

如果遇到权限错误：

```sql
-- 确保用户有足够权限
GRANT ALL PRIVILEGES ON legal_qa.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

## 🔧 常见问题排查

### 问题 1：找不到 SQL 文件

**错误信息：**

```
ERROR 2 (HY000): File 'backend/src/main/resources/db/migration/legal_qa_complete.sql' not found
```

**解决方案：**

- 确认当前工作目录是项目根目录（包含 `backend` 和 `frontend` 文件夹）
- 检查文件是否存在：

  ```powershell
  # Windows PowerShell
  Test-Path backend/src/main/resources/db/migration/legal_qa_complete.sql

  # Linux/Mac
  ls backend/src/main/resources/db/migration/legal_qa_complete.sql
  ```

- 如果文件不存在，请确认您已下载完整的项目代码
- 如果使用 `source` 命令，确保在项目根目录下执行，或使用完整绝对路径

### 问题 2：字符编码错误

**错误信息：**

```
ERROR 1366 (HY000): Incorrect string value
```

**解决方案：**

```sql
-- 确保数据库使用utf8mb4
ALTER DATABASE legal_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 问题 3：表已存在错误

**错误信息：**

```
ERROR 1050 (42S01): Table 'xxx' already exists
```

**解决方案：**

- 如果表已存在且想保留数据，不要导入完整 SQL 文件
- 如果表已存在但想重新导入，先删除表：

```sql
DROP DATABASE legal_qa;
CREATE DATABASE legal_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 问题 4：导入速度慢

**可能原因：**

- 数据量较大
- MySQL 配置不当

**优化建议：**

```sql
-- 临时禁用索引更新（导入完成后会自动重建）
SET unique_checks=0;
SET foreign_key_checks=0;
-- 导入SQL文件
-- ...
SET unique_checks=1;
SET foreign_key_checks=1;
```

### 问题 5：MySQL 命令找不到

**Windows 解决方案：**

```powershell
# 将MySQL添加到PATH环境变量
# 或使用完整路径
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

## 📝 仅导入表结构（不含数据）

如果您只需要表结构而不需要示例数据，可以使用：

```powershell
mysql -u root -p legal_qa < backend/src/main/resources/db/migration/schema.sql
```

这个文件只包含表结构定义，不包含数据。

## 🔄 重新导入

如果需要重新导入数据库：

```sql
-- 1. 删除现有数据库（谨慎操作！）
DROP DATABASE legal_qa;

-- 2. 重新创建数据库
CREATE DATABASE legal_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. 重新导入
-- 使用上述任一导入方法
```

## 📞 获取帮助

如果遇到问题：

1. 检查 MySQL 服务是否运行
2. 确认数据库连接配置正确
3. 查看 MySQL 错误日志
4. 参考主文档：`PROJECT_ARCHITECTURE_GUIDE.md`

---

**导入完成后，您就可以启动项目并开始使用了！** 🎉
