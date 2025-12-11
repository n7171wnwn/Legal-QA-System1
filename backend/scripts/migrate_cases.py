#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将案例数据从 legal_articles 表迁移到 legal_cases 表
"""

import pymysql
import re
from datetime import datetime

# 确保导入re模块用于正则表达式

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

def extract_case_info(content):
    """从案例内容中提取信息"""
    case_type = None
    court_name = None
    judge_date = None
    dispute_point = None
    judgment_result = None
    
    if not content:
        return case_type, court_name, judge_date, dispute_point, judgment_result
    
    # 提取案由
    case_type_patterns = [
        r'案由[：:]\s*(.+?)(?:\n|$)',
        r'案件类型[：:]\s*(.+?)(?:\n|$)',
    ]
    for pattern in case_type_patterns:
        match = re.search(pattern, content)
        if match:
            case_type = match.group(1).strip()
            break
    
    # 提取审理法院
    court_patterns = [
        r'审理法院[：:]\s*(.+?)(?:\n|$)',
        r'法院[：:]\s*(.+?)(?:\n|$)',
        r'(.+?法院)',
    ]
    for pattern in court_patterns:
        match = re.search(pattern, content)
        if match:
            court_name = match.group(1).strip()
            if len(court_name) < 50:  # 避免匹配到太长的内容
                break
    
    # 提取判决日期
    date_patterns = [
        r'判决日期[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?)',
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, content)
        if match:
            if len(match.groups()) == 3:
                year, month, day = match.groups()
                date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                date_str = match.group(1).replace('年', '-').replace('月', '-').replace('日', '')
                date_str = re.sub(r'[年月日]', '-', date_str).strip('-')
                parts = date_str.split('-')
                if len(parts) >= 3:
                    date_str = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            
            try:
                judge_date = datetime.strptime(date_str, '%Y-%m-%d')
            except:
                try:
                    judge_date = datetime.strptime(date_str, '%Y-%m')
                except:
                    pass
            if judge_date:
                break
    
    # 提取核心争议点
    dispute_patterns = [
        r'争议点[：:]\s*(.+?)(?:\n\n|$)',
        r'核心争议[：:]\s*(.+?)(?:\n\n|$)',
        r'争议焦点[：:]\s*(.+?)(?:\n\n|$)',
    ]
    for pattern in dispute_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            dispute_point = match.group(1).strip()[:2000]  # 限制长度
            break
    
    # 提取判决结果
    result_patterns = [
        r'判决结果[：:]\s*(.+?)(?:\n\n|$)',
        r'判决[：:]\s*(.+?)(?:\n\n|$)',
        r'裁判结果[：:]\s*(.+?)(?:\n\n|$)',
    ]
    for pattern in result_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            judgment_result = match.group(1).strip()[:2000]  # 限制长度
            break
    
    return case_type, court_name, judge_date, dispute_point, judgment_result

def is_case_data(title, content, article_number, law_type):
    """判断是否为案例数据（排除法规）"""
    if not title:
        return False
    
    # 首先排除法规（优先级最高）
    regulation_keywords = [
        '规定', '办法', '条例', '解释', '规则', '细则', '决定', '通知',
        '最高人民法院关于', '公安机关办理', '程序规定', '组织法',
        '多元化解纠纷', '预防与处置', '权属纠纷处理', '法律援助条例',
        '诉讼费用交纳', '人民检察院', '人民法院在线', '合议庭工作',
        '审判监督程序', '行政机关负责人', '行政诉讼证据', '人民陪审员法',
        '保险法', '公司法', '担保法', '物权法', '民法总则', '国家赔偿法'
    ]
    
    # 如果标题包含法规关键词，排除（不是案例）
    for keyword in regulation_keywords:
        if keyword in title:
            return False
    
    # 如果内容中有明确的条号结构（如"第一条"、"第一章"），更可能是法规
    if content and re.search(r'第[一二三四五六七八九十百千万\d]+[条章节]', content[:500]):
        # 但如果标题明确包含案例关键词，还是认为是案例
        if not any(kw in title for kw in ['案例', '判例', '判决书', '裁判书']):
            return False
    
    # 方法1: law_type 明确标记为案例
    if law_type and ('案例' in str(law_type) or '判例' in str(law_type)):
        return True
    
    # 方法2: title中包含明确的案例关键词（排除"案件"、"纠纷"，因为法规也可能包含）
    case_keywords_in_title = ['案例', '判例', '判决书', '裁判书', '纠纷案']
    if title:
        for keyword in case_keywords_in_title:
            if keyword in title:
                return True
    
    # 方法3: content中包含明确的案例特征（需要多个特征同时存在）
    if content:
        case_keywords_in_content = [
            '审理法院', '判决日期', '案由', '争议点', '判决结果',
            '法院审理', '一审', '二审', '再审', '终审',
            '原告', '被告', '上诉人', '被上诉人', '当事人'
        ]
        match_count = 0
        for keyword in case_keywords_in_content:
            if keyword in content:
                match_count += 1
        # 如果匹配到4个以上案例特征，且没有法规特征，认为是案例
        if match_count >= 4:
            # 再次确认不是法规
            if not any(kw in title for kw in regulation_keywords):
                return True
    
    return False

def migrate_cases():
    """迁移案例数据"""
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("将案例数据从 legal_articles 迁移到 legal_cases")
    print("=" * 70)
    
    try:
        # 步骤1: 查找所有可能的案例数据
        print("\n【步骤1】查找案例数据...")
        cursor.execute("""
            SELECT id, title, article_number, content, law_type, create_time
            FROM legal_articles
            WHERE is_valid = 1
        """)
        
        all_articles = cursor.fetchall()
        print(f"总共找到 {len(all_articles)} 条法条数据，开始识别案例...")
        
        # 识别案例数据
        cases = []
        for article in all_articles:
            article_id, title, article_number, content, law_type, create_time = article
            if is_case_data(title, content, article_number, law_type):
                cases.append((article_id, title, content, law_type, create_time))
        
        print(f"识别出 {len(cases)} 条案例数据")
        
        if len(cases) == 0:
            print("没有找到案例数据，无需迁移")
            conn.close()
            return
        
        # 步骤2: 迁移数据
        print("\n【步骤2】开始迁移数据...")
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        migrated_ids = []  # 记录成功迁移的ID
        
        for case in cases:
            case_id, title, content, law_type, create_time = case
            
            try:
                # 提取案例信息
                case_type, court_name, judge_date, dispute_point, judgment_result = extract_case_info(content)
                
                # 检查是否已存在（基于标题）
                cursor.execute("SELECT id FROM legal_cases WHERE title = %s", (title,))
                if cursor.fetchone():
                    print(f"  - 跳过已存在的案例: {title}")
                    skipped_count += 1
                    migrated_ids.append(case_id)  # 即使已存在，也记录ID以便删除
                    continue
                
                # 插入到 legal_cases 表
                insert_sql = """
                    INSERT INTO legal_cases 
                    (title, case_type, content, court_name, judge_date, 
                     dispute_point, judgment_result, law_type, create_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_sql, (
                    title,
                    case_type,
                    content[:5000] if content else None,  # 限制长度
                    court_name,
                    judge_date,
                    dispute_point,
                    judgment_result,
                    law_type,
                    create_time
                ))
                
                migrated_count += 1
                migrated_ids.append(case_id)  # 记录成功迁移的ID
                
                if migrated_count % 10 == 0:
                    print(f"  已迁移 {migrated_count} 条案例...")
                
            except Exception as e:
                print(f"  ✗ 迁移案例失败 {title}: {e}")
                error_count += 1
                continue
        
        # 提交事务
        conn.commit()
        
        # 步骤3: 删除 legal_articles 表中的案例数据
        print("\n【步骤3】删除 legal_articles 表中的案例数据...")
        if migrated_ids:
            placeholders = ','.join(['%s'] * len(migrated_ids))
            cursor.execute(f"DELETE FROM legal_articles WHERE id IN ({placeholders})", migrated_ids)
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"✓ 已删除 {deleted_count} 条案例数据")
        else:
            deleted_count = 0
            print("  没有需要删除的数据")
        
        # 显示统计
        print("\n" + "=" * 70)
        print("迁移完成！统计信息：")
        print(f"  成功迁移: {migrated_count} 条案例")
        print(f"  跳过记录: {skipped_count} 条（已存在）")
        print(f"  错误数量: {error_count} 条")
        print(f"  从法条表删除: {deleted_count} 条")
        print("=" * 70)
        
        # 验证结果
        cursor.execute("SELECT COUNT(*) FROM legal_cases")
        case_count = cursor.fetchone()[0]
        
        # 重新检查是否还有案例数据
        cursor.execute("""
            SELECT id, title, article_number, content, law_type
            FROM legal_articles
            WHERE is_valid = 1
        """)
        remaining_articles = cursor.fetchall()
        remaining_cases = 0
        for article in remaining_articles:
            article_id, title, article_number, content, law_type = article
            if is_case_data(title, content, article_number, law_type):
                remaining_cases += 1
        
        print(f"\n当前 legal_cases 表中的案例数: {case_count}")
        print(f"legal_articles 表中剩余的案例数: {remaining_cases}")
        
        conn.close()
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"\n❌ 迁移过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    migrate_cases()










