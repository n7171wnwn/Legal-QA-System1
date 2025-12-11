# 法律术语词典数据提取指南

## 概述

本指南介绍如何使用 `extract_from_legal_dictionary.py` 脚本从各种格式的法律术语词典中提取数据并导入到 `legal_concepts` 表中。

## 脚本功能

- ✅ 支持多种词典格式：文本、Markdown、结构化文本、JSON、CSV
- ✅ 自动检测法律领域
- ✅ 智能提取概念名称和定义
- ✅ 数据去重和验证
- ✅ 批量导入，支持事务回滚

## 支持的格式

### 1. 文本格式（Text）

**格式示例：**
```
合同：当事人之间设立、变更、终止民事权利义务关系的协议
物权：权利人依法对特定的物享有直接支配和排他的权利
```

**使用方法：**
```bash
python scripts/extract_from_legal_dictionary.py dictionary.txt text
```

### 2. Markdown格式

**格式示例：**
```markdown
# 合同
当事人之间设立、变更、终止民事权利义务关系的协议。

合同是民事法律行为的一种...

# 物权
权利人依法对特定的物享有直接支配和排他的权利。
```

**使用方法：**
```bash
python scripts/extract_from_legal_dictionary.py dictionary.md markdown
```

### 3. 结构化文本格式

**格式示例：**
```
合同|当事人之间设立、变更、终止民事权利义务关系的协议|详细解释...|民法|协议,民事行为
物权|权利人依法对特定的物享有直接支配和排他的权利|详细解释...|民法|所有权,用益物权
```

**使用方法：**
```bash
python scripts/extract_from_legal_dictionary.py dictionary.txt structured
```

### 4. JSON格式

**格式示例：**
```json
[
  {
    "name": "合同",
    "definition": "当事人之间设立、变更、终止民事权利义务关系的协议",
    "explanation": "详细解释...",
    "law_type": "民法",
    "related_concepts": "协议,民事行为"
  }
]
```

**使用方法：**
```bash
python scripts/extract_from_legal_dictionary.py dictionary.json json
```

### 5. CSV格式

**格式示例：**
```csv
name,definition,explanation,law_type,related_concepts
合同,当事人之间设立...,详细解释...,民法,"协议,民事行为"
物权,权利人依法对...,详细解释...,民法,"所有权,用益物权"
```

**使用方法：**
```bash
python scripts/extract_from_legal_dictionary.py dictionary.csv csv
```

## 自动格式检测

如果不指定格式类型，脚本会自动根据文件扩展名检测：

```bash
python scripts/extract_from_legal_dictionary.py dictionary.txt
# 自动检测为文本格式

python scripts/extract_from_legal_dictionary.py dictionary.json
# 自动检测为JSON格式

python scripts/extract_from_legal_dictionary.py dictionary.md
# 自动检测为Markdown格式
```

## 从常见法律术语词典提取

### 方法1: 从电子版词典提取

如果你有电子版的法律术语词典（PDF、Word、TXT等），可以：

1. **转换为文本格式**
   - PDF → TXT：使用PDF阅读器或转换工具
   - Word → TXT：另存为纯文本格式

2. **整理格式**
   - 确保格式为：`概念名：定义` 或 `概念名——定义`
   - 每行一个概念

3. **导入数据**
   ```bash
   python scripts/extract_from_legal_dictionary.py dictionary.txt text
   ```

### 方法2: 从在线词典提取

1. **获取词典内容**
   - 访问在线法律术语词典网站
   - 复制或下载词典内容

2. **保存为文本文件**
   - 保存为 `.txt` 文件
   - 确保编码为 UTF-8

3. **导入数据**
   ```bash
   python scripts/extract_from_legal_dictionary.py dictionary.txt text
   ```

### 方法3: 使用项目提供的数据集

项目已经提供了两个数据集文件：

