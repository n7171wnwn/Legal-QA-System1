#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面修复案例数据，改进提取逻辑
"""

import pymysql
import sys
import re
from datetime import datetime
from typing import Optional

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

def extract_court_name_improved(content: str) -> Optional[str]:
    """改进的法院名称提取"""
    if not content:
        return None
    
    # 更精确的法院名称模式
    # 优先匹配：XX市XX区人民法院 或 XX省XX市人民法院
    precise_patterns = [
        # 完整的省市区+人民法院格式（最优先）
        r'([^，。\n]{2,30}(?:省|市|县|区|自治区|特别行政区)(?:高级|中级|基层)?人民法院)',
        # 完整的仲裁委员会格式
        r'([^，。\n]{2,30}(?:劳动人事争议|劳动争议)?仲裁委员会)',
        # 简化的格式（但必须包含地区名）
        r'([^，。\n]{2,20}(?:市|县|区)(?:高级|中级|基层)?人民法院)',
    ]
    
    exclude_keywords = ['诉至', '不服', '《', '》', '规定', '法条', '法律', '第', '条', 
                       '作为', '系', '于', '年', '月', '日', '申请', '请求', '主张',
                       '认为', '判决', '裁定', '仲裁', '争议', '纠纷', '案件', '此案',
                       '向', '至', '在', '由', '被', '简称', '审理', '开庭', '不服']
    
    all_courts = []
    for pattern in precise_patterns:
        matches = re.findall(pattern, content)
        all_courts.extend(matches)
    
    # 验证和过滤
    valid_courts = []
    for court in all_courts:
        court = court.strip()
        # 基本验证
        if 5 <= len(court) <= 50:
            # 排除包含排除词汇的
            if not any(kw in court for kw in exclude_keywords):
                # 必须包含"人民法院"或"仲裁委员会"
                if '人民法院' in court or '仲裁委员会' in court:
                    # 排除以特定词开头的
                    if not court.startswith(('向', '至', '在', '由', '被', '简称', '申请', '诉', '不服', '张某', '李某', '王某')):
                        # 排除包含"诉至"、"不服"等词的句子片段
                        if '诉至' not in court and '不服' not in court:
                            # 排除包含人名开头的（如"张某向..."）
                            if not re.match(r'^[张李王刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤]', court):
                                valid_courts.append(court)
    
    # 如果找到多个，优先选择最完整的（包含省市区信息的）
    if valid_courts:
        # 优先选择包含"省"、"市"、"区"的完整格式
        for court in valid_courts:
            if any(keyword in court for keyword in ['省', '市', '区', '县']):
                # 进一步验证：应该是一个完整的法院名称，不应该包含其他句子成分
                if not any(kw in court for kw in ['于', '在', '向', '申请', '请求']):
                    return court
        # 如果没有找到包含省市区信息的，返回第一个有效的
        return valid_courts[0]
    
    return None

def extract_law_type_improved(title: str, content: str, current_law_type: str) -> str:
    """改进的法律领域检测"""
    if current_law_type and current_law_type not in ['案例', '其他']:
        return current_law_type
    
    text = (title + ' ' + (content or ''))[:2000]
    
    # 更精确的关键词匹配
    law_type_keywords = {
        '劳动法': ['劳动', '加班', '工资', '劳动合同', '劳动争议', '仲裁', '工伤', '解除合同', '赔偿', '用人单位', '劳动者', '工作'],
        '民法': ['合同', '买卖', '租赁', '侵权', '赔偿', '离婚', '继承', '财产', '房屋', '债务', '婚姻', '家庭', '物权', '人格权'],
        '刑法': ['故意', '伤害', '诈骗', '盗窃', '抢劫', '杀人', '犯罪', '刑事', '刑罚', '罪', '判刑'],
        '行政法': ['行政', '处罚', '许可', '复议', '诉讼', '政府', '机关', '协议'],
        '知识产权法': ['专利', '商标', '著作权', '知识产权', '侵权', '版权'],
        '消费者权益保护法': ['消费', '购物', '商品', '服务', '消费者', '经营者', '食品', '安全']
    }
    
    # 计算每个法律领域的匹配分数
    scores = {}
    for law_type, keywords in law_type_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        scores[law_type] = score
    
    # 返回得分最高的
    if scores:
        max_score = max(scores.values())
        if max_score > 0:
            for law_type, score in scores.items():
                if score == max_score:
                    return law_type
    
    return '民法'  # 默认

def extract_case_type_improved(title: str, content: str) -> Optional[str]:
    """改进的案由检测"""
    text = (title + ' ' + (content or ''))[:500]
    
    # 更精确的案由关键词
    case_type_keywords = {
        '劳动争议': ['劳动', '加班', '工资', '劳动合同', '解除', '仲裁'],
        '合同纠纷': ['合同', '买卖', '租赁', '服务', '协议'],
        '侵权纠纷': ['侵权', '损害', '赔偿', '人身', '财产'],
        '离婚纠纷': ['离婚', '婚姻', '撤销婚姻'],
        '继承纠纷': ['继承', '遗产', '遗嘱'],
        '人身损害赔偿': ['人身', '损害', '伤害', '赔偿', '事故'],
        '财产纠纷': ['财产', '债务', '房屋', '分割'],
        '故意伤害罪': ['故意', '伤害'],
        '诈骗罪': ['诈骗'],
        '盗窃罪': ['盗窃']
    }
    
    # 计算匹配分数
    scores = {}
    for case_type, keywords in case_type_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        scores[case_type] = score
    
    # 返回得分最高的
    if scores:
        max_score = max(scores.values())
        if max_score > 0:
            for case_type, score in scores.items():
                if score == max_score:
                    return case_type
    
    # 如果标题包含"纠纷"、"争议"等，提取案由
    if '纠纷' in title:
        parts = title.split('纠纷')
        if len(parts) > 0 and len(parts[0]) > 0:
            return parts[0] + '纠纷'
    if '争议' in title:
        parts = title.split('争议')
        if len(parts) > 0 and len(parts[0]) > 0:
            return parts[0] + '争议'
    
    return None

def extract_judge_date_improved(content: str) -> Optional[datetime]:
    """改进的日期提取"""
    if not content:
        return None
    
    # 更精确的日期模式
    date_patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})',
    ]
    
    all_dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            try:
                year, month, day = int(match[0]), int(match[1]), int(match[2])
                # 验证日期合理性
                if 2000 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                    all_dates.append(datetime(year, month, day))
            except:
                continue
    
    # 返回最晚的日期（通常是判决日期）
    if all_dates:
        return max(all_dates)
    
    return None

def extract_dispute_point_improved(content: str) -> Optional[str]:
    """改进的争议点提取"""
    if not content:
        return None
    
    # 查找争议点章节
    patterns = [
        r'争议焦点[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'核心争议[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'本案争议[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'主要争议[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        # 从"案例分析"章节中提取
        r'案例分析[^。]*争议[^。]*(.+?)(?:\n\n|\n##|\n典型|$)',
        # 查找"争议焦点是"
        r'争议焦点是[^。]*(.+?)(?:\n\n|。|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            dispute = match.group(1).strip()
            dispute = re.sub(r'\s+', ' ', dispute)
            if len(dispute) > 20:
                # 截取合理长度
                if len(dispute) > 500:
                    dispute = dispute[:500] + '...'
                # 排除明显不是争议点的内容
                if not dispute.startswith(('《', '根据', '按照', '依据', '第')):
                    return dispute
    
    return None

def extract_judgment_result_improved(content: str) -> Optional[str]:
    """改进的判决结果提取"""
    if not content:
        return None
    
    # 查找判决结果章节
    patterns = [
        r'裁判结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'判决结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'处理结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        # 查找"一审法院判决"、"法院判决"等
        r'(?:一审|二审|终审)?(?:法院|人民法院)[判决|裁定][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'仲裁委员会[裁决|认定][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        # 查找"判决"、"裁定"等关键词后的内容
        r'[判决|裁定][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            result = re.sub(r'\s+', ' ', result)
            if len(result) > 20:
                # 截取合理长度
                if len(result) > 500:
                    result = result[:500] + '...'
                return result
    
    return None

def comprehensive_fix_cases():
    """全面修复案例数据"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print(f"✓ 成功连接到数据库: {DB_CONFIG['database']}")
        
        # 查询所有案例
        cursor.execute("""
            SELECT id, title, content, case_type, court_name, judge_date, 
                   dispute_point, judgment_result, law_type
            FROM legal_cases
            ORDER BY id
        """)
        
        cases = cursor.fetchall()
        print(f"找到 {len(cases)} 条案例，开始全面修复...")
        
        fixed_count = 0
        for case in cases:
            case_id, title, content, case_type, court_name, judge_date, \
            dispute_point, judgment_result, law_type = case
            
            updates = {}
            
            # 1. 修复法律领域
            new_law_type = extract_law_type_improved(title, content, law_type)
            if new_law_type != law_type:
                updates['law_type'] = new_law_type
            
            # 2. 修复案由
            if not case_type:
                new_case_type = extract_case_type_improved(title, content)
                if new_case_type:
                    updates['case_type'] = new_case_type
            
            # 3. 修复法院名称（如果为空或明显错误）
            invalid_court = (not court_name or 
                           len(court_name) > 100 or
                           any(kw in (court_name or '') for kw in ['诉至', '不服', '《', '》', '规定', '作为', '简称']) or
                           (court_name and '人民法院' not in court_name and '仲裁委员会' not in court_name))
            
            if invalid_court:
                new_court_name = extract_court_name_improved(content or '')
                if new_court_name:
                    updates['court_name'] = new_court_name
            
            # 4. 提取判决日期
            if not judge_date:
                new_judge_date = extract_judge_date_improved(content or '')
                if new_judge_date:
                    updates['judge_date'] = new_judge_date
            
            # 5. 提取争议点
            if not dispute_point:
                new_dispute = extract_dispute_point_improved(content or '')
                if new_dispute:
                    updates['dispute_point'] = new_dispute
            
            # 6. 提取判决结果
            if not judgment_result:
                new_result = extract_judgment_result_improved(content or '')
                if new_result:
                    updates['judgment_result'] = new_result
            
            # 执行更新
            if updates:
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
                
                values.append(case_id)
                
                update_sql = f"""
                UPDATE legal_cases 
                SET {', '.join(set_clauses)}
                WHERE id = %s
                """
                
                try:
                    cursor.execute(update_sql, values)
                    fixed_count += 1
                    print(f"✓ ID {case_id}: {title[:40]}...")
                    if len(updates) > 1:
                        print(f"  更新字段: {', '.join(updates.keys())}")
                except Exception as e:
                    print(f"✗ ID {case_id}: 更新失败 - {e}")
        
        connection.commit()
        print(f"\n✓ 成功修复 {fixed_count} 条案例")
        
        # 最终统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN law_type IS NOT NULL AND law_type != '案例' THEN 1 ELSE 0 END) as valid_law_type,
                SUM(CASE WHEN case_type IS NOT NULL THEN 1 ELSE 0 END) as has_case_type,
                SUM(CASE WHEN court_name IS NOT NULL 
                         AND LENGTH(court_name) <= 100
                         AND court_name NOT LIKE '%诉至%'
                         AND court_name NOT LIKE '%不服%'
                         AND court_name NOT LIKE '%《%'
                         AND (court_name LIKE '%法院%' OR court_name LIKE '%仲裁委员会%')
                    THEN 1 ELSE 0 END) as valid_court,
                SUM(CASE WHEN judge_date IS NOT NULL THEN 1 ELSE 0 END) as has_date,
                SUM(CASE WHEN dispute_point IS NOT NULL THEN 1 ELSE 0 END) as has_dispute,
                SUM(CASE WHEN judgment_result IS NOT NULL THEN 1 ELSE 0 END) as has_result
            FROM legal_cases
        """)
        
        row = cursor.fetchone()
        print(f"\n最终数据质量统计:")
        print(f"总案例数: {row[0]}")
        print(f"有效法律领域: {row[1]} ({row[1]/row[0]*100:.1f}%)")
        print(f"有案由: {row[2]} ({row[2]/row[0]*100:.1f}%)")
        print(f"有效法院名称: {row[3]} ({row[3]/row[0]*100:.1f}%)")
        print(f"有判决日期: {row[4]} ({row[4]/row[0]*100:.1f}%)")
        print(f"有争议点: {row[5]} ({row[5]/row[0]*100:.1f}%)")
        print(f"有判决结果: {row[6]} ({row[6]/row[0]*100:.1f}%)")
        
        # 法律领域分布
        cursor.execute("SELECT law_type, COUNT(*) as count FROM legal_cases GROUP BY law_type ORDER BY count DESC")
        print(f"\n法律领域分布:")
        for r in cursor.fetchall():
            print(f"  {r[0] or 'NULL':<20} : {r[1]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始全面修复案例数据...")
    print("=" * 60)
    success = comprehensive_fix_cases()
    if success:
        print("\n✓ 数据修复完成！")
        sys.exit(0)
    else:
        print("\n✗ 数据修复失败！")
        sys.exit(1)

