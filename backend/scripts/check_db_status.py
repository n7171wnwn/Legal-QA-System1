# -*- coding: utf-8 -*-
import pymysql
import json
from datetime import datetime

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

output_file = 'import_status.json'

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
        minor_laws.append({'title': row[0], 'count': count})

    # 查询最近更新的法律
    cursor.execute("""
        SELECT title, COUNT(*) as count, MAX(update_time) as last_update
        FROM legal_articles 
        WHERE is_valid = true 
        GROUP BY title 
        ORDER BY last_update DESC 
        LIMIT 20
    """)
    recent_laws = []
    for row in cursor.fetchall():
        recent_laws.append({
            'title': row[0],
            'count': row[1],
            'last_update': str(row[2]) if row[2] else None
        })

    # 保存到JSON文件
    status = {
        'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'law_count': law_count,
        'article_count': article_count,
        'minor_laws': minor_laws,
        'recent_laws': recent_laws
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    # 同时输出到控制台
    print('=' * 70)
    print('数据库导入状态')
    print('=' * 70)
    print(f'\n检查时间: {status["check_time"]}')
    print(f'法律总数: {law_count} 部')
    print(f'法条总数: {article_count} 条')
    
    print('\n' + '=' * 70)
    if minor_laws:
        print('✓ 未成年人相关法律:')
        for law in minor_laws:
            print(f'  - {law["title"]} ({law["count"]} 条)')
    else:
        print('⚠ 未找到未成年人保护法相关法律')

    print('\n' + '=' * 70)
    print('最近更新的法律（前10部）:')
    for i, law in enumerate(recent_laws[:10], 1):
        print(f'  {i:2d}. {law["title"]} ({law["count"]} 条) - {law["last_update"]}')

    print(f'\n状态已保存到: {output_file}')
    conn.close()

except Exception as e:
    error_info = {'error': str(e), 'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(error_info, f, ensure_ascii=False, indent=2)
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
