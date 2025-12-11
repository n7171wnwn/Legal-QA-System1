#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试脚本：检查数据库中的法律"""

import pymysql
import sys

db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

try:
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT title FROM legal_articles WHERE is_valid = true ORDER BY title")
    results = cursor.fetchall()
    
    print(f"数据库中已有 {len(results)} 部法律：")
    for i, row in enumerate(results, 1):
        print(f"  {i}. {row[0]}")
    
    # 检查是否有未成年人保护法
    cursor.execute("SELECT DISTINCT title FROM legal_articles WHERE title LIKE '%未成年%' OR title LIKE '%未成年人%'")
    minor_results = cursor.fetchall()
    
    if minor_results:
        print(f"\n找到未成年人相关法律：")
        for row in minor_results:
            print(f"  - {row[0]}")
    else:
        print("\n未找到未成年人保护法相关法律")
    
    conn.close()
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
