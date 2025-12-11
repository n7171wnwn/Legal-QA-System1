#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复明显错误的法院名称
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

def extract_court_name_proper(content: str) -> str:
    """正确提取法院名称"""
    if not content:
        return None
    
    # 精确匹配法院名称
    patterns = [
        r'([^，。\n]{2,20}(?:省|市|县|区|自治区)(?:高级|中级|基层)?人民法院)',
        r'([^，。\n]{2,20}(?:劳动人事争议|劳动争议)?仲裁委员会)',
    ]
    
    exclude = ['诉至', '不服', '《', '》', '规定', '作为', '系', '向', '至', '简称', '申请']
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            match = match.strip()
            if 5 <= len(match) <= 50:
                if not any(kw in match for kw in exclude):
                    if '人民法院' in match or '仲裁委员会' in match:
                        if not match.startswith(('向', '至', '在', '由', '被')):
                            return match
    return None

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# 查找所有有问题的法院名称
cursor.execute("""
    SELECT id, title, content, court_name
    FROM legal_cases
    WHERE court_name IS NOT NULL
""")

fixed = 0
for row in cursor.fetchall():
    case_id, title, content, court_name = row
    
    # 检查是否是错误的法院名称
    bad_keywords = ['诉至', '不服', '《', '》', '规定', '作为', '系', '向', '简称', '申请', '请求', '主张']
    is_bad = any(kw in court_name for kw in bad_keywords)
    too_long = len(court_name) > 100
    no_keyword = '人民法院' not in court_name and '仲裁委员会' not in court_name
    
    if is_bad or too_long or no_keyword:
        # 尝试重新提取
        new_court = extract_court_name_proper(content or '')
        if new_court:
            try:
                cursor.execute("UPDATE legal_cases SET court_name = %s WHERE id = %s", (new_court, case_id))
                print(f"✓ ID {case_id}: {title[:40]}...")
                print(f"  旧: {court_name[:60]}...")
                print(f"  新: {new_court}")
                fixed += 1
            except Exception as e:
                print(f"✗ ID {case_id}: 更新失败 - {e}")
        else:
            # 如果无法提取，设置为NULL
            try:
                cursor.execute("UPDATE legal_cases SET court_name = NULL WHERE id = %s", (case_id,))
                print(f"⚠ ID {case_id}: 无法提取，设置为NULL")
                fixed += 1
            except Exception as e:
                print(f"✗ ID {case_id}: 更新失败 - {e}")

conn.commit()
print(f"\n✓ 修复了 {fixed} 条案例的法院名称")

cursor.close()
conn.close()













