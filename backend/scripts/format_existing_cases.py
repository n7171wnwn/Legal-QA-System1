#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格式化原有案例数据，使其格式与新数据一致
"""

import pymysql
import sys
import re
from datetime import datetime
from typing import Optional, Dict

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

# 法律领域关键词映射
LAW_TYPE_KEYWORDS = {
    '劳动法': ['劳动', '加班', '工资', '劳动合同', '劳动争议', '仲裁', '工伤', '解除合同', '赔偿'],
    '民法': ['合同', '买卖', '租赁', '侵权', '赔偿', '离婚', '继承', '财产', '房屋', '债务'],
    '刑法': ['故意', '伤害', '诈骗', '盗窃', '抢劫', '杀人', '犯罪', '刑事', '刑罚'],
    '行政法': ['行政', '处罚', '许可', '复议', '诉讼'],
    '知识产权法': ['专利', '商标', '著作权', '知识产权', '侵权'],
    '消费者权益保护法': ['消费', '购物', '商品', '服务', '消费者']
}

# 案由关键词映射
CASE_TYPE_KEYWORDS = {
    '劳动争议': ['劳动', '加班', '工资', '劳动合同', '解除'],
    '合同纠纷': ['合同', '买卖', '租赁', '服务'],
    '侵权纠纷': ['侵权', '损害', '赔偿', '人身'],
    '离婚纠纷': ['离婚', '婚姻'],
    '继承纠纷': ['继承', '遗产'],
    '人身损害赔偿': ['人身', '损害', '伤害', '赔偿'],
    '财产纠纷': ['财产', '债务', '房屋'],
    '故意伤害罪': ['故意', '伤害'],
    '诈骗罪': ['诈骗'],
    '盗窃罪': ['盗窃']
}

def extract_court_name(content: str) -> Optional[str]:
    """从内容中提取审理法院"""
    if not content:
        return None
    
    # 排除的词汇（如果包含这些词，不是真正的法院名称）
    exclude_keywords = ['诉至', '不服', '《', '》', '规定', '法条', '法律', '第', '条', 
                       '作为', '系', '于', '年', '月', '日', '申请', '请求', '主张',
                       '认为', '判决', '裁定', '仲裁', '争议', '纠纷', '案件']
    
    # 更精确的法院名称模式（必须包含完整的法院名称格式）
    patterns = [
        # 完整的法院名称格式：XX省/市/县/区 + 人民法院
        r'([^，。\n]{2,20}(?:省|市|县|区|自治区|特别行政区)(?:高级|中级|基层)?人民法院)',
        # 完整的仲裁委员会格式
        r'([^，。\n]{2,20}(?:劳动人事争议|劳动争议)?仲裁委员会)',
        # 简化的法院名称（但必须包含地区名）
        r'([^，。\n]{2,15}(?:市|县|区)(?:高级|中级|基层)?人民法院)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        if matches:
            for court in matches:
                court = court.strip()
                # 基本验证
                if 5 <= len(court) <= 50:
                    # 排除包含排除词汇的匹配
                    if not any(keyword in court for keyword in exclude_keywords):
                        # 必须包含"人民法院"或"仲裁委员会"
                        if '人民法院' in court or '仲裁委员会' in court:
                            # 排除以"向"、"至"等词开头的
                            if not court.startswith(('向', '至', '在', '由', '被')):
                                return court
    
    return None

def extract_judge_date(content: str) -> Optional[datetime]:
    """从内容中提取判决日期"""
    if not content:
        return None
    
    # 匹配日期格式
    date_patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})'
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, content)
        if matches:
            try:
                year, month, day = matches[-1]  # 取最后一个日期
                return datetime(int(year), int(month), int(day))
            except:
                continue
    
    return None

def extract_dispute_point(content: str) -> Optional[str]:
    """从内容中提取核心争议点"""
    if not content:
        return None
    
    # 查找争议点相关章节（更全面的模式）
    patterns = [
        r'争议焦点[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'核心争议[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'本案争议[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'主要争议[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'争议[焦点|点|问题][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'焦点[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        # 查找"案例分析"章节中的争议点
        r'案例分析[^。]*争议[^。]*(.+?)(?:\n\n|\n##|\n典型|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            dispute = match.group(1).strip()
            # 清理多余的空白字符和换行
            dispute = re.sub(r'\s+', ' ', dispute)
            # 如果提取的内容太长，截取前500字符
            if len(dispute) > 500:
                dispute = dispute[:500] + '...'
            if 20 <= len(dispute) <= 2000:
                # 排除明显不是争议点的内容
                if not dispute.startswith(('《', '根据', '按照', '依据')):
                    return dispute
    
    return None

def extract_judgment_result(content: str) -> Optional[str]:
    """从内容中提取判决结果"""
    if not content:
        return None
    
    # 查找判决结果相关章节（更全面的模式）
    patterns = [
        r'裁判结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'判决结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'处理结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'最终[判决|裁决][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'法院[判决|认定][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'仲裁[裁决|认定][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        # 查找"一审法院判决"、"法院判决"等格式
        r'(?:一审|二审|终审)?(?:法院|人民法院)[判决|裁定][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            # 清理多余的空白字符和换行
            result = re.sub(r'\s+', ' ', result)
            # 如果提取的内容太长，截取前500字符
            if len(result) > 500:
                result = result[:500] + '...'
            if 20 <= len(result) <= 2000:
                return result
    
    return None

def detect_law_type(title: str, content: str, current_law_type: str) -> str:
    """检测法律领域"""
    if current_law_type and current_law_type != '案例':
        return current_law_type
    
    text = (title + ' ' + (content or ''))[:1000]  # 只检查前1000字符
    
    for law_type, keywords in LAW_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return law_type
    
    return '民法'  # 默认返回民法

def detect_case_type(title: str, content: str) -> Optional[str]:
    """检测案由"""
    text = (title + ' ' + (content or ''))[:500]
    
    for case_type, keywords in CASE_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return case_type
    
    # 如果标题包含"纠纷"、"争议"等，提取案由
    if '纠纷' in title:
        return title.split('纠纷')[0] + '纠纷'
    if '争议' in title:
        return title.split('争议')[0] + '争议'
    
    return None

def format_existing_cases():
    """格式化原有案例数据"""
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print(f"✓ 成功连接到数据库: {DB_CONFIG['database']}")
        
        # 查询需要格式化的案例（law_type为"案例"或缺少关键字段的，或法院名称明显错误的）
        query_sql = """
        SELECT id, title, case_type, content, court_name, judge_date, 
               dispute_point, judgment_result, law_type
        FROM legal_cases
        WHERE law_type = '案例' 
           OR case_type IS NULL 
           OR court_name IS NULL 
           OR court_name LIKE '%诉至%' 
           OR court_name LIKE '%不服%'
           OR court_name LIKE '%《%'
           OR court_name LIKE '%规定%'
           OR court_name LIKE '%作为%'
           OR LENGTH(court_name) > 100
           OR (court_name IS NOT NULL AND court_name NOT LIKE '%法院%' AND court_name NOT LIKE '%仲裁委员会%')
           OR dispute_point IS NULL
           OR judgment_result IS NULL
        """
        
        cursor.execute(query_sql)
        cases = cursor.fetchall()
        
        print(f"找到 {len(cases)} 条需要格式化的案例")
        
        updated_count = 0
        for case in cases:
            case_id, title, case_type, content, court_name, judge_date, \
            dispute_point, judgment_result, law_type = case
            
            updates = {}
            
            # 更新法律领域
            new_law_type = detect_law_type(title, content, law_type)
            if new_law_type != law_type:
                updates['law_type'] = new_law_type
            
            # 更新案由
            if not case_type:
                new_case_type = detect_case_type(title, content)
                if new_case_type:
                    updates['case_type'] = new_case_type
            
            # 更新审理法院（如果当前法院名称明显不正确，也尝试更新）
            invalid_court_keywords = ['诉至', '不服', '《', '》', '规定', '作为', '系', '于', 
                                     '申请', '请求', '主张', '认为', '案件', '此案']
            current_court_invalid = any(keyword in (court_name or '') for keyword in invalid_court_keywords)
            current_court_too_long = court_name and len(court_name) > 100
            current_court_no_keyword = court_name and '人民法院' not in court_name and '仲裁委员会' not in court_name
            
            if not court_name or current_court_invalid or current_court_too_long or current_court_no_keyword:
                new_court_name = extract_court_name(content or '')
                if new_court_name:
                    updates['court_name'] = new_court_name
            
            # 更新判决日期
            if not judge_date:
                new_judge_date = extract_judge_date(content or '')
                if new_judge_date:
                    updates['judge_date'] = new_judge_date
            
            # 更新核心争议点（即使已有也尝试更新，因为可能提取不完整）
            new_dispute_point = extract_dispute_point(content or '')
            if new_dispute_point and (not dispute_point or len(dispute_point) < len(new_dispute_point)):
                updates['dispute_point'] = new_dispute_point
            
            # 更新判决结果（即使已有也尝试更新，因为可能提取不完整）
            new_judgment_result = extract_judgment_result(content or '')
            if new_judgment_result and (not judgment_result or len(judgment_result) < len(new_judgment_result)):
                updates['judgment_result'] = new_judgment_result
            
            # 如果有更新，执行更新
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
                    updated_count += 1
                    print(f"✓ 更新案例 ID {case_id}: {title[:40]}...")
                    if len(updates) > 1:
                        print(f"  更新字段: {', '.join(updates.keys())}")
                except Exception as e:
                    print(f"✗ 更新失败 ID {case_id}: {e}")
        
        # 提交事务
        connection.commit()
        print(f"\n✓ 成功更新 {updated_count} 条案例")
        
        # 统计更新后的数据
        cursor.execute("SELECT law_type, COUNT(*) as count FROM legal_cases GROUP BY law_type")
        print("\n更新后的法律领域分布:")
        print("法律领域 | 数量")
        print("-" * 30)
        for row in cursor.fetchall():
            print(f"{row[0] or '未分类':<10} | {row[1]}")
        
        # 关闭连接
        cursor.close()
        connection.close()
        print("\n✓ 数据库连接已关闭")
        
        return True
        
    except Exception as e:
        print(f"✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始格式化原有案例数据...")
    print("=" * 60)
    success = format_existing_cases()
    if success:
        print("\n✓ 数据格式化完成！")
        sys.exit(0)
    else:
        print("\n✗ 数据格式化失败！")
        sys.exit(1)

