#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终检查和修复案例数据
"""

import pymysql
import re
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

def fix_law_type(title: str, content: str, current: str) -> str:
    """修复法律领域分类"""
    text = (title + ' ' + (content or ''))[:2000]
    
    # 更精确的关键词匹配，避免误分类
    # 优先匹配更具体的关键词
    if any(kw in text for kw in ['劳动争议', '劳动合同', '用人单位', '劳动者', '加班费', '劳动仲裁']):
        return '劳动法'
    if any(kw in text for kw in ['故意伤害', '诈骗罪', '盗窃罪', '犯罪', '刑事']):
        return '刑法'
    if any(kw in text for kw in ['行政协议', '行政决定', '政府', '机关']):
        return '行政法'
    if any(kw in text for kw in ['消费者权益', '食品安全', '经营者', '消费者']):
        return '消费者权益保护法'
    if any(kw in text for kw in ['专利', '商标', '著作权', '知识产权']):
        return '知识产权法'
    # 民法是默认的，包含合同、侵权、婚姻、继承等
    if any(kw in text for kw in ['合同', '侵权', '离婚', '继承', '财产', '房屋', '债务', '婚姻', '家庭']):
        return '民法'
    
    return current if current and current != '案例' else '民法'

def fix_court_name(content: str) -> str:
    """修复法院名称"""
    if not content:
        return None
    
    # 精确匹配法院名称
    pattern = r'([^，。\n]{2,30}(?:省|市|县|区|自治区)(?:高级|中级|基层)?人民法院)'
    matches = re.findall(pattern, content)
    
    for match in matches:
        match = match.strip()
        if 5 <= len(match) <= 50:
            # 排除明显错误的
            if not any(kw in match for kw in ['诉至', '不服', '《', '》', '规定', '作为', '向', '应予', '支持', '作出', '撤销', '号', '（', '）']):
                if match.endswith('人民法院'):
                    if not match.startswith(('向', '至', '在', '由', '被', '简称', '申请', '诉', '不服')):
                        if not re.search(r'[0-9（）()]', match):
                            if any(kw in match for kw in ['省', '市', '区', '县']):
                                return match
    return None

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("最终检查和修复...")
print("=" * 60)

# 检查法律领域分布
cursor.execute("SELECT law_type, COUNT(*) as count FROM legal_cases GROUP BY law_type ORDER BY count DESC")
print("\n当前法律领域分布:")
for row in cursor.fetchall():
    print(f"  {row[0] or 'NULL':<20} : {row[1]}")

# 修复错误分类的法律领域
cursor.execute("SELECT id, title, content, law_type FROM legal_cases")
cases = cursor.fetchall()

fixed_law = 0
for case in cases:
    case_id, title, content, law_type = case
    new_law_type = fix_law_type(title, content or '', law_type)
    if new_law_type != law_type:
        cursor.execute("UPDATE legal_cases SET law_type = %s WHERE id = %s", (new_law_type, case_id))
        fixed_law += 1
        print(f"✓ ID {case_id}: 法律领域 {law_type} -> {new_law_type}")

# 修复法院名称
cursor.execute("SELECT id, title, content, court_name FROM legal_cases WHERE court_name IS NULL OR court_name LIKE '%诉至%' OR court_name LIKE '%不服%' OR court_name LIKE '%《%'")
cases = cursor.fetchall()

fixed_court = 0
for case in cases:
    case_id, title, content, court_name = case
    new_court = fix_court_name(content or '')
    if new_court:
        cursor.execute("UPDATE legal_cases SET court_name = %s WHERE id = %s", (new_court, case_id))
        fixed_court += 1
        print(f"✓ ID {case_id}: 提取法院名称: {new_court}")

conn.commit()
print(f"\n✓ 修复法律领域: {fixed_law} 条")
print(f"✓ 修复法院名称: {fixed_court} 条")

# 最终统计
cursor.execute("""
    SELECT 
        law_type, COUNT(*) as count
    FROM legal_cases
    GROUP BY law_type
    ORDER BY count DESC
""")
print("\n修复后的法律领域分布:")
for row in cursor.fetchall():
    print(f"  {row[0] or 'NULL':<20} : {row[1]}")

cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN court_name IS NOT NULL 
                 AND LENGTH(court_name) <= 100
                 AND court_name NOT LIKE '%诉至%'
                 AND court_name NOT LIKE '%不服%'
                 AND (court_name LIKE '%法院%' OR court_name LIKE '%仲裁委员会%')
            THEN 1 ELSE 0 END) as valid_court
    FROM legal_cases
""")
row = cursor.fetchone()
print(f"\n有效法院名称: {row[1]}/{row[0]} ({row[1]/row[0]*100:.1f}%)")

cursor.close()
conn.close()
print("\n✓ 完成！")













