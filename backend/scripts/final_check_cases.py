#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终检查：找出所有可能的案例数据
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
    """更宽松的判断，找出所有可能的案例"""
    if not title:
        return False
    
    # 排除明显的法规
    if any(kw in title for kw in ['法', '条例', '规定', '办法', '解释', '规则', '细则', '决定', '通知', '批复', '决议']):
        # 但如果是"XXX诉XXX案"这种格式，即使包含"法"也可能是案例
        if '诉' in title and '案' in title:
            # 检查是否是"XX法"结尾（法规）还是"XX案"结尾（案例）
            if title.endswith('案'):
                return True  # 是案例
            else:
                return False  # 是法规
        else:
            return False  # 是法规
    
    # 明确的案例格式
    if '诉' in title and '案' in title:
        return True
    
    # 明确的案例关键词
    if any(kw in title for kw in ['案例', '判例', '判决书', '裁判书']):
        return True
    
    # 如果条号为空，且标题或内容有案例特征
    if not article_number or article_number.strip() == '':
        if '诉' in title or '案' in title:
            return True
        if content and any(kw in content[:500] for kw in ['法院', '判决', '争议', '原告', '被告']):
            return True
    
    return False

conn = pymysql.connect(**db_config)
cursor = conn.cursor()

print("=" * 80)
print("最终检查：法条表中的案例数据")
print("=" * 80)

# 查询所有法条数据
cursor.execute("""
    SELECT id, title, article_number, content
    FROM legal_articles
    WHERE is_valid = 1
    ORDER BY id
""")

all_articles = cursor.fetchall()
print(f"\n总共 {len(all_articles)} 条法条数据\n")

# 识别可能的案例
possible_cases = []
for article in all_articles:
    article_id, title, article_number, content = article
    if is_likely_case(title, content, article_number):
        possible_cases.append((article_id, title))

print(f"发现 {len(possible_cases)} 条可能的案例数据\n")

if len(possible_cases) > 0:
    print("所有可能的案例:")
    for i, (article_id, title) in enumerate(possible_cases, 1):
        print(f"{i}. ID={article_id}: {title}")

# 检查案例表
print("\n" + "=" * 80)
print("案例表中的数据:")
print("=" * 80)
cursor.execute("SELECT id, title FROM legal_cases ORDER BY id")
cases = cursor.fetchall()
print(f"\n总共 {len(cases)} 条案例:")
for case in cases:
    print(f"  ID={case[0]}: {case[1]}")

conn.close()

