# 法律概念数据导入指南

## 概述

本指南介绍如何使用 `import_disc_lawllm_concepts.py` 脚本将法律概念数据导入到 `legal_concepts` 表中。

## 脚本功能

- ✅ 支持多种数据格式：JSON、CSV、TXT
- ✅ 自动检测法律领域
- ✅ 自动提取相关概念
- ✅ 数据去重和验证
- ✅ 批量导入，支持事务回滚
- ✅ 详细的导入统计信息

## 使用方法

### 1. 从JSON文件导入

```bash
python scripts/import_disc_lawllm_concepts.py scripts/legal_concepts_sample.json
```

**JSON格式示例：**
```json
[
  {
    "name": "合同",
    "definition": "当事人之间设立、变更、终止民事权利义务关系的协议",
    "explanation": "详细解释...",
    "law_type": "民法",
    "related_concepts": "协议,民事行为,权利义务"
  }
]
```

### 2. 从CSV文件导入

```bash
python scripts/import_disc_lawllm_concepts.py data/concepts.csv
```

**CSV格式示例：**
```csv
name,definition,explanation,law_type,related_concepts
合同,当事人之间设立...,详细解释...,民法,"协议,民事行为"
故意伤害罪,故意非法损害...,详细解释...,刑法,"故意,伤害,犯罪"
```

### 3. 从TXT文件导入

```bash
python scripts/import_disc_lawllm_concepts.py data/concepts.txt
```

**TXT格式示例：**
```
合同|当事人之间设立、变更、终止民事权利义务关系的协议|详细解释...|民法
故意伤害罪|故意非法损害他人身体健康的行为|详细解释...|刑法
```

### 4. 使用示例数据

如果不提供文件路径，脚本会使用内置的示例数据：

```bash
python scripts/import_disc_lawllm_concepts.py
```

## 数据字段说明

### 必需字段
- `name` (概念名称): 唯一标识，最大长度100字符

### 可选字段
- `definition` (定义): 简洁的定义，最大长度2000字符
- `explanation` (详细解释): 详细的解释说明，最大长度5000字符
- `law_type` (法律领域): 所属法律领域，如：民法、刑法、行政法等
- `related_concepts` (相关概念): 相关概念列表，用逗号分隔，最大长度1000字符

## 支持的法律领域

脚本会自动检测以下法律领域：
- **民法**: 合同、物权、侵权、婚姻、继承等
- **刑法**: 犯罪、故意伤害、诈骗、盗窃等
- **劳动法**: 劳动合同、劳动争议、加班费等
- **行政法**: 行政行为、行政许可、行政处罚等
- **知识产权法**: 著作权、专利权、商标权等
- **消费者权益保护法**: 消费者、经营者、商品服务等
- **程序法**: 诉讼、程序、审理、判决等

## 数据去重

脚本使用 `ON DUPLICATE KEY UPDATE` 语句处理重复数据：
- 如果概念名称已存在，会更新其他字段
- 不会创建重复的概念记录

## 导入统计

导入完成后，脚本会显示：
- 成功导入的数量
- 跳过（重复）的数量
- 失败的数量
- 各法律领域的分布情况

## 从DISC-LawLLM数据集导入

### 方法1: 直接使用GitHub数据

1. **克隆DISC-LawLLM仓库**
   ```bash
   git clone https://github.com/FudanDISC/DISC-LawLLM.git
   cd DISC-LawLLM
   ```

2. **查找概念数据文件**
   - 查看数据集目录结构
   - 找到包含法律概念的文件（通常是JSON或CSV格式）

3. **转换数据格式**
   - 如果数据格式不完全匹配，需要先转换
   - 确保字段名匹配：name, definition, explanation, law_type, related_concepts

4. **导入数据**
   ```bash
   python scripts/import_disc_lawllm_concepts.py path/to/concepts.json
   ```

### 方法2: 使用示例数据

如果无法直接获取DISC-LawLLM数据，可以使用项目提供的示例数据：

```bash
python scripts/import_disc_lawllm_concepts.py scripts/legal_concepts_sample.json
```

## 数据验证

导入后，可以通过以下SQL验证数据：

```sql
-- 查看所有概念
SELECT * FROM legal_concepts;

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

### Q1: 导入时出现编码错误
**A**: 确保数据文件使用UTF-8编码保存。

### Q2: 某些概念没有自动检测到法律领域
**A**: 脚本会自动检测，如果检测不准确，可以在数据文件中手动指定 `law_type` 字段。

### Q3: 相关概念没有自动提取
**A**: 相关概念的自动提取依赖于已存在的概念名称。如果数据集中没有相关概念，可以在数据文件中手动指定 `related_concepts` 字段。

### Q4: 如何更新已存在的概念
**A**: 脚本会自动更新已存在的概念（基于概念名称）。重新运行导入脚本即可更新数据。

## 数据质量建议

1. **概念名称**: 
   - 使用标准法律术语
   - 保持唯一性
   - 长度控制在100字符以内

2. **定义**: 
   - 简洁准确
   - 符合法律规范
   - 长度建议200-500字

3. **详细解释**: 
   - 可包含示例和适用场景
   - 长度建议500-2000字

4. **法律领域**: 
   - 使用标准分类
   - 一个概念通常属于一个主要领域

5. **相关概念**: 
   - 建议3-10个相关概念
   - 用逗号分隔

## 扩展数据

如果需要添加更多概念，可以：

1. **编辑JSON文件**: 在 `legal_concepts_sample.json` 中添加新概念
2. **创建新文件**: 创建新的JSON/CSV/TXT文件
3. **从其他数据源导入**: 使用脚本支持的数据格式

## 联系与支持

如有问题，请参考：
- 项目文档
- DISC-LawLLM GitHub: https://github.com/FudanDISC/DISC-LawLLM
- 脚本注释和代码













