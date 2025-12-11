# -*- coding: utf-8 -*-
import pymysql
import sys

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='hjj060618',
        database='legal_qa',
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    # 查询法律总数
    cursor.execute('SELECT COUNT(DISTINCT title) FROM legal_articles WHERE is_valid = true')
    law_count = cursor.fetchone()[0]

    # 查询法条总数
    cursor.execute('SELECT COUNT(*) FROM legal_articles WHERE is_valid = true')
    article_count = cursor.fetchone()[0]

    print('=' * 70)
    print('数据库导入状态')
    print('=' * 70)
    print(f'\n法律总数: {law_count} 部')
    print(f'法条总数: {article_count} 条')

    # 检查未成年人相关法律
    cursor.execute("""
        SELECT DISTINCT title 
        FROM legal_articles 
        WHERE (title LIKE '%未成年%' OR title LIKE '%未成年人%') 
        AND is_valid = true
    """)
    minor_laws = cursor.fetchall()

    print('\n' + '=' * 70)
    if minor_laws:
        print('✓ 未成年人相关法律:')
        for law in minor_laws:
            cursor.execute('SELECT COUNT(*) FROM legal_articles WHERE title = %s AND is_valid = true', (law[0],))
            count = cursor.fetchone()[0]
            print(f'  - {law[0]} ({count} 条)')
    else:
        print('⚠ 未找到未成年人保护法相关法律')

    # 显示最近导入的一些法律（按更新时间排序）
    print('\n' + '=' * 70)
    print('最近更新的法律（前20部）:')
    cursor.execute("""
        SELECT title, COUNT(*) as count, MAX(update_time) as last_update
        FROM legal_articles 
        WHERE is_valid = true 
        GROUP BY title 
        ORDER BY last_update DESC 
        LIMIT 20
    """)
    recent_laws = cursor.fetchall()
    for i, (title, count, last_update) in enumerate(recent_laws, 1):
        print(f'  {i:2d}. {title} ({count} 条) - {last_update}')

    conn.close()
    print('\n' + '=' * 70)
    print('检查完成！')
    
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
