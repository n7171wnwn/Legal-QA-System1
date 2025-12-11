#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将法条表中的劳动相关案例数据迁移到案例表
"""

import pymysql
import re
from datetime import datetime

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

def is_labor_case(title, content, article_number):
    """判断是否为劳动相关案例"""
    if not title:
        return False
    
    # 案例特征关键词
    case_keywords = [
        '劳动者超时加班发生工伤',
        '劳动者拒绝违法超时加班',
        '劳动者与用人单位订立放弃加班费',
        '劳动者在离职文件上签字确认加班费',
        '用人单位未按规章制度履行加班审批',
        '用人单位未与劳动者协商一致增加工作任务',
        '用人单位以规章制度形式否认劳动者加班',
        '用人单位与劳动者约定实行包薪制',
        '是否', '能否', '是否有权', '是否有效', '是否承担'
    ]
    
    # 如果标题是问题形式（包含"是否"、"能否"等），很可能是案例
    if any(kw in title for kw in ['是否', '能否', '是否有权', '是否有效', '是否承担']):
        # 排除明显的法条格式（如"第X条"）
        if not re.match(r'^第[一二三四五六七八九十百千万\d]+[条章节]', title):
            return True
    
    # 如果内容中有"基本案情"等案例特征
    if content and '基本案情' in content:
        return True
    
    # 如果标题包含明确的案例关键词
    if any(kw in title for kw in case_keywords[:8]):  # 前8个是具体的案例标题
        return True
    
    return False

def extract_case_info(content):
    """从案例内容中提取信息"""
    case_type = None
    court_name = None
    judge_date = None
    dispute_point = None
    judgment_result = None
    
    if not content:
        return case_type, court_name, judge_date, dispute_point, judgment_result
    
    # 提取案由（通常是"劳动纠纷"、"劳动争议"等）
    if '劳动' in content[:500]:
        case_type = '劳动争议'
    
    # 提取法院名称
    court_patterns = [
        r'([^，。！？\n]{0,50}法院)',
        r'([^，。！？\n]{0,50}仲裁委员会)',
    ]
    for pattern in court_patterns:
        match = re.search(pattern, content[:2000])
        if match:
            court_name = match.group(1).strip()[:200]
            if '法院' in court_name or '仲裁委员会' in court_name:
                break
    
    # 提取判决日期
    date_patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, content[:2000])
        if match:
            year, month, day = match.groups()
            try:
                judge_date = datetime(int(year), int(month), int(day))
            except:
                pass
            if judge_date:
                break
    
    # 提取争议点（通常是标题本身）
    dispute_point = None
    
    # 提取判决结果
    result_patterns = [
        r'判决[：:]\s*(.+?)(?:\n\n|$)',
        r'裁判结果[：:]\s*(.+?)(?:\n\n|$)',
    ]
    for pattern in result_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            judgment_result = match.group(1).strip()[:2000]
            break
    
    return case_type, court_name, judge_date, dispute_point, judgment_result

conn = pymysql.connect(**db_config)
cursor = conn.cursor()

print("=" * 80)
print("将法条表中的劳动相关案例数据迁移到案例表")
print("=" * 80)

# 步骤1: 查找所有劳动相关案例数据
print("\n【步骤1】查找劳动相关案例数据...")
cursor.execute("""
    SELECT id, title, article_number, content, law_type, publish_org, publish_date, create_time
    FROM legal_articles
    WHERE is_valid = 1
    AND (title LIKE '%劳动者%' OR content LIKE '%劳动者%')
""")

all_articles = cursor.fetchall()
print(f"总共找到 {len(all_articles)} 条包含'劳动者'的数据，开始识别案例...\n")

# 识别案例数据
cases = []
for article in all_articles:
    article_id, title, article_number, content, law_type, publish_org, publish_date, create_time = article
    if is_labor_case(title, content, article_number):
        cases.append(article)
        print(f"发现案例: ID={article_id}, 标题={title}")

print(f"\n总共发现 {len(cases)} 条案例数据")

if len(cases) == 0:
    print("没有找到需要迁移的案例数据")
    conn.close()
    exit(0)

# 步骤2: 迁移数据
print("\n【步骤2】开始迁移数据...")
migrated_count = 0
skipped_count = 0
error_count = 0
migrated_ids = []

for case in cases:
    case_id, title, article_number, content, law_type, publish_org, publish_date, create_time = case
    
    try:
        # 提取案例信息
        case_type, court_name, judge_date, dispute_point, judgment_result = extract_case_info(content)
        
        # 如果没有提取到法院名称，使用发布机构
        if not court_name and publish_org:
            court_name = publish_org
        
        # 如果没有提取到判决日期，使用发布日期
        if not judge_date and publish_date:
            judge_date = publish_date
        
        # 如果没有提取到案由，使用标题作为争议点
        if not dispute_point:
            dispute_point = title[:2000]
        
        # 检查是否已存在（基于标题）
        cursor.execute("SELECT id FROM legal_cases WHERE title = %s", (title,))
        if cursor.fetchone():
            print(f"  - 跳过已存在的案例: {title}")
            skipped_count += 1
            migrated_ids.append(case_id)
            continue
        
        # 插入到 legal_cases 表
        insert_sql = """
            INSERT INTO legal_cases 
            (title, case_type, content, court_name, judge_date, 
             dispute_point, judgment_result, law_type, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_sql, (
            title,
            case_type if case_type else '劳动争议',
            content[:5000] if content else None,
            court_name,
            judge_date,
            dispute_point,
            judgment_result,
            law_type if law_type else '劳动法',
            create_time
        ))
        
        migrated_count += 1
        migrated_ids.append(case_id)
        
        if migrated_count % 5 == 0:
            print(f"  已迁移 {migrated_count} 条案例...")
        
    except Exception as e:
        print(f"  ✗ 迁移案例失败 {title}: {e}")
        error_count += 1
        continue

# 提交事务
conn.commit()

# 步骤3: 从法条表中删除这些案例数据
print("\n【步骤3】从法条表中删除案例数据...")
if migrated_ids:
    placeholders = ','.join(['%s'] * len(migrated_ids))
    cursor.execute(f"DELETE FROM legal_articles WHERE id IN ({placeholders})", migrated_ids)
    deleted_count = cursor.rowcount
    conn.commit()
    print(f"✓ 已删除 {deleted_count} 条案例数据")
else:
    deleted_count = 0
    print("  没有需要删除的数据")

# 显示统计
print("\n" + "=" * 80)
print("迁移完成！统计信息：")
print(f"  成功迁移: {migrated_count} 条案例")
print(f"  跳过记录: {skipped_count} 条（已存在）")
print(f"  错误数量: {error_count} 条")
print(f"  从法条表删除: {deleted_count} 条")
print("=" * 80)

# 验证结果
cursor.execute("SELECT COUNT(*) FROM legal_cases")
case_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM legal_articles WHERE is_valid = 1")
article_count = cursor.fetchone()[0]

print(f"\n当前 legal_cases 表中的案例数: {case_count}")
print(f"当前 legal_articles 表中的法条数: {article_count}")

conn.close()

