#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查"劳动"相关的案例数据是否在法条表中
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
print("检查'劳动'相关的案例数据是否在法条表中")
print("=" * 80)

# 搜索包含"劳动者超时加班"等关键词的数据
keywords = [
    '劳动者超时加班发生工伤',
    '劳动者拒绝违法超时加班',
    '劳动者与用人单位订立放弃加班费',
    '劳动者在离职文件上签字确认加班费',
    '用人单位未按规章制度履行加班审批',
    '用人单位未与劳动者协商一致增加工作任务',
    '用人单位以规章制度形式否认劳动者加班',
    '用人单位与劳动者约定实行包薪制'
]

print("\n在法条表中查找这些数据...\n")

for keyword in keywords:
    cursor.execute("""
        SELECT id, title, article_number, content, law_type
        FROM legal_articles
        WHERE (title LIKE %s OR content LIKE %s) AND is_valid = 1
        LIMIT 5
    """, (f'%{keyword}%', f'%{keyword}%'))
    
    results = cursor.fetchall()
    if results:
        print(f"找到 '{keyword}' 相关的数据:")
        for result in results:
            article_id, title, article_number, content, law_type = result
            print(f"  ID={article_id}, 标题={title}")
            print(f"  条号={article_number}, 法律类型={law_type}")
            if content:
                print(f"  内容预览={content[:100]}...")
            print()
    else:
        print(f"未找到 '{keyword}' 相关的数据\n")

# 统计一下法条表中包含"劳动者"的数据数量
cursor.execute("""
    SELECT COUNT(*) 
    FROM legal_articles 
    WHERE (title LIKE '%劳动者%' OR content LIKE '%劳动者%') 
    AND is_valid = 1
""")
count = cursor.fetchone()[0]
print(f"\n法条表中包含'劳动者'的数据总数: {count}")

# 查看一些示例
cursor.execute("""
    SELECT id, title, article_number, law_type
    FROM legal_articles
    WHERE (title LIKE '%劳动者%' OR content LIKE '%劳动者%') 
    AND is_valid = 1
    LIMIT 10
""")
samples = cursor.fetchall()
print(f"\n前10条示例:")
for sample in samples:
    article_id, title, article_number, law_type = sample
    print(f"  ID={article_id}: {title[:50]}... (条号={article_number}, 类型={law_type})")

conn.close()

