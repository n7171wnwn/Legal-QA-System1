#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查案例表中的数据
"""

import pymysql

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

conn = pymysql.connect(**db_config)
cursor = conn.cursor()

print("=" * 80)
print("检查案例表中的所有数据")
print("=" * 80)

cursor.execute("""
    SELECT id, title, case_type, court_name, judge_date, law_type
    FROM legal_cases
    ORDER BY id
""")

cases = cursor.fetchall()
print(f"\n总共 {len(cases)} 条案例数据:\n")

for case in cases:
    case_id, title, case_type, court_name, judge_date, law_type = case
    print(f"ID: {case_id}")
    print(f"  标题: {title}")
    print(f"  案由: {case_type}")
    print(f"  法院: {court_name}")
    print(f"  判决日期: {judge_date}")
    print(f"  法律领域: {law_type}")
    print()

conn.close()

