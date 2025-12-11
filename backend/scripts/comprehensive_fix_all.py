#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面修复所有案例数据
"""

import pymysql
import sys
import re
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

def extract_court(content: str) -> str:
    """提取法院名称"""
    if not content:
        return None
    
    pattern = r'([^，。\n]{2,30}(?:省|市|县|区|自治区)(?:高级|中级|基层)?人民法院)'
    matches = re.findall(pattern, content)
    
    for match in matches:
        match = match.strip()
        if 5 <= len(match) <= 50:
            if not any(kw in match for kw in ['诉至', '不服', '《', '》', '规定', '作为', '向', '应予', '支持', '作出', '撤销', '号', '（', '）']):
                if match.endswith('人民法院'):
                    if not match.startswith(('向', '至', '在', '由', '被', '简称', '申请', '诉', '不服')):
                        if not re.search(r'[0-9（）()]', match):
                            if any(kw in match for kw in ['省', '市', '区', '县']):
                                return match
    return None

def extract_law_type(title: str, content: str) -> str:
    """提取法律领域（改进版，避免误分类）"""
    text = (title + ' ' + (content or ''))[:2000]
    
    # 使用加权关键词，更精确的关键词权重更高
    keywords = {
        '劳动法': {
            'high': ['劳动争议', '劳动合同', '用人单位', '劳动者', '加班费', '劳动仲裁'],
            'medium': ['劳动', '加班', '工资', '工伤', '解除合同']
        },
        '民法': {
            'high': ['合同纠纷', '离婚', '继承', '侵权', '物权', '人格权'],
            'medium': ['合同', '买卖', '租赁', '赔偿', '财产', '房屋', '债务', '婚姻', '家庭']
        },
        '刑法': {
            'high': ['故意伤害', '诈骗罪', '盗窃罪', '犯罪', '刑事'],
            'medium': ['故意', '伤害', '诈骗', '盗窃', '刑罚', '罪']
        },
        '行政法': {
            'high': ['行政协议', '行政决定', '行政', '政府', '机关'],
            'medium': ['处罚', '许可', '复议']
        },
        '知识产权法': {
            'high': ['专利', '商标', '著作权', '知识产权'],
            'medium': ['版权']
        },
        '消费者权益保护法': {
            'high': ['消费者权益', '食品安全', '经营者', '消费者'],
            'medium': ['消费', '购物', '商品', '食品']
        }
    }
    
    scores = {}
    for law_type, kw_groups in keywords.items():
        score = 0
        # 高权重关键词
        for kw in kw_groups.get('high', []):
            if kw in text:
                score += 3
        # 中权重关键词
        for kw in kw_groups.get('medium', []):
            if kw in text:
                score += 1
        scores[law_type] = score
    
    max_score = max(scores.values()) if scores else 0
    if max_score > 0:
        # 返回得分最高的，如果得分相同，按优先级返回
        best_law_type = max((lt for lt, s in scores.items() if s == max_score), key=lambda x: scores[x])
        return best_law_type
    
    return '民法'

def extract_case_type(title: str, content: str) -> str:
    """提取案由"""
    text = (title + ' ' + (content or ''))[:500]
    keywords = {
        '劳动争议': ['劳动', '加班', '工资', '劳动合同', '解除', '仲裁'],
        '合同纠纷': ['合同', '买卖', '租赁', '服务', '协议'],
        '侵权纠纷': ['侵权', '损害', '赔偿', '人身'],
        '离婚纠纷': ['离婚', '婚姻', '撤销婚姻'],
        '继承纠纷': ['继承', '遗产', '遗嘱'],
    }
    scores = {ct: sum(1 for kw in kws if kw in text) for ct, kws in keywords.items()}
    max_score = max(scores.values()) if scores else 0
    if max_score > 0:
        return max((ct for ct, s in scores.items() if s == max_score), key=lambda x: scores[x])
    if '纠纷' in title:
        return title.split('纠纷')[0] + '纠纷'
    return None

def extract_date(content: str) -> datetime:
    """提取日期"""
    if not content:
        return None
    patterns = [r'(\d{4})年(\d{1,2})月(\d{1,2})日', r'(\d{4})-(\d{1,2})-(\d{1,2})']
    dates = []
    for pattern in patterns:
        for match in re.findall(pattern, content):
            try:
                y, m, d = int(match[0]), int(match[1]), int(match[2])
                if 2000 <= y <= 2030 and 1 <= m <= 12 and 1 <= d <= 31:
                    dates.append(datetime(y, m, d))
            except:
                pass
    return max(dates) if dates else None

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("全面修复案例数据...")
print("=" * 60)

cursor.execute("SELECT id, title, content, case_type, court_name, judge_date, dispute_point, judgment_result, law_type FROM legal_cases ORDER BY id")
cases = cursor.fetchall()

fixed = 0
for case in cases:
    case_id, title, content, case_type, court_name, judge_date, dispute_point, judgment_result, law_type = case
    
    updates = {}
    
    # 1. 法律领域
    new_law_type = extract_law_type(title, content or '')
    if new_law_type != law_type:
        updates['law_type'] = new_law_type
    
    # 2. 案由
    if not case_type:
        new_case_type = extract_case_type(title, content or '')
        if new_case_type:
            updates['case_type'] = new_case_type
    
    # 3. 法院名称
    is_invalid_court = (not court_name or 
                       len(court_name) > 100 or
                       any(kw in (court_name or '') for kw in ['诉至', '不服', '《', '》', '规定', '作为', '简称', '向', '应予', '支持', '作出', '撤销']) or
                       (court_name and '人民法院' not in court_name and '仲裁委员会' not in court_name))
    
    if is_invalid_court:
        new_court = extract_court(content or '')
        if new_court:
            updates['court_name'] = new_court
    
    # 4. 日期
    if not judge_date:
        new_date = extract_date(content or '')
        if new_date:
            updates['judge_date'] = new_date
    
    if updates:
        set_clauses = [f"{k} = %s" for k in updates.keys()]
        values = list(updates.values()) + [case_id]
        cursor.execute(f"UPDATE legal_cases SET {', '.join(set_clauses)} WHERE id = %s", values)
        fixed += 1
        print(f"✓ ID {case_id}: {title[:40]}... 更新: {', '.join(updates.keys())}")

conn.commit()
print(f"\n✓ 修复了 {fixed} 条案例")

# 最终统计
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN law_type IS NOT NULL AND law_type != '案例' THEN 1 ELSE 0 END) as valid_law,
        SUM(CASE WHEN case_type IS NOT NULL THEN 1 ELSE 0 END) as has_case_type,
        SUM(CASE WHEN court_name IS NOT NULL AND LENGTH(court_name) <= 100 
                 AND court_name NOT LIKE '%诉至%' AND court_name NOT LIKE '%不服%'
                 AND court_name NOT LIKE '%《%' AND court_name NOT LIKE '%规定%'
                 AND (court_name LIKE '%法院%' OR court_name LIKE '%仲裁委员会%')
            THEN 1 ELSE 0 END) as valid_court,
        SUM(CASE WHEN judge_date IS NOT NULL THEN 1 ELSE 0 END) as has_date
    FROM legal_cases
""")
row = cursor.fetchone()
print(f"\n最终统计:")
print(f"总案例数: {row[0]}")
print(f"有效法律领域: {row[1]} ({row[1]/row[0]*100:.1f}%)")
print(f"有案由: {row[2]} ({row[2]/row[0]*100:.1f}%)")
print(f"有效法院名称: {row[3]} ({row[3]/row[0]*100:.1f}%)")
print(f"有判决日期: {row[4]} ({row[4]/row[0]*100:.1f}%)")

cursor.close()
conn.close()
print("\n✓ 完成！")

