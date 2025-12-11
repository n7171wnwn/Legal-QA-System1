#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查导入状态和结果"""

import pymysql
from pathlib import Path
import re

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

print("="*70)
print("检查数据库导入状态")
print("="*70)

# 连接数据库
conn = pymysql.connect(**db_config)
cursor = conn.cursor()

# 查询所有法律名称和数量
cursor.execute("""
    SELECT title, COUNT(*) as count 
    FROM legal_articles 
    WHERE is_valid = true 
    GROUP BY title 
    ORDER BY title
""")
results = cursor.fetchall()

print(f"\n数据库中已有 {len(results)} 部法律：\n")
for i, (title, count) in enumerate(results, 1):
    print(f"  {i:3d}. {title} ({count} 条)")

# 检查是否有未成年人保护法
cursor.execute("""
    SELECT DISTINCT title 
    FROM legal_articles 
    WHERE (title LIKE '%未成年%' OR title LIKE '%未成年人%') 
    AND is_valid = true
""")
minor_results = cursor.fetchall()

print("\n" + "="*70)
if minor_results:
    print("找到未成年人相关法律：")
    for title in minor_results:
        cursor.execute("SELECT COUNT(*) FROM legal_articles WHERE title = %s AND is_valid = true", (title[0],))
        count = cursor.fetchone()[0]
        print(f"  ✓ {title[0]} ({count} 条)")
else:
    print("⚠ 未找到未成年人保护法相关法律")

# 统计总数
cursor.execute("SELECT COUNT(*) FROM legal_articles WHERE is_valid = true")
total_articles = cursor.fetchone()[0]
print(f"\n总计：{len(results)} 部法律，{total_articles} 条法条")

conn.close()
print("\n检查完成！")
