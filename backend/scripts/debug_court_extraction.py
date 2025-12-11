#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试法院名称提取
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

def debug_extract_court(text: str, case_id: int, title: str):
    """调试法院名称提取"""
    if not text:
        print(f"ID {case_id}: 无内容")
        return None
    
    patterns = [
        r'([^，。\n]{2,30}(?:省|市|县|区|自治区|特别行政区)(?:高级|中级|基层)?人民法院)',
        r'([^，。\n]{2,30}(?:劳动人事争议|劳动争议)?仲裁委员会)',
    ]
    
    exclude = ['诉至', '不服', '《', '》', '规定', '作为', '系', '向', '至', '简称', 
               '申请', '请求', '主张', '认为', '案件', '此案', '审理', '开庭', '应予', '支持']
    
    print(f"\n{'='*80}")
    print(f"调试 ID {case_id}: {title[:50]}...")
    print(f"{'='*80}")
    
    all_matches = []
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text)
        print(f"\n模式 {i+1}: {pattern}")
        print(f"  匹配到: {matches[:5]}")  # 只显示前5个
        all_matches.extend(matches)
    
    print(f"\n所有匹配: {all_matches[:10]}")
    
    valid_courts = []
    for court in all_matches:
        court = court.strip()
        print(f"\n检查: '{court}' (长度: {len(court)})")
        
        if not (5 <= len(court) <= 50):
            print(f"  ✗ 长度不符合要求")
            continue
        
        has_exclude = any(kw in court for kw in exclude)
        if has_exclude:
            print(f"  ✗ 包含排除词")
            continue
        
        has_keyword = '人民法院' in court or '仲裁委员会' in court
        if not has_keyword:
            print(f"  ✗ 不包含关键词")
            continue
        
        starts_with_bad = court.startswith(('向', '至', '在', '由', '被', '简称', '申请', '诉', '不服', '张某', '李某', '王某', '人民法院应予'))
        if starts_with_bad:
            print(f"  ✗ 以排除词开头")
            continue
        
        starts_with_name = re.match(r'^[张李王刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤]', court)
        if starts_with_name:
            print(f"  ✗ 以姓氏开头")
            continue
        
        has_yingshu = '应予' in court or '支持' in court
        if has_yingshu:
            print(f"  ✗ 包含'应予'或'支持'")
            continue
        
        print(f"  ✓ 通过验证")
        valid_courts.append(court)
    
    print(f"\n有效法院: {valid_courts}")
    
    # 优先返回包含省市区信息的
    for court in valid_courts:
        if any(kw in court for kw in ['省', '市', '区', '县']):
            if not any(kw in court for kw in ['于', '在', '向', '申请', '请求', '诉', '不服', '应予', '支持']):
                if re.match(r'^[^，。\n]{2,25}(?:省|市|县|区)(?:高级|中级|基层)?人民法院$', court):
                    print(f"\n✓ 最终选择: {court}")
                    return court
    
    if valid_courts:
        print(f"\n⚠ 返回第一个有效: {valid_courts[0]}")
        return valid_courts[0]
    
    print(f"\n✗ 未找到有效法院")
    return None

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# 测试几个案例
cursor.execute("SELECT id, title, content FROM legal_cases WHERE id IN (12, 1, 25) ORDER BY id")

for row in cursor.fetchall():
    case_id, title, content = row
    result = debug_extract_court(content or '', case_id, title)

cursor.close()
conn.close()













