#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查案例数据格式
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

# 检查数据完整性
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN law_type IS NOT NULL AND law_type != '案例' THEN 1 ELSE 0 END) as has_law_type,
        SUM(CASE WHEN case_type IS NOT NULL THEN 1 ELSE 0 END) as has_case_type,
        SUM(CASE WHEN court_name IS NOT NULL THEN 1 ELSE 0 END) as has_court,
        SUM(CASE WHEN judge_date IS NOT NULL THEN 1 ELSE 0 END) as has_date,
        SUM(CASE WHEN dispute_point IS NOT NULL THEN 1 ELSE 0 END) as has_dispute,
        SUM(CASE WHEN judgment_result IS NOT NULL THEN 1 ELSE 0 END) as has_result
    FROM legal_cases
""")

row = cursor.fetchone()
print("案例数据完整性统计:")
print(f"总案例数: {row[0]}")
print(f"有法律领域: {row[1]} ({row[1]/row[0]*100:.1f}%)")
print(f"有案由: {row[2]} ({row[2]/row[0]*100:.1f}%)")
print(f"有审理法院: {row[3]} ({row[3]/row[0]*100:.1f}%)")
print(f"有判决日期: {row[4]} ({row[4]/row[0]*100:.1f}%)")
print(f"有争议点: {row[5]} ({row[5]/row[0]*100:.1f}%)")
print(f"有判决结果: {row[6]} ({row[6]/row[0]*100:.1f}%)")

# 显示几个示例
print("\n示例案例（前3条）:")
cursor.execute("""
    SELECT id, title, case_type, law_type, court_name, 
           CASE WHEN judge_date IS NOT NULL THEN '有' ELSE '无' END as has_date,
           CASE WHEN dispute_point IS NOT NULL THEN '有' ELSE '无' END as has_dispute,
           CASE WHEN judgment_result IS NOT NULL THEN '有' ELSE '无' END as has_result
    FROM legal_cases
    ORDER BY id
    LIMIT 3
""")

for row in cursor.fetchall():
    print(f"\nID: {row[0]}")
    print(f"  标题: {row[1][:50]}...")
    print(f"  案由: {row[2] or '未设置'}")
    print(f"  法律领域: {row[3]}")
    print(f"  审理法院: {row[4] or '未设置'}")
    print(f"  判决日期: {row[5]}")
    print(f"  争议点: {row[6]}")
    print(f"  判决结果: {row[7]}")

cursor.close()
conn.close()













