#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单直接地修复法院名称
"""

import pymysql
import re

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

print("直接修复法院名称...")
print("=" * 60)

cursor.execute("SELECT id, title, content, court_name FROM legal_cases ORDER BY id")
cases = cursor.fetchall()

fixed = 0
for case in cases:
    case_id, title, content, court_name = case
    
    # 简单直接的提取
    if not content:
        continue
    
    # 查找所有可能的法院名称
    pattern = r'([^，。\n]{2,30}(?:省|市|县|区|自治区)(?:高级|中级|基层)?人民法院)'
    matches = re.findall(pattern, content)
    
    # 过滤
    valid_courts = []
    for match in matches:
        match = match.strip()
        # 基本验证
        if 5 <= len(match) <= 50:
            # 排除明显错误的
            if not any(kw in match for kw in ['诉至', '不服', '《', '》', '规定', '作为', '向', '应予', '支持', '作出', '撤销', '号', '（', '）']):
                if match.endswith('人民法院'):
                    if not match.startswith(('向', '至', '在', '由', '被', '简称', '申请', '诉', '不服')):
                        if not re.search(r'[0-9（）()]', match):
                            if any(kw in match for kw in ['省', '市', '区', '县']):
                                valid_courts.append(match)
    
    if valid_courts:
        # 选择第一个有效的
        new_court = valid_courts[0]
        
        # 检查是否需要更新（如果当前为空或与新的不同，就更新）
        current_court = court_name if court_name else None
        if current_court != new_court:
            try:
                cursor.execute("UPDATE legal_cases SET court_name = %s WHERE id = %s", (new_court, case_id))
                print(f"✓ ID {case_id}: {title[:40]}...")
                if current_court:
                    print(f"  旧: {current_court[:50]}...")
                print(f"  新: {new_court}")
                fixed += 1
            except Exception as e:
                print(f"✗ ID {case_id}: 失败 - {e}")

conn.commit()
print(f"\n✓ 修复了 {fixed} 条案例")

# 统计
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN court_name IS NOT NULL 
                 AND LENGTH(court_name) <= 100
                 AND court_name NOT LIKE '%诉至%'
                 AND court_name NOT LIKE '%不服%'
                 AND court_name NOT LIKE '%《%'
                 AND (court_name LIKE '%法院%' OR court_name LIKE '%仲裁委员会%')
            THEN 1 ELSE 0 END) as valid_court
    FROM legal_cases
""")
row = cursor.fetchone()
print(f"有效法院名称: {row[1]}/{row[0]} ({row[1]/row[0]*100:.1f}%)")

cursor.close()
conn.close()

