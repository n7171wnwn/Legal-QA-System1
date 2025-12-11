#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终修复案例数据 - 强制更新所有字段
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

def extract_court_name_final(content: str) -> str:
    """最终版本的法院名称提取"""
    if not content:
        return None
    
    # 精确匹配法院名称
    patterns = [
        r'([^，。\n]{2,30}(?:省|市|县|区|自治区)(?:高级|中级|基层)?人民法院)',
        r'([^，。\n]{2,30}(?:劳动人事争议|劳动争议)?仲裁委员会)',
    ]
    
    exclude = ['诉至', '不服', '《', '》', '规定', '作为', '系', '向', '至', '简称', '申请', 
               '请求', '主张', '认为', '案件', '此案', '审理', '开庭', '张某', '李某', '王某']
    
    all_courts = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        all_courts.extend(matches)
    
    # 验证
    for court in all_courts:
        court = court.strip()
        if 5 <= len(court) <= 50:
            if not any(kw in court for kw in exclude):
                if '人民法院' in court or '仲裁委员会' in court:
                    if not court.startswith(('向', '至', '在', '由', '被', '简称', '申请', '诉', '不服')):
                        if not re.match(r'^[张李王刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤]', court):
                            # 优先返回包含省市区信息的
                            if any(kw in court for kw in ['省', '市', '区', '县']):
                                return court
                            return court
    return None

def extract_law_type_final(title: str, content: str) -> str:
    """最终版本的法律领域检测"""
    text = (title + ' ' + (content or ''))[:2000]
    
    keywords = {
        '劳动法': ['劳动', '加班', '工资', '劳动合同', '劳动争议', '仲裁', '工伤', '解除合同', '用人单位', '劳动者'],
        '民法': ['合同', '买卖', '租赁', '侵权', '赔偿', '离婚', '继承', '财产', '房屋', '债务', '婚姻', '家庭'],
        '刑法': ['故意', '伤害', '诈骗', '盗窃', '犯罪', '刑事', '刑罚', '罪'],
        '行政法': ['行政', '处罚', '许可', '复议', '政府', '机关', '协议'],
        '知识产权法': ['专利', '商标', '著作权', '知识产权', '版权'],
        '消费者权益保护法': ['消费', '购物', '商品', '服务', '消费者', '经营者', '食品', '安全']
    }
    
    scores = {law_type: sum(1 for kw in kws if kw in text) for law_type, kws in keywords.items()}
    max_score = max(scores.values()) if scores else 0
    if max_score > 0:
        return max((lt for lt, s in scores.items() if s == max_score), key=lambda x: scores[x])
    return '民法'

def extract_case_type_final(title: str, content: str) -> str:
    """最终版本的案由检测"""
    text = (title + ' ' + (content or ''))[:500]
    
    keywords = {
        '劳动争议': ['劳动', '加班', '工资', '劳动合同', '解除', '仲裁'],
        '合同纠纷': ['合同', '买卖', '租赁', '服务', '协议'],
        '侵权纠纷': ['侵权', '损害', '赔偿', '人身'],
        '离婚纠纷': ['离婚', '婚姻', '撤销婚姻'],
        '继承纠纷': ['继承', '遗产', '遗嘱'],
        '人身损害赔偿': ['人身', '损害', '伤害', '赔偿'],
    }
    
    scores = {ct: sum(1 for kw in kws if kw in text) for ct, kws in keywords.items()}
    max_score = max(scores.values()) if scores else 0
    if max_score > 0:
        return max((ct for ct, s in scores.items() if s == max_score), key=lambda x: scores[x])
    
    if '纠纷' in title:
        return title.split('纠纷')[0] + '纠纷'
    if '争议' in title:
        return title.split('争议')[0] + '争议'
    return None

def extract_date_final(content: str) -> datetime:
    """最终版本的日期提取"""
    if not content:
        return None
    
    patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
    ]
    
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

def extract_dispute_final(content: str) -> str:
    """最终版本的争议点提取"""
    if not content:
        return None
    
    patterns = [
        r'争议焦点[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'核心争议[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'本案争议[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'争议焦点是[^。]*(.+?)(?:\n\n|。|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            dispute = re.sub(r'\s+', ' ', match.group(1).strip())
            if 20 <= len(dispute) <= 500:
                if not dispute.startswith(('《', '根据', '按照')):
                    return dispute[:500]
    return None

def extract_result_final(content: str) -> str:
    """最终版本的判决结果提取"""
    if not content:
        return None
    
    patterns = [
        r'裁判结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'判决结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'处理结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'(?:一审|二审)?(?:法院|人民法院)[判决|裁定][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'仲裁委员会[裁决|认定][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            result = re.sub(r'\s+', ' ', match.group(1).strip())
            if 20 <= len(result) <= 500:
                return result[:500]
    return None

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("开始全面修复案例数据...")
print("=" * 60)

cursor.execute("SELECT id, title, content, case_type, court_name, judge_date, dispute_point, judgment_result, law_type FROM legal_cases ORDER BY id")
cases = cursor.fetchall()

fixed = 0
for case in cases:
    case_id, title, content, case_type, court_name, judge_date, dispute_point, judgment_result, law_type = case
    
    updates = {}
    
    # 强制更新法律领域
    new_law_type = extract_law_type_final(title, content or '')
    if new_law_type != law_type:
        updates['law_type'] = new_law_type
    
    # 更新案由
    if not case_type:
        new_case_type = extract_case_type_final(title, content or '')
        if new_case_type:
            updates['case_type'] = new_case_type
    
    # 更新法院名称（如果为空或明显错误）
    if not court_name or len(court_name) > 100 or any(kw in (court_name or '') for kw in ['诉至', '不服', '《', '规定', '作为']):
        new_court = extract_court_name_final(content or '')
        if new_court:
            updates['court_name'] = new_court
    
    # 更新日期
    if not judge_date:
        new_date = extract_date_final(content or '')
        if new_date:
            updates['judge_date'] = new_date
    
    # 更新争议点
    if not dispute_point:
        new_dispute = extract_dispute_final(content or '')
        if new_dispute:
            updates['dispute_point'] = new_dispute
    
    # 更新判决结果
    if not judgment_result:
        new_result = extract_result_final(content or '')
        if new_result:
            updates['judgment_result'] = new_result
    
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
                 AND (court_name LIKE '%法院%' OR court_name LIKE '%仲裁委员会%')
            THEN 1 ELSE 0 END) as valid_court,
        SUM(CASE WHEN judge_date IS NOT NULL THEN 1 ELSE 0 END) as has_date,
        SUM(CASE WHEN dispute_point IS NOT NULL THEN 1 ELSE 0 END) as has_dispute,
        SUM(CASE WHEN judgment_result IS NOT NULL THEN 1 ELSE 0 END) as has_result
    FROM legal_cases
""")
row = cursor.fetchone()
print(f"\n最终统计:")
print(f"总案例数: {row[0]}")
print(f"有效法律领域: {row[1]} ({row[1]/row[0]*100:.1f}%)")
print(f"有案由: {row[2]} ({row[2]/row[0]*100:.1f}%)")
print(f"有效法院名称: {row[3]} ({row[3]/row[0]*100:.1f}%)")
print(f"有判决日期: {row[4]} ({row[4]/row[0]*100:.1f}%)")
print(f"有争议点: {row[5]} ({row[5]/row[0]*100:.1f}%)")
print(f"有判决结果: {row[6]} ({row[6]/row[0]*100:.1f}%)")

cursor.close()
conn.close()
print("\n✓ 完成！")













