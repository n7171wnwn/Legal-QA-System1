#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从案例内容中提取法院名称
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

def find_court_in_content(content: str) -> str:
    """在内容中查找法院名称"""
    if not content:
        return None
    
    # 查找所有可能的法院名称
    patterns = [
        r'([^，。\n]{2,25}(?:省|市|县|区|自治区)(?:高级|中级|基层)?人民法院)',
        r'([^，。\n]{2,25}(?:劳动人事争议|劳动争议)?仲裁委员会)',
    ]
    
    courts = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        courts.extend(matches)
    
    # 过滤和验证
    valid_courts = []
    exclude = ['诉至', '不服', '《', '》', '规定', '作为', '系', '向', '至', '简称', '申请', '请求']
    
    for court in courts:
        court = court.strip()
        if 5 <= len(court) <= 50:
            if not any(kw in court for kw in exclude):
                if '人民法院' in court or '仲裁委员会' in court:
                    if not court.startswith(('向', '至', '在', '由', '被', '简称')):
                        valid_courts.append(court)
    
    # 返回第一个有效的
    return valid_courts[0] if valid_courts else None

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# 查找法院名称为NULL的案例
cursor.execute("""
    SELECT id, title, content
    FROM legal_cases
    WHERE court_name IS NULL
""")

fixed = 0
for row in cursor.fetchall():
    case_id, title, content = row
    court = find_court_in_content(content or '')
    if court:
        try:
            cursor.execute("UPDATE legal_cases SET court_name = %s WHERE id = %s", (court, case_id))
            print(f"✓ ID {case_id}: {title[:50]}...")
            print(f"  提取法院: {court}")
            fixed += 1
        except Exception as e:
            print(f"✗ ID {case_id}: 更新失败 - {e}")

conn.commit()
print(f"\n✓ 为 {fixed} 条案例提取了法院名称")

cursor.close()
conn.close()













