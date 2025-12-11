#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理和修复案例数据中的错误提取
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

def extract_dispute_point(content: str) -> Optional[str]:
    """提取争议点"""
    if not content:
        return None
    patterns = [
        r'争议焦点[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'核心争议[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'本案争议[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            dispute = match.group(1).strip()
            dispute = re.sub(r'\s+', ' ', dispute)
            if 20 <= len(dispute) <= 500:
                return dispute[:500]
    return None

def extract_judgment_result(content: str) -> Optional[str]:
    """提取判决结果"""
    if not content:
        return None
    patterns = [
        r'裁判结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'判决结果[：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
        r'(?:一审|二审)?(?:法院|人民法院)[判决|裁定][：:]\s*(.+?)(?:\n\n|\n##|\n典型|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            result = re.sub(r'\s+', ' ', result)
            if 20 <= len(result) <= 500:
                return result[:500]
    return None

def extract_court_name_fixed(content: str) -> Optional[str]:
    """改进的法院名称提取"""
    if not content:
        return None
    
    # 排除的词汇
    exclude_keywords = ['诉至', '不服', '《', '》', '规定', '法条', '法律', '第', '条', 
                       '作为', '系', '于', '年', '月', '日', '申请', '请求', '主张',
                       '认为', '判决', '裁定', '仲裁', '争议', '纠纷', '案件', '此案',
                       '向', '至', '在', '由', '被', '简称']
    
    # 精确的法院名称模式
    patterns = [
        # 完整的法院名称：XX省/市/县/区 + 人民法院
        r'([^，。\n]{2,20}(?:省|市|县|区|自治区|特别行政区)(?:高级|中级|基层)?人民法院)',
        # 完整的仲裁委员会
        r'([^，。\n]{2,20}(?:劳动人事争议|劳动争议)?仲裁委员会)',
        # 简化的法院名称（必须包含地区名）
        r'([^，。\n]{2,15}(?:市|县|区)(?:高级|中级|基层)?人民法院)',
    ]
    
    all_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        all_matches.extend(matches)
    
    # 去重并验证
    for court in all_matches:
        court = court.strip()
        if 5 <= len(court) <= 50:
            # 排除包含排除词汇的
            if not any(keyword in court for keyword in exclude_keywords):
                # 必须包含"人民法院"或"仲裁委员会"
                if '人民法院' in court or '仲裁委员会' in court:
                    # 排除以特定词开头的
                    if not court.startswith(('向', '至', '在', '由', '被', '简称', '申请')):
                        return court
    
    return None

def clean_and_fix_cases():
    """清理和修复案例数据"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print(f"✓ 成功连接到数据库: {DB_CONFIG['database']}")
        
        # 查找所有需要清理的案例
        query_sql = """
        SELECT id, title, content, court_name, dispute_point, judgment_result
        FROM legal_cases
        """
        
        cursor.execute(query_sql)
        cases = cursor.fetchall()
        
        print(f"找到 {len(cases)} 条案例，开始清理...")
        
        fixed_count = 0
        for case in cases:
            case_id, title, content, court_name, dispute_point, judgment_result = case
            
            updates = {}
            
            # 检查并修复法院名称
            if court_name:
                # 检查是否是错误的法院名称
                invalid_keywords = ['诉至', '不服', '《', '》', '规定', '作为', '系', '于', 
                                  '申请', '请求', '主张', '认为', '案件', '此案', '简称']
                is_invalid = any(keyword in court_name for keyword in invalid_keywords)
                is_too_long = len(court_name) > 100
                no_keyword = '人民法院' not in court_name and '仲裁委员会' not in court_name
                
                if is_invalid or is_too_long or no_keyword:
                    # 重新提取
                    new_court_name = extract_court_name_fixed(content or '')
                    if new_court_name:
                        updates['court_name'] = new_court_name
                        print(f"  ID {case_id}: 修复法院名称")
            
            # 尝试提取争议点
            if not dispute_point:
                new_dispute = extract_dispute_point(content or '')
                if new_dispute:
                    updates['dispute_point'] = new_dispute
                    print(f"  ID {case_id}: 提取争议点")
            
            # 尝试提取判决结果
            if not judgment_result:
                new_result = extract_judgment_result(content or '')
                if new_result:
                    updates['judgment_result'] = new_result
                    print(f"  ID {case_id}: 提取判决结果")
            
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
                except Exception as e:
                    print(f"  ✗ 更新失败 ID {case_id}: {e}")
        
        connection.commit()
        print(f"\n✓ 成功修复 {fixed_count} 条案例")
        
        # 统计最终状态
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN court_name IS NOT NULL 
                         AND court_name NOT LIKE '%诉至%' 
                         AND court_name NOT LIKE '%不服%'
                         AND court_name NOT LIKE '%《%'
                         AND LENGTH(court_name) <= 100
                         AND (court_name LIKE '%法院%' OR court_name LIKE '%仲裁委员会%')
                    THEN 1 ELSE 0 END) as valid_court,
                SUM(CASE WHEN dispute_point IS NOT NULL THEN 1 ELSE 0 END) as has_dispute,
                SUM(CASE WHEN judgment_result IS NOT NULL THEN 1 ELSE 0 END) as has_result
            FROM legal_cases
        """)
        
        row = cursor.fetchone()
        print(f"\n数据质量统计:")
        print(f"总案例数: {row[0]}")
        print(f"有效法院名称: {row[1]} ({row[1]/row[0]*100:.1f}%)")
        print(f"有争议点: {row[2]} ({row[2]/row[0]*100:.1f}%)")
        print(f"有判决结果: {row[3]} ({row[3]/row[0]*100:.1f}%)")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始清理和修复案例数据...")
    print("=" * 60)
    success = clean_and_fix_cases()
    if success:
        print("\n✓ 数据清理完成！")
        sys.exit(0)
    else:
        print("\n✗ 数据清理失败！")
        sys.exit(1)