1. **基础数据集**：`legal_concepts_sample.json`（21条）
2. **扩展数据集**：`legal_concepts_extended.json`（33条）
3. **词典数据集**：`legal_dictionary_comprehensive.json`（28条）

**导入方法：**
```bash
# 导入基础数据集
python scripts/import_disc_lawllm_concepts.py scripts/legal_concepts_sample.json

# 导入扩展数据集
python scripts/import_disc_lawllm_concepts.py scripts/legal_concepts_extended.json

# 导入词典数据集
python scripts/import_disc_lawllm_concepts.py scripts/legal_dictionary_comprehensive.json
```

## 数据提取规则

### 文本格式提取规则

脚本会识别以下格式：
- `概念名：定义`
- `概念名——定义`
- `概念名 定义`

### 自动法律领域检测

脚本会根据概念名称和定义内容自动检测法律领域：
- **民法**：合同、物权、侵权、婚姻、继承等
- **刑法**：犯罪、故意、伤害、诈骗、盗窃等
- **劳动法**：劳动、加班、工资、劳动合同等
- **行政法**：行政、政府、机关、处罚等
- **知识产权法**：专利、商标、著作权等
- **消费者权益保护法**：消费、消费者、经营者等
- **程序法**：诉讼、程序、审理、判决等

## 数据验证

导入后，可以通过以下SQL验证数据：

```sql
-- 查看所有概念
SELECT name, law_type, LEFT(definition, 50) as def 
FROM legal_concepts 
ORDER BY law_type, name;

-- 按法律领域统计
SELECT law_type, COUNT(*) as count 
FROM legal_concepts 
GROUP BY law_type 
ORDER BY count DESC;

-- 查看特定法律领域的概念
SELECT name, definition 
FROM legal_concepts 
WHERE law_type = '民法' 
LIMIT 10;
```

## 常见问题

### Q1: 提取的概念数量为0

**可能原因：**
- 文件格式不匹配
- 文件编码不是UTF-8
- 格式不符合提取规则

**解决方法：**
- 检查文件格式是否正确
- 确保文件使用UTF-8编码
- 尝试手动指定格式类型

### Q2: 法律领域检测不准确

**解决方法：**
- 在数据文件中手动指定 `law_type` 字段
- 或者在导入后手动更新数据库

### Q3: 某些概念没有提取到定义

**解决方法：**
- 检查原始文件格式
- 可能需要手动整理数据格式
- 或者直接在JSON/CSV文件中提供完整数据

### Q4: 如何批量处理多个词典文件

**解决方法：**
```bash
# 创建批处理脚本
for file in dictionary*.txt; do
    python scripts/extract_from_legal_dictionary.py "$file" text
done
```

## 数据质量建议

1. **概念名称**：
   - 使用标准法律术语
   - 保持唯一性
   - 长度控制在100字符以内

2. **定义**：
   - 简洁准确
   - 符合法律规范
   - 长度建议200-500字

3. **详细解释**：
   - 可包含示例和适用场景
   - 长度建议500-2000字

4. **法律领域**：
   - 使用标准分类
   - 一个概念通常属于一个主要领域

## 推荐的法律术语词典

1. **《法律术语词典》**（法律出版社）
2. **《法学大辞典》**（中国政法大学出版社）
3. **《法律辞典》**（商务印书馆）
4. **在线法律术语词典**：
   - 中国法律术语网
   - 法律词典在线

## 扩展数据集

当前数据库已包含 **82条法律概念**，涵盖：
- 民法：18条
- 刑法：15条
- 劳动法：11条
- 知识产权法：11条
- 行政法：9条
- 程序法：9条
- 消费者权益保护法：9条

## 下一步

1. **继续扩展**：从更多法律术语词典提取数据
2. **数据验证**：定期检查数据质量和准确性
3. **数据更新**：保持数据的时效性

## 联系与支持

如有问题，请参考：
- 项目文档
- 脚本注释和代码
- 相关法律术语词典













