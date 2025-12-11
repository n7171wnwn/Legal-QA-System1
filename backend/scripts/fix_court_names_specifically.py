#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门修复法院名称提取问题
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

def find_court_in_text(text: str) -> str:
    """在文本中查找法院名称"""
    if not text:
        return None
    
    # 更精确的模式：必须包含地区名+人民法院/仲裁委员会
    # 优先匹配：XX市XX区人民法院 这种完整格式
    patterns = [
        # 完整的格式：XX省XX市XX区人民法院（最优先）
        # 匹配：北京市朝阳区人民法院、XX市XX区人民法院等
        r'([^，。\n]{2,30}(?:省|市|县|区|自治区|特别行政区)(?:高级|中级|基层)?人民法院)',
        # 匹配：XX市XX区人民法院（不包含省）
        r'([^，。\n]{2,25}(?:市|县|区)(?:高级|中级|基层)?人民法院)',
        # 仲裁委员会
        r'([^，。\n]{2,30}(?:劳动人事争议|劳动争议)?仲裁委员会)',
    ]
    
    exclude = ['诉至', '不服', '《', '》', '规定', '作为', '系', '向', '至', '简称', 
               '申请', '请求', '主张', '认为', '案件', '此案', '审理', '开庭', '应予', '支持',
               '作出', '撤销', '维持', '判决', '裁定', '号', '（', '）']
    
    all_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        all_matches.extend(matches)
    
    # 验证每个匹配
    valid_courts = []
    for court in all_matches:
        court = court.strip()
        # 基本长度验证
        if not (5 <= len(court) <= 50):
            continue
        
        # 排除包含排除词的
        if any(kw in court for kw in exclude):
            continue
        
        # 必须包含关键词
        if '人民法院' not in court and '仲裁委员会' not in court:
            continue
        
        # 不能以特定词开头
        if court.startswith(('向', '至', '在', '由', '被', '简称', '申请', '诉', '不服', '张某', '李某', '王某', '人民法院应予', '31日', '（')):
            continue
        
        # 不能以常见姓氏开头
        if re.match(r'^[张李王刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤]', court):
            continue
        
        # 排除包含"应予"、"支持"、"作出"、"撤销"等词的（这些是法条描述或判决书内容，不是法院名称）
        if any(kw in court for kw in ['应予', '支持', '作出', '撤销', '维持', '判决', '裁定', '号']):
            continue
        
        # 验证格式：应该是纯法院名称，不应该包含其他句子成分
        # 法院名称应该以"人民法院"或"仲裁委员会"结尾
        if not (court.endswith('人民法院') or court.endswith('仲裁委员会')):
            continue
        
        # 进一步验证：不应该包含数字、括号等（这些通常是判决书编号）
        if re.search(r'[0-9（）()]', court):
            continue
        
        valid_courts.append(court)
    
    # 优先返回包含省市区信息的完整法院名称
    for court in valid_courts:
        if any(kw in court for kw in ['省', '市', '区', '县']):
            # 验证格式：应该是"XX市XX区人民法院"这样的格式
            # 使用更宽松的验证，只要以"人民法院"结尾且包含地区名即可
            if court.endswith('人民法院') and any(kw in court for kw in ['省', '市', '区', '县']):
                # 确保不包含数字、括号等（这些通常是判决书编号）
                if not re.search(r'[0-9（）()]', court):
                    return court
    
    # 如果没有找到包含省市区信息的，尝试返回第一个有效的
    for court in valid_courts:
        # 至少应该包含"市"或"区"或"县"
        if any(kw in court for kw in ['市', '区', '县']):
            if court.endswith('人民法院') and not re.search(r'[0-9（）()]', court):
                return court
    
    # 如果还是没有，返回第一个有效的（但必须是完整的法院名称格式）
    for court in valid_courts:
        if court.endswith('人民法院') or court.endswith('仲裁委员会'):
            if not re.search(r'[0-9（）()]', court):
                return court
    
    return None

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("专门修复法院名称...")
print("=" * 60)

# 查找所有案例，强制重新提取法院名称
cursor.execute("""
    SELECT id, title, content, court_name
    FROM legal_cases
    ORDER BY id
""")

cases = cursor.fetchall()
print(f"找到 {len(cases)} 条需要修复的案例\n")

fixed = 0
for case in cases:
    case_id, title, content, court_name = case
    
    # 检查当前法院名称是否有效
    is_invalid = (not court_name or 
                 len(court_name) > 100 or
                 any(kw in (court_name or '') for kw in ['诉至', '不服', '《', '》', '规定', '作为', '简称', '向', '应予', '支持', '作出', '撤销']) or
                 (court_name and '人民法院' not in court_name and '仲裁委员会' not in court_name))
    
    # 尝试提取法院名称
    new_court = find_court_in_text(content or '')
    
    if new_court:
        # 如果当前法院名称无效，或者新提取的更好，则更新
        if is_invalid or not court_name:
            try:
                cursor.execute("UPDATE legal_cases SET court_name = %s WHERE id = %s", (new_court, case_id))
                if is_invalid:
                    print(f"✓ ID {case_id}: {title[:45]}...")
                    print(f"  旧: {court_name[:50] if court_name else 'NULL'}...")
                    print(f"  新: {new_court}")
                else:
                    print(f"✓ ID {case_id}: {title[:45]}... 提取到: {new_court}")
                fixed += 1
            except Exception as e:
                print(f"✗ ID {case_id}: 更新失败 - {e}")
    elif is_invalid:
        # 如果无法提取且当前无效，显示提示
        content_preview = (content or '')[:200]
        if '人民法院' in content_preview or '仲裁委员会' in content_preview:
            print(f"⚠ ID {case_id}: {title[:45]}...")
            print(f"  内容中有法院相关词汇，但无法精确提取")
            print(f"  当前法院: {court_name[:50] if court_name else 'NULL'}...")

conn.commit()
print(f"\n✓ 修复了 {fixed} 条案例的法院名称")

# 最终统计
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN court_name IS NOT NULL 
                 AND LENGTH(court_name) <= 100
                 AND court_name NOT LIKE '%诉至%'
                 AND court_name NOT LIKE '%不服%'
                 AND court_name NOT LIKE '%《%'
                 AND (court_name LIKE '%法院%' OR court_name LIKE '%仲裁委员会%')
            THEN 1 ELSE 0 END) as valid_court
    FROM legal_cases
""")
row = cursor.fetchone()
print(f"\n最终统计:")
print(f"总案例数: {row[0]}")
print(f"有效法院名称: {row[1]} ({row[1]/row[0]*100:.1f}%)")

cursor.close()
conn.close()
print("\n✓ 完成！")

