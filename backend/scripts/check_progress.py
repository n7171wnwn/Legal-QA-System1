#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查导入进度"""

import pymysql
from pathlib import Path
import re
import sys

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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

try:
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
    for i, (title, count) in enumerate(results[:50], 1):  # 只显示前50个
        print(f"  {i:3d}. {title} ({count} 条)")
    
    if len(results) > 50:
        print(f"  ... 还有 {len(results) - 50} 部法律未显示")

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
        print("✓ 找到未成年人相关法律：")
        for title in minor_results:
            cursor.execute("SELECT COUNT(*) FROM legal_articles WHERE title = %s AND is_valid = true", (title[0],))
            count = cursor.fetchone()[0]
            print(f"  - {title[0]} ({count} 条)")
    else:
        print("⚠ 未找到未成年人保护法相关法律（可能正在导入中...）")

    # 统计总数
    cursor.execute("SELECT COUNT(*) FROM legal_articles WHERE is_valid = true")
    total_articles = cursor.fetchone()[0]
    print(f"\n总计：{len(results)} 部法律，{total_articles} 条法条")

    # 扫描文件夹，检查未导入的法律
    print("\n" + "="*70)
    print("检查文件夹中的法律文件...")
    laws_path = Path(r'E:\Laws\Laws')
    if laws_path.exists():
        md_files = list(laws_path.rglob('*.md'))
        print(f"文件夹中找到 {len(md_files)} 个markdown文件")
        
        # 提取法律名称
        file_laws = set()
        for md_file in md_files[:100]:  # 只检查前100个文件
            if any(skip in md_file.name for skip in ['README', 'readme', '_index', '.git']):
                continue
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # 只读前500字符
                    title_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
                    if title_match:
                        law_title = title_match.group(1).strip()
                        file_laws.add(law_title)
            except:
                pass
        
        # 对比
        db_laws = {row[0] for row in results}
        missing = file_laws - db_laws
        
        if missing:
            print(f"\n⚠ 发现 {len(missing)} 部可能未导入的法律（示例）：")
            for i, law in enumerate(list(missing)[:10], 1):
                print(f"  {i}. {law}")
            if len(missing) > 10:
                print(f"  ... 还有 {len(missing) - 10} 部")
        else:
            print("\n✓ 检查的文件都已导入")

    conn.close()
    print("\n检查完成！")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
