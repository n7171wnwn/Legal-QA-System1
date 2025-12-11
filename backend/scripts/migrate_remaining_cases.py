#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将法条表中剩余的案例数据迁移到案例表（排除司法解释）
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

def is_real_case_not_interpretation(title, content, article_number):
    """判断是否为真正的案例（排除司法解释）"""
    if not title:
        return False
    
    # 排除司法解释（这些应该留在法条表）
    if '最高人民法院' in title or '最高人民检察院' in title:
        if '解释' in title or '规定' in title:
            return False  # 司法解释，不是案例
    
    # 排除法规名称
    if any(kw in title for kw in ['法', '条例', '规定', '办法', '解释', '规则', '细则']):
        # 但如果是"XXX诉XXX案"这种格式，即使包含"法"也可能是案例
        if not ('诉' in title and '案' in title):
            return False  # 是法规
    
    # 明确的案例格式：XXX诉XXX案
    if '诉' in title and '案' in title:
        return True
    
    # 案例特征：问题形式（包含"是否"、"能否"、"如何"等）
    question_keywords = ['是否', '能否', '是否有权', '是否有效', '是否承担', '如何', '怎样', '什么']
    if any(kw in title for kw in question_keywords):
        # 排除明显的法条格式
        if not re.match(r'^第[一二三四五六七八九十百千万\d]+[条章节]', title):
            return True
    
    # 案例特征：内容中有"基本案情"、"裁判规则"等
    if content:
        case_keywords = ['基本案情', '裁判规则', '案例', '判例', '判决', '争议', '纠纷']
        if any(kw in content[:1000] for kw in case_keywords):
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
    
    # 提取案由（根据内容判断）
    if '劳动' in content[:500]:
        case_type = '劳动争议'
    elif '婚姻' in content[:500] or '离婚' in content[:500]:
        case_type = '婚姻家庭纠纷'
    elif '合同' in content[:500]:
        case_type = '合同纠纷'
    elif '消费者' in content[:500]:
        case_type = '消费者权益纠纷'
    elif '侵权' in content[:500]:
        case_type = '侵权纠纷'
    elif '继承' in content[:500]:
        case_type = '继承纠纷'
    
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
        r'裁判规则[：:]\s*(.+?)(?:\n\n|$)',
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
print("将法条表中剩余的案例数据迁移到案例表")
print("=" * 80)

# 步骤1: 查找所有可能的案例数据
print("\n【步骤1】查找案例数据...")
cursor.execute("""
    SELECT id, title, article_number, content, law_type, publish_org, publish_date, create_time
    FROM legal_articles
    WHERE is_valid = 1
""")

all_articles = cursor.fetchall()
print(f"总共 {len(all_articles)} 条法条数据，开始识别案例...\n")

# 识别案例数据
cases = []
for article in all_articles:
    article_id, title, article_number, content, law_type, publish_org, publish_date, create_time = article
    if is_real_case_not_interpretation(title, content, article_number):
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
        
        # 如果没有提取到案由，根据标题判断
        if not case_type:
            if '劳动' in title:
                case_type = '劳动争议'
            elif '婚姻' in title or '离婚' in title:
                case_type = '婚姻家庭纠纷'
            elif '合同' in title:
                case_type = '合同纠纷'
            elif '消费者' in title:
                case_type = '消费者权益纠纷'
            elif '侵权' in title:
                case_type = '侵权纠纷'
            elif '继承' in title:
                case_type = '继承纠纷'
            else:
                case_type = '其他'
        
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
            case_type,
            content[:5000] if content else None,
            court_name,
            judge_date,
            dispute_point,
            judgment_result,
            law_type if law_type else '其他',
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

