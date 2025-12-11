#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新法院名称
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

# 测试ID 12
cursor.execute("SELECT id, title, content, court_name FROM legal_cases WHERE id = 12")
row = cursor.fetchone()
case_id, title, content, court_name = row

print(f"ID: {case_id}")
print(f"标题: {title}")
print(f"当前法院: {repr(court_name)}")
print(f"是否为None: {court_name is None}")

# 提取法院名称
pattern = r'([^，。\n]{2,30}(?:省|市|县|区|自治区)(?:高级|中级|基层)?人民法院)'
matches = re.findall(pattern, content or '')

print(f"\n匹配结果: {matches}")

if matches:
    new_court = matches[0].strip()
    print(f"提取到的法院: {new_court}")
    print(f"长度: {len(new_court)}")
    
    # 验证
    if 5 <= len(new_court) <= 50:
        if not any(kw in new_court for kw in ['诉至', '不服', '《', '》', '规定', '作为', '向', '应予', '支持', '作出', '撤销', '号', '（', '）']):
            if new_court.endswith('人民法院'):
                if not new_court.startswith(('向', '至', '在', '由', '被', '简称', '申请', '诉', '不服')):
                    if not re.search(r'[0-9（）()]', new_court):
                        if any(kw in new_court for kw in ['省', '市', '区', '县']):
                            print(f"\n✓ 验证通过，准备更新...")
                            try:
                                cursor.execute("UPDATE legal_cases SET court_name = %s WHERE id = %s", (new_court, case_id))
                                conn.commit()
                                print(f"✓ 更新成功！")
                                
                                # 验证更新
                                cursor.execute("SELECT court_name FROM legal_cases WHERE id = %s", (case_id,))
                                updated = cursor.fetchone()[0]
                                print(f"更新后的值: {repr(updated)}")
                            except Exception as e:
                                print(f"✗ 更新失败: {e}")
                                conn.rollback()

cursor.close()
conn.close()













