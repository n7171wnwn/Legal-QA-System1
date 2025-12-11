#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试案例数据提取问题
"""

import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# 查看有问题的法院名称
print("=" * 80)
print("检查有问题的法院名称:")
print("=" * 80)
cursor.execute("""
    SELECT id, title, court_name, LEFT(content, 200) as content_preview
    FROM legal_cases
    WHERE court_name IS NOT NULL 
      AND (court_name LIKE '%诉至%' 
           OR court_name LIKE '%不服%'
           OR court_name LIKE '%《%'
           OR LENGTH(court_name) > 100
           OR court_name NOT LIKE '%法院%' AND court_name NOT LIKE '%仲裁委员会%')
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"\nID: {row[0]}")
    print(f"标题: {row[1]}")
    print(f"法院名称: {row[2]}")
    print(f"内容预览: {row[3]}...")
    print("-" * 80)

# 查看缺少关键字段的案例
print("\n\n" + "=" * 80)
print("检查缺少关键字段的案例:")
print("=" * 80)
cursor.execute("""
    SELECT id, title, case_type, court_name, judge_date, 
           dispute_point IS NOT NULL as has_dispute,
           judgment_result IS NOT NULL as has_result
    FROM legal_cases
    WHERE case_type IS NULL 
       OR court_name IS NULL 
       OR (dispute_point IS NULL AND judgment_result IS NULL)
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"\nID: {row[0]}")
    print(f"标题: {row[1][:60]}...")
    print(f"案由: {row[2] or 'NULL'}")
    print(f"法院: {row[3] or 'NULL'}")
    print(f"日期: {row[4] or 'NULL'}")
    print(f"有争议点: {row[5]}")
    print(f"有判决结果: {row[6]}")
    print("-" * 80)

# 查看一个完整案例的内容结构
print("\n\n" + "=" * 80)
print("查看完整案例内容结构（ID=1）:")
print("=" * 80)
cursor.execute("""
    SELECT title, content
    FROM legal_cases
    WHERE id = 1
""")

row = cursor.fetchone()
if row:
    print(f"标题: {row[0]}")
    print(f"\n内容（前1000字符）:")
    print(row[1][:1000] if row[1] else "无内容")
    print("\n" + "=" * 80)
    print("查找关键信息:")
    import re
    
    content = row[1] or ""
    
    # 查找法院
    court_patterns = [
        r'([^，。\n]{2,30}(?:省|市|县|区)?(?:高级|中级|基层)?人民法院)',
        r'([^，。\n]{2,30}(?:劳动争议)?仲裁委员会)',
    ]
    print("\n可能的法院名称:")
    for pattern in court_patterns:
        matches = re.findall(pattern, content)
        for match in matches[:5]:  # 只显示前5个
            if len(match) < 50:
                print(f"  - {match}")
    
    # 查找日期
    date_patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
    ]
    print("\n可能的日期:")
    for pattern in date_patterns:
        matches = re.findall(pattern, content)
        for match in matches[:3]:  # 只显示前3个
            print(f"  - {match[0]}年{match[1]}月{match[2]}日")
    
    # 查找争议点
    dispute_patterns = [
        r'争议[焦点|点|问题][：:]\s*(.+?)(?:\n\n|\n##|$)',
        r'核心争议[：:]\s*(.+?)(?:\n\n|\n##|$)',
    ]
    print("\n可能的争议点:")
    for pattern in dispute_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches[:2]:  # 只显示前2个
            dispute = match.strip()[:200]
            print(f"  - {dispute}...")
    
    # 查找判决结果
    result_patterns = [
        r'判决[结果|内容][：:]\s*(.+?)(?:\n\n|\n##|$)',
        r'裁判[结果|内容][：:]\s*(.+?)(?:\n\n|\n##|$)',
    ]
    print("\n可能的判决结果:")
    for pattern in result_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches[:2]:  # 只显示前2个
            result = match.strip()[:200]
            print(f"  - {result}...")

cursor.close()
conn.close()













