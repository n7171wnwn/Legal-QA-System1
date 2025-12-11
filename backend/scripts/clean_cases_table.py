#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理案例表中的法规数据，移回法条表
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
    
    # 优先判断：如果标题明确是案例格式，不是法规
    # 案例格式：XXX诉XXX案、XXX纠纷案、XXX案等
    if '诉' in title and '案' in title:
        # 排除法规名称（如"XX诉讼法"）
        if not any(kw in title for kw in ['诉讼法', '仲裁法', '调解法', '组织法']):
            return False  # 是案例，不是法规
    
    # 明确的案例关键词
    explicit_case_keywords = ['案例', '判例', '判决书', '裁判书', '纠纷案']
    if any(kw in title for kw in explicit_case_keywords):
        return False  # 是案例，不是法规
    
    # 法规特征关键词（更精确的列表）
    regulation_keywords = [
        # 完整的法律名称格式
        '中华人民共和国XXX法', '中华人民共和国XXX条例', '中华人民共和国XXX规定',
        # 法律类型后缀（必须与"中华人民共和国"或机构名配合）
        '法', '条例', '规定', '办法', '解释', '规则', '细则', 
        '决定', '通知', '批复', '决议', '意见', '公告',
        # 机构名称 + 法规类型
        '最高人民法院关于', '最高人民检察院关于', '公安机关办理',
        '人民检察院', '人民法院组织法',
        '人民代表大会常务委员会关于', '人民代表大会关于', '国务院关于',
        # 特定法规类型
        '程序规定', '组织法', '诉讼法', '仲裁法', '调解仲裁法',
        '多元化解纠纷', '预防与处置', '权属纠纷处理', '法律援助条例',
        '诉讼费用交纳', '合议庭工作', '审判监督程序', '行政机关负责人',
        '行政诉讼证据', '人民陪审员法',
        # 完整的法律名称
        '刑事诉讼法', '民事诉讼法', '行政诉讼法', '保险法', '公司法',
        '担保法', '物权法', '民法总则', '国家赔偿法',
        '农村土地承包经营纠纷调解仲裁法',
        # 指导性文档
        '攻略', '指南', '手册',
        # 省份相关法规
        '河南省人民代表大会常务委员会', '广东省人民代表大会常务委员会',
        '山东省人民代表大会常务委员会', '经济特区', '直辖市'
    ]
    
    # 检查是否是完整的法规名称格式
    # 格式1: "中华人民共和国XXX法/条例/规定"
    if title.startswith('中华人民共和国'):
        if any(title.endswith(kw) or kw in title for kw in ['法', '条例', '规定', '办法', '解释']):
            return True
    
    # 格式2: "最高人民法院/最高人民检察院关于XXX"
    if title.startswith('最高人民法院') or title.startswith('最高人民检察院'):
        if '关于' in title:
            return True
    
    # 格式3: "XXX人民代表大会常务委员会关于XXX"
    if '人民代表大会常务委员会' in title and '关于' in title:
        return True
    
    # 格式4: 明确的法规类型（如"XXX法"、"XXX条例"）
    if title.endswith('法') or title.endswith('条例') or title.endswith('规定') or title.endswith('办法'):
        # 排除案例标题（如"XXX纠纷案"）
        if not title.endswith('纠纷案') and not title.endswith('案'):
            return True
    
    # 检查内容特征
    if content:
        # 如果内容中有明确的条号结构（如"第一条"、"第一章"），且标题不是案例格式
        if re.search(r'第[一二三四五六七八九十百千万\d]+[条章节]', content[:1000]):
            # 如果标题不是案例格式，更可能是法规
            if not ('诉' in title and '案' in title) and not any(kw in title for kw in explicit_case_keywords):
                return True
    
    return False

def clean_cases_table():
    """清理案例表中的法规数据"""
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("清理案例表中的法规数据")
    print("=" * 70)
    
    try:
        # 步骤1: 查找所有可能是法规的数据
        print("\n【步骤1】查找法规数据...")
        cursor.execute("""
            SELECT id, title, case_type, content, court_name, judge_date, 
                   dispute_point, judgment_result, law_type, create_time
            FROM legal_cases
            ORDER BY id
        """)
        
        all_cases = cursor.fetchall()
        print(f"总共找到 {len(all_cases)} 条案例数据，开始识别法规...")
        
        # 识别法规数据
        regulations = []
        real_cases = []
        for case in all_cases:
            case_id, title, case_type, content, court_name, judge_date, \
            dispute_point, judgment_result, law_type, create_time = case
            if is_regulation_not_case(title, content):
                regulations.append(case)
                print(f"  识别为法规: {title}")
            else:
                real_cases.append(case)
        
        print(f"\n识别结果:")
        print(f"  法规数据: {len(regulations)} 条")
        print(f"  真实案例: {len(real_cases)} 条")
        
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
                existing = cursor.fetchone()
                if existing:
                    print(f"  - 跳过已存在的法规: {title}")
                    skipped_count += 1
                    migrated_ids.append(reg_id)
                    continue
                
                # 尝试从内容中提取条号（法规通常有条号）
                article_number = None
                if content:
                    # 查找第一个条号
                    match = re.search(r'第([一二三四五六七八九十百千万\d]+)条', content[:2000])
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
                
                if migrated_count % 10 == 0:
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
        print("清理完成！统计信息：")
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
        
        # 显示剩余的案例标题
        cursor.execute("SELECT title FROM legal_cases ORDER BY id LIMIT 20")
        remaining_cases = cursor.fetchall()
        print(f"\n剩余的案例（前20条）:")
        for case in remaining_cases:
            print(f"  - {case[0]}")
        
        conn.close()
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"\n❌ 清理过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    clean_cases_table()

