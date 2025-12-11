#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速检查数据库中的法律"""

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

# 连接数据库
conn = pymysql.connect(**db_config)
cursor = conn.cursor()

# 查询所有法律名称
cursor.execute("SELECT DISTINCT title FROM legal_articles WHERE is_valid = true ORDER BY title")
existing_laws = {row[0] for row in cursor.fetchall()}

print(f"数据库中已有 {len(existing_laws)} 部法律\n")

# 检查是否有未成年人保护法
minor_laws = [law for law in existing_laws if '未成年' in law or '未成年人' in law]
if minor_laws:
    print("找到未成年人相关法律：")
    for law in minor_laws:
        cursor.execute("SELECT COUNT(*) FROM legal_articles WHERE title = %s AND is_valid = true", (law,))
        count = cursor.fetchone()[0]
        print(f"  - {law} ({count} 条)")
else:
    print("未找到未成年人保护法相关法律\n")

# 扫描文件夹
laws_path = Path(r'E:\Laws\Laws')
if laws_path.exists():
    md_files = list(laws_path.rglob('*.md'))
    print(f"\n文件夹中找到 {len(md_files)} 个markdown文件")
    
    # 检查未成年人保护法文件
    minor_files = [f for f in md_files if '未成年' in f.name]
    if minor_files:
        print("\n找到未成年人保护法相关文件：")
        for f in minor_files[:5]:
            print(f"  - {f.name} ({f.parent.name})")
            # 尝试提取法律名称
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    content = file.read()
                    title_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
                    if title_match:
                        law_title = title_match.group(1).strip()
                        if law_title not in existing_laws:
                            print(f"    → 未导入: {law_title}")
                        else:
                            print(f"    → 已导入: {law_title}")
            except:
                pass

conn.close()
print("\n检查完成！")
