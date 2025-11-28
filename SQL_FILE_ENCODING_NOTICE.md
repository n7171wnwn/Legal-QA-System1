# SQL 文件编码说明

## ⚠️ 如果看到乱码

`legal_qa_complete.sql` 文件使用 **UTF-8** 编码保存，如果您的编辑器显示乱码，请按照以下方法解决：

## 🔧 解决方法

### 方法一：在编辑器中设置编码（推荐）

**VS Code / Cursor：**
1. 打开文件后，点击右下角的编码显示（如 "UTF-8" 或 "GBK"）
2. 选择 **"通过编码重新打开"** 或 **"Reopen with Encoding"**
3. 选择 **"UTF-8"**

**Notepad++：**
1. 菜单栏：**编码** → **转为 UTF-8 编码**
2. 或者：**编码** → **使用 UTF-8 编码**

**Sublime Text：**
1. 菜单栏：**File** → **Reopen with Encoding** → **UTF-8**

**IntelliJ IDEA / PyCharm：**
1. 右键文件 → **File Encoding** → 选择 **UTF-8**
2. 或者：**File** → **Settings** → **Editor** → **File Encodings** → 设置为 UTF-8

### 方法二：直接导入数据库（无需查看文件内容）

**您不需要查看SQL文件的内容，直接导入即可：**

```powershell
# 在项目根目录下执行
mysql -u root -p legal_qa < backend/src/main/resources/db/migration/legal_qa_complete.sql
```

MySQL 会自动识别 UTF-8 编码，即使编辑器显示乱码，导入也不会受影响。

### 方法三：验证文件编码

**使用 PowerShell 验证：**

```powershell
# 检查文件是否可以正常读取
Get-Content backend/src/main/resources/db/migration/legal_qa_complete.sql -Encoding UTF8 -TotalCount 20

# 如果能看到正常的SQL语句和中文字符，说明文件本身没问题
```

## ✅ 文件信息

- **文件位置：** `backend/src/main/resources/db/migration/legal_qa_complete.sql`
- **文件大小：** 约 28-34 MB
- **编码格式：** UTF-8
- **字符集：** utf8mb4

## 📝 重要提示

1. **不需要查看文件内容**：SQL 文件是用于导入数据库的，不需要手动阅读
2. **导入不受影响**：即使编辑器显示乱码，使用 `mysql` 命令导入时，MySQL 会自动正确处理 UTF-8 编码
3. **文件本身正常**：文件已正确导出，包含完整的数据库结构和数据

## 🔍 如何确认文件正常

导入数据库后，验证数据是否正确：

```sql
-- 登录MySQL
mysql -u root -p legal_qa

-- 查看表
SHOW TABLES;

-- 检查中文数据
SELECT title FROM legal_articles LIMIT 5;
SELECT name FROM legal_concepts LIMIT 5;
```

如果能看到正常的中文内容，说明文件完全正常，只是编辑器显示的问题。

---

**总结：如果只是编辑器显示乱码，不影响使用。直接导入数据库即可！** ✅

