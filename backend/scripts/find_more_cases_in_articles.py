#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找法条表中其他可能的案例数据
"""

import pymysql
import re

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

def is_likely_case(title, content, article_number):
    """判断是否为案例"""
    if not title:
        return False
    
    # 排除明显的法条格式
    if re.match(r'^第[一二三四五六七八九十百千万\d]+[条章节]', title):
        return False
    
    # 案例特征：问题形式（包含"是否"、"能否"、"如何"等）
    question_keywords = ['是否', '能否', '是否有权', '是否有效', '是否承担', '如何', '怎样', '什么']
    if any(kw in title for kw in question_keywords):
        # 排除法规名称
        if not any(kw in title for kw in ['法', '条例', '规定', '办法', '解释']):
            return True
    
    # 案例特征：内容中有"基本案情"
    if content and '基本案情' in content:
        return True
    
    # 案例特征：标题是"XXX诉XXX"格式
    if '诉' in title and '案' in title:
        if not any(kw in title for kw in ['诉讼法', '仲裁法', '调解法']):
            return True
    
    return False

conn = pymysql.connect(**db_config)
cursor = conn.cursor()

print("=" * 80)
print("查找法条表中其他可能的案例数据")
print("=" * 80)

# 查询所有法条数据
cursor.execute("""
    SELECT id, title, article_number, content
    FROM legal_articles
    WHERE is_valid = 1
    ORDER BY id
""")

all_articles = cursor.fetchall()
print(f"\n总共 {len(all_articles)} 条法条数据，开始识别案例...\n")

# 识别可能的案例
possible_cases = []
for article in all_articles:
    article_id, title, article_number, content = article
    if is_likely_case(title, content, article_number):
        possible_cases.append((article_id, title))

print(f"发现 {len(possible_cases)} 条可能的案例数据\n")

if len(possible_cases) > 0:
    print("前50条可能的案例:")
    for i, (article_id, title) in enumerate(possible_cases[:50], 1):
        print(f"{i}. ID={article_id}: {title}")

conn.close()

