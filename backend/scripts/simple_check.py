# -*- coding: utf-8 -*-
import pymysql

conn = pymysql.connect(host='localhost', user='root', password='hjj060618', database='legal_qa', charset='utf8mb4')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(DISTINCT title) FROM legal_articles WHERE is_valid = true')
law_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM legal_articles WHERE is_valid = true')
article_count = cursor.fetchone()[0]

cursor.execute("SELECT DISTINCT title FROM legal_articles WHERE title LIKE '%未成年%' AND is_valid = true")
minor_laws = cursor.fetchall()

print(f'数据库状态:')
print(f'  法律数量: {law_count} 部')
print(f'  法条总数: {article_count} 条')
print(f'  未成年人相关法律: {len(minor_laws)} 部')
for law in minor_laws:
    print(f'    - {law[0]}')

conn.close()
