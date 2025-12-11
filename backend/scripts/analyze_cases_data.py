#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析案例数据，找出问题
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

print("=" * 80)
print("1. 法律领域分布:")
print("=" * 80)
cursor.execute("SELECT law_type, COUNT(*) as count FROM legal_cases GROUP BY law_type ORDER BY count DESC")
for row in cursor.fetchall():
    print(f"  {row[0] or 'NULL':<20} : {row[1]}")

print("\n" + "=" * 80)
print("2. 检查有问题的法律领域:")
print("=" * 80)
cursor.execute("""
    SELECT id, title, law_type, LEFT(content, 100) as content_preview
    FROM legal_cases
    WHERE law_type IS NULL OR law_type = '案例' OR law_type NOT IN ('劳动法', '民法', '刑法', '行政法', '知识产权法', '消费者权益保护法', '程序法')
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"\nID: {row[0]}")
    print(f"  标题: {row[1][:50]}...")
    print(f"  法律领域: {row[2]}")
    print(f"  内容预览: {row[3]}...")

print("\n" + "=" * 80)
print("3. 检查法院名称问题:")
print("=" * 80)
cursor.execute("""
    SELECT id, title, court_name, 
           CASE 
               WHEN court_name IS NULL THEN 'NULL'
               WHEN LENGTH(court_name) > 100 THEN 'TOO_LONG'
               WHEN court_name LIKE '%诉至%' OR court_name LIKE '%不服%' THEN 'INVALID'
               WHEN court_name LIKE '%《%' OR court_name LIKE '%规定%' THEN 'INVALID'
               WHEN court_name NOT LIKE '%法院%' AND court_name NOT LIKE '%仲裁委员会%' THEN 'NO_KEYWORD'
               ELSE 'OK'
           END as status
    FROM legal_cases
    ORDER BY id
    LIMIT 20
""")
for row in cursor.fetchall():
    status = row[3]
    if status != 'OK':
        print(f"\nID: {row[0]} - {status}")
        print(f"  标题: {row[1][:50]}...")
        print(f"  法院: {row[2][:80] if row[2] else 'NULL'}...")

print("\n" + "=" * 80)
print("4. 查看几个完整案例的原始内容结构:")
print("=" * 80)
cursor.execute("""
    SELECT id, title, content
    FROM legal_cases
    WHERE id IN (1, 2, 12, 25)
    ORDER BY id
""")
for row in cursor.fetchall():
    print(f"\n{'='*80}")
    print(f"ID: {row[0]} - {row[1]}")
    print(f"{'='*80}")
    content = row[2] or ''
    # 显示前500字符
    print(content[:500])
    print("...")

print("\n" + "=" * 80)
print("5. 统计各字段完整性:")
print("=" * 80)
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN law_type IS NOT NULL AND law_type != '案例' THEN 1 ELSE 0 END) as valid_law_type,
        SUM(CASE WHEN case_type IS NOT NULL THEN 1 ELSE 0 END) as has_case_type,
        SUM(CASE WHEN court_name IS NOT NULL 
                 AND LENGTH(court_name) <= 100
                 AND court_name NOT LIKE '%诉至%'
                 AND court_name NOT LIKE '%不服%'
                 AND court_name NOT LIKE '%《%'
                 AND (court_name LIKE '%法院%' OR court_name LIKE '%仲裁委员会%')
            THEN 1 ELSE 0 END) as valid_court,
        SUM(CASE WHEN judge_date IS NOT NULL THEN 1 ELSE 0 END) as has_date,
        SUM(CASE WHEN dispute_point IS NOT NULL THEN 1 ELSE 0 END) as has_dispute,
        SUM(CASE WHEN judgment_result IS NOT NULL THEN 1 ELSE 0 END) as has_result
    FROM legal_cases
""")
row = cursor.fetchone()
print(f"总案例数: {row[0]}")
print(f"有效法律领域: {row[1]} ({row[1]/row[0]*100:.1f}%)")
print(f"有案由: {row[2]} ({row[2]/row[0]*100:.1f}%)")
print(f"有效法院名称: {row[3]} ({row[3]/row[0]*100:.1f}%)")
print(f"有判决日期: {row[4]} ({row[4]/row[0]*100:.1f}%)")
print(f"有争议点: {row[5]} ({row[5]/row[0]*100:.1f}%)")
print(f"有判决结果: {row[6]} ({row[6]/row[0]*100:.1f}%)")

cursor.close()
conn.close()













