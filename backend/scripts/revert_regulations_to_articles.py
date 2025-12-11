#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将误迁移到案例表的法规数据移回法条表
"""

import pymysql
import re
from datetime import datetime

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

def is_regulation_not_case(title, content):
    """判断是否为法规而非案例"""
    if not title:
        return False
    
    # 法规特征关键词
    regulation_keywords = [
        '规定', '办法', '条例', '解释', '规则', '细则', '决定', '通知',
        '最高人民法院关于', '公安机关办理', '程序规定', '组织法',
        '多元化解纠纷', '预防与处置', '权属纠纷处理'
    ]
    
    # 如果标题包含法规关键词，很可能是法规
    for keyword in regulation_keywords:
        if keyword in title:
            return True
    
    # 案例特征关键词（如果包含这些，更可能是案例）
    case_keywords = ['案例', '判例', '判决书', '裁判书', '纠纷案']
    has_case_keyword = any(kw in title for kw in case_keywords)
    
    # 如果标题包含案例关键词，不是法规
    if has_case_keyword:
        return False
    
    # 检查内容特征
    if content:
        # 如果内容中有明确的条号结构（如"第一条"、"第一章"），更可能是法规
        if re.search(r'第[一二三四五六七八九十百千万\d]+[条章节]', content[:500]):
            return True
        
        # 如果内容中有法院、判决日期等案例特征，更可能是案例
        if re.search(r'(审理法院|判决日期|案由|争议点|判决结果)', content[:500]):
            return False
    
    return False

def revert_regulations():
    """将法规从案例表移回法条表"""
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("将误迁移的法规数据从 legal_cases 移回 legal_articles")
    print("=" * 70)
    
    try:
        # 步骤1: 查找所有可能是法规的数据
        print("\n【步骤1】查找法规数据...")
        cursor.execute("""
            SELECT id, title, case_type, content, court_name, judge_date, 
                   dispute_point, judgment_result, law_type, create_time
            FROM legal_cases
        """)
        
        all_cases = cursor.fetchall()
        print(f"总共找到 {len(all_cases)} 条案例数据，开始识别法规...")
        
        # 识别法规数据
        regulations = []
        for case in all_cases:
            case_id, title, case_type, content, court_name, judge_date, \
            dispute_point, judgment_result, law_type, create_time = case
            if is_regulation_not_case(title, content):
                regulations.append(case)
        
        print(f"识别出 {len(regulations)} 条法规数据需要移回法条表")
        
        if len(regulations) == 0:
            print("没有找到需要移回的法规数据")
            conn.close()
            return
        
        # 步骤2: 迁移数据回法条表
        print("\n【步骤2】开始迁移数据回法条表...")
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        migrated_ids = []
        
        for reg in regulations:
            reg_id, title, case_type, content, court_name, judge_date, \
            dispute_point, judgment_result, law_type, create_time = reg
            
            try:
                # 检查是否已存在（基于标题）
                cursor.execute("SELECT id FROM legal_articles WHERE title = %s", (title,))
                if cursor.fetchone():
                    print(f"  - 跳过已存在的法规: {title}")
                    skipped_count += 1
                    migrated_ids.append(reg_id)
                    continue
                
                # 尝试从内容中提取条号（法规通常有条号）
                article_number = None
                if content:
                    # 查找第一个条号
                    match = re.search(r'第([一二三四五六七八九十百千万\d]+)条', content[:1000])
                    if match:
                        article_number = f"第{match.group(1)}条"
                
                # 插入到 legal_articles 表
                insert_sql = """
                    INSERT INTO legal_articles 
                    (title, article_number, content, law_type, publish_org, 
                     publish_date, is_valid, create_time, update_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_sql, (
                    title,
                    article_number,
                    content[:5000] if content else None,  # 限制长度
                    law_type if law_type else '其他',
                    court_name,  # 使用法院名称作为发布机构
                    judge_date,  # 使用判决日期作为发布日期
                    True,
                    create_time,
                    datetime.now()
                ))
                
                migrated_count += 1
                migrated_ids.append(reg_id)
                
                if migrated_count % 50 == 0:
                    print(f"  已迁移 {migrated_count} 条法规...")
                
            except Exception as e:
                print(f"  ✗ 迁移法规失败 {title}: {e}")
                error_count += 1
                continue
        
        # 提交事务
        conn.commit()
        
        # 步骤3: 从案例表中删除这些法规数据
        print("\n【步骤3】从案例表中删除法规数据...")
        if migrated_ids:
            placeholders = ','.join(['%s'] * len(migrated_ids))
            cursor.execute(f"DELETE FROM legal_cases WHERE id IN ({placeholders})", migrated_ids)
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"✓ 已删除 {deleted_count} 条法规数据")
        else:
            deleted_count = 0
            print("  没有需要删除的数据")
        
        # 显示统计
        print("\n" + "=" * 70)
        print("迁移完成！统计信息：")
        print(f"  成功移回法条表: {migrated_count} 条法规")
        print(f"  跳过记录: {skipped_count} 条（已存在）")
        print(f"  错误数量: {error_count} 条")
        print(f"  从案例表删除: {deleted_count} 条")
        print("=" * 70)
        
        # 验证结果
        cursor.execute("SELECT COUNT(*) FROM legal_articles")
        article_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM legal_cases")
        case_count = cursor.fetchone()[0]
        
        print(f"\n当前 legal_articles 表中的法条数: {article_count}")
        print(f"当前 legal_cases 表中的案例数: {case_count}")
        
        conn.close()
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"\n❌ 迁移过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    revert_regulations()

