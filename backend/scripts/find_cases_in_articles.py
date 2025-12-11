#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查法条表中是否有案例数据
"""

import pymysql
import re

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

def is_case_in_articles(title, content, article_number):
    """判断法条表中的数据是否为案例（更精确的判断）"""
    if not title:
        return False
    
    # 首先排除明显的法规（优先级最高）
    regulation_keywords = [
        '法', '条例', '规定', '办法', '解释', '规则', '细则', '决定', '通知', '批复', '决议',
        '中华人民共和国', '最高人民法院关于', '最高人民检察院关于', '公安机关办理',
        '程序规定', '组织法', '诉讼法', '仲裁法', '调解法', '修正案',
        '人民代表大会常务委员会', '人民代表大会', '经济特区', '直辖市',
        '档案法', '律师法', '公证法', '人民警察法', '外国国家豁免法',
        '攻略', '指南', '手册'  # 指导性文档
    ]
    
    # 如果标题是完整的法规名称格式，排除
    if any(title.startswith(kw) or title.endswith(kw) or (kw in title and len(kw) > 3) for kw in regulation_keywords):
        # 但如果是"XXX诉XXX案"这种格式，即使包含"法"也可能是案例
        if '诉' in title and '案' in title:
            # 检查是否是"XX法"结尾（法规）还是"XX案"结尾（案例）
            if not title.endswith('法') and not title.endswith('条例') and not title.endswith('规定'):
                pass  # 可能是案例，继续判断
            else:
                return False  # 是法规
        else:
            return False  # 是法规
    
    # 明确的案例格式：XXX诉XXX案、XXX纠纷案
    if '诉' in title and '案' in title:
        # 排除法规名称（如"XX诉讼法"）
        if not any(kw in title for kw in ['诉讼法', '仲裁法', '调解法', '组织法', '修正案']):
            return True
    
    # 明确的案例关键词（但排除法规）
    explicit_case_keywords = ['案例', '判例', '判决书', '裁判书']
    if any(kw in title for kw in explicit_case_keywords):
        return True
    
    # 如果内容中有明确的案例特征，且标题不是法规格式
    if content:
        case_feature_keywords = [
            '审理法院', '判决日期', '案由', '争议点', '判决结果',
            '原告', '被告', '上诉人', '被上诉人', '当事人',
            '一审', '二审', '再审', '终审'
        ]
        case_feature_count = 0
        for keyword in case_feature_keywords:
            if keyword in content[:2000]:
                case_feature_count += 1
        
        # 如果匹配到4个以上案例特征，且没有条号结构，很可能是案例
        if case_feature_count >= 4:
            # 检查是否有条号结构（法规通常有条号）
            if not re.search(r'第[一二三四五六七八九十百千万\d]+[条章节]', content[:1000]):
                # 再次确认标题不是法规格式
                if not any(kw in title for kw in ['法', '条例', '规定', '办法', '解释']):
                    return True
    
    # 如果条号为空，且标题是案例描述性的（不是法规名称）
    if not article_number or article_number.strip() == '':
        # 标题包含"诉"和"案"，且不是法规格式
        if '诉' in title and '案' in title:
            if not any(kw in title for kw in ['诉讼法', '仲裁法', '调解法', '组织法']):
                return True
        # 或者标题是案例描述性的（如"婚前隐瞒重大疾病 配偶可申请撤销婚姻"）
        elif any(kw in title for kw in ['纠纷', '争议', '赔偿', '解除', '撤销']):
            # 且内容中有案例特征
            if content and any(kw in content[:500] for kw in ['法院', '判决', '原告', '被告']):
                return True
    
    return False

conn = pymysql.connect(**db_config)
cursor = conn.cursor()

print("=" * 80)
print("检查法条表中是否有案例数据")
print("=" * 80)

# 查询所有法条数据
cursor.execute("""
    SELECT id, title, article_number, content, law_type, create_time
    FROM legal_articles
    WHERE is_valid = 1
    ORDER BY id
""")

all_articles = cursor.fetchall()
print(f"\n总共 {len(all_articles)} 条法条数据，开始识别案例...\n")

# 识别案例数据
cases_in_articles = []
for article in all_articles:
    article_id, title, article_number, content, law_type, create_time = article
    if is_case_in_articles(title, content, article_number):
        cases_in_articles.append(article)
        print(f"发现案例: ID={article_id}, 标题={title}")

print(f"\n总共发现 {len(cases_in_articles)} 条案例数据在法条表中")

if len(cases_in_articles) > 0:
    print("\n前50条案例数据:")
    for i, case in enumerate(cases_in_articles[:50], 1):
        article_id, title, article_number, content, law_type, create_time = case
        print(f"{i}. ID={article_id}: {title}")

conn.close()

