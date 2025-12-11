#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取导入状态并保存到文件"""

import pymysql
from datetime import datetime

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

output_file = 'import_status_report.txt'

try:
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    # 查询法律总数
    cursor.execute('SELECT COUNT(DISTINCT title) FROM legal_articles WHERE is_valid = true')
    law_count = cursor.fetchone()[0]

    # 查询法条总数
    cursor.execute('SELECT COUNT(*) FROM legal_articles WHERE is_valid = true')
    article_count = cursor.fetchone()[0]

    # 查询未成年人相关法律
    cursor.execute("""
        SELECT DISTINCT title 
        FROM legal_articles 
        WHERE (title LIKE '%未成年%' OR title LIKE '%未成年人%') 
        AND is_valid = true
    """)
    minor_laws = []
    for row in cursor.fetchall():
        cursor.execute('SELECT COUNT(*) FROM legal_articles WHERE title = %s AND is_valid = true', (row[0],))
        count = cursor.fetchone()[0]
        minor_laws.append((row[0], count))

    # 查询最近更新的法律
    cursor.execute("""
        SELECT title, COUNT(*) as count, MAX(update_time) as last_update
        FROM legal_articles 
        WHERE is_valid = true 
        GROUP BY title 
        ORDER BY last_update DESC 
        LIMIT 15
    """)
    recent_laws = cursor.fetchall()

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('=' * 70 + '\n')
        f.write('数据库导入状态报告\n')
        f.write('=' * 70 + '\n')
        f.write(f'\n检查时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'法律总数: {law_count} 部\n')
        f.write(f'法条总数: {article_count} 条\n')

        f.write('\n' + '=' * 70 + '\n')
        if minor_laws:
            f.write('✓ 未成年人相关法律:\n')
            for title, count in minor_laws:
                f.write(f'  - {title} ({count} 条)\n')
        else:
            f.write('⚠ 未找到未成年人保护法相关法律\n')

        f.write('\n' + '=' * 70 + '\n')
        f.write('最近更新的法律（前15部）:\n')
        for i, (title, count, last_update) in enumerate(recent_laws, 1):
            f.write(f'  {i:2d}. {title} ({count} 条) - {last_update}\n')

        f.write('\n' + '=' * 70 + '\n')
        f.write('报告完成！\n')

    print(f'状态报告已保存到: {output_file}')
    print(f'法律总数: {law_count} 部')
    print(f'法条总数: {article_count} 条')
    print(f'未成年人相关法律: {len(minor_laws)} 部')
    
    conn.close()

except Exception as e:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'错误: {e}\n')
        import traceback
        f.write(traceback.format_exc())
    print(f'错误: {e}')
