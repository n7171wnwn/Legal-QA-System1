#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从法律术语词典提取数据并导入到legal_concepts表
支持多种词典格式：文本、PDF、JSON、CSV等
"""

import pymysql
import json
import csv
import re
import sys
import os
from typing import List, Dict, Optional

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

def detect_law_type(text: str) -> str:
    """根据文本内容自动检测法律领域"""
    if not text:
        return '民法'
    
    # 劳动法关键词
    if any(kw in text for kw in ['劳动', '加班', '工资', '劳动合同', '劳动争议', '用人单位', '劳动者', '工伤', '仲裁', '工作']):
        return '劳动法'
    
    # 刑法关键词
    if any(kw in text for kw in ['犯罪', '故意', '伤害', '诈骗', '盗窃', '刑事', '刑罚', '罪', '杀人', '抢劫', '贪污', '受贿']):
        return '刑法'
    
    # 行政法关键词
    if any(kw in text for kw in ['行政', '政府', '机关', '处罚', '许可', '复议', '协议', '强制', '诉讼']):
        return '行政法'
    
    # 知识产权法关键词
    if any(kw in text for kw in ['专利', '商标', '著作权', '知识产权', '版权', '商业秘密', '侵权']):
        return '知识产权法'
    
    # 消费者权益保护法关键词
    if any(kw in text for kw in ['消费', '消费者', '经营者', '商品', '服务', '食品', '安全', '欺诈', '赔偿']):
        return '消费者权益保护法'
    
    # 程序法关键词
    if any(kw in text for kw in ['诉讼', '程序', '审理', '判决', '裁定', '上诉', '申诉', '执行', '时效', '举证']):
        return '程序法'
    
    # 默认民法
    return '民法'

def extract_from_text_dictionary(file_path: str) -> List[Dict]:
    """从文本格式的词典提取数据（格式：概念名：定义）"""
    concepts = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配模式：概念名：定义 或 概念名——定义 或 概念名 定义
    patterns = [
        r'([^：:\n]{2,50})[：:]([^。\n]{10,500})',
        r'([^——\n]{2,50})——([^。\n]{10,500})',
        r'([^：:\n]{2,50})\s+([^。\n]{10,500})',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            name = match[0].strip()
            definition = match[1].strip()
            
            if len(name) <= 100 and len(definition) >= 10:
                concepts.append({
                    'name': name,
                    'definition': definition,
                    'explanation': definition,  # 如果没有详细解释，使用定义
                    'law_type': detect_law_type(name + ' ' + definition),
                    'related_concepts': ''
                })
    
    return concepts

def extract_from_markdown_dictionary(file_path: str) -> List[Dict]:
    """从Markdown格式的词典提取数据"""
    concepts = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_concept = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        # 检测标题（概念名）
        if line.startswith('#'):
            if current_concept:
                concepts.append(current_concept)
            
            name = line.lstrip('#').strip()
            current_concept = {
                'name': name,
                'definition': '',
                'explanation': '',
                'law_type': '',
                'related_concepts': ''
            }
            current_content = []
        elif current_concept:
            current_content.append(line)
            current_concept['explanation'] += line + '\n'
    
    if current_concept:
        concepts.append(current_concept)
    
    # 处理提取的概念
    for concept in concepts:
        if concept['explanation']:
            # 第一段作为定义
            paragraphs = concept['explanation'].split('\n\n')
            if paragraphs:
                concept['definition'] = paragraphs[0].strip()[:2000]
            concept['law_type'] = detect_law_type(concept['name'] + ' ' + concept['explanation'])
    
    return concepts

def extract_from_structured_text(file_path: str) -> List[Dict]:
    """从结构化文本提取（每行一个概念，格式：概念名|定义|解释|法律领域）"""
    concepts = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('|')
            if len(parts) >= 2:
                concept = {
                    'name': parts[0].strip(),
                    'definition': parts[1].strip() if len(parts) > 1 else '',
                    'explanation': parts[2].strip() if len(parts) > 2 else parts[1].strip(),
                    'law_type': parts[3].strip() if len(parts) > 3 else '',
                    'related_concepts': parts[4].strip() if len(parts) > 4 else ''
                }
                
                if not concept['law_type']:
                    concept['law_type'] = detect_law_type(concept['name'] + ' ' + concept['definition'])
                
                concepts.append(concept)
    
    return concepts

def import_concepts_to_db(concepts: List[Dict]):
    """将概念导入数据库"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"\n开始导入 {len(concepts)} 条概念到数据库...")
        print("=" * 60)
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        sql = """
        INSERT INTO legal_concepts 
        (name, definition, explanation, law_type, related_concepts, create_time, update_time)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
        definition = VALUES(definition),
        explanation = VALUES(explanation),
        law_type = VALUES(law_type),
        related_concepts = VALUES(related_concepts),
        update_time = NOW()
        """
        
        for i, concept in enumerate(concepts):
            try:
                # 验证和清理数据
                name = concept.get('name', '').strip()[:100]
                if not name:
                    continue
                
                definition = (concept.get('definition') or '')[:2000]
                explanation = (concept.get('explanation') or definition)[:5000]
                law_type = concept.get('law_type') or detect_law_type(name + ' ' + definition)
                related = (concept.get('related_concepts') or '')[:1000]
                
                cursor.execute(sql, (name, definition, explanation, law_type, related))
                success_count += 1
                
                if (i + 1) % 50 == 0:
                    conn.commit()
                    print(f"  已导入 {i + 1}/{len(concepts)} 条...")
            except pymysql.err.IntegrityError:
                skip_count += 1
            except Exception as e:
                error_count += 1
                print(f"  ✗ 导入失败: {concept.get('name', 'Unknown')[:30]}... - {e}")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print(f"导入完成!")
        print(f"  成功: {success_count} 条")
        print(f"  跳过(重复): {skip_count} 条")
        print(f"  失败: {error_count} 条")
        
        # 统计信息
        cursor.execute("SELECT COUNT(*) FROM legal_concepts")
        total = cursor.fetchone()[0]
        print(f"\n数据库中共有 {total} 条概念")
        
        cursor.execute("SELECT law_type, COUNT(*) as count FROM legal_concepts GROUP BY law_type ORDER BY count DESC")
        print("\n法律领域分布:")
        for row in cursor.fetchall():
            print(f"  {row[0] or '未分类':<20} : {row[1]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("法律术语词典数据提取工具")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python extract_from_legal_dictionary.py <词典文件路径> [格式类型]")
        print("\n支持的格式:")
        print("  - text: 文本格式（概念名：定义）")
        print("  - markdown: Markdown格式")
        print("  - structured: 结构化文本（概念名|定义|解释|法律领域）")
        print("  - json: JSON格式")
        print("  - csv: CSV格式")
        print("\n示例:")
        print("  python extract_from_legal_dictionary.py dictionary.txt text")
        print("  python extract_from_legal_dictionary.py dictionary.md markdown")
        return
    
    file_path = sys.argv[1]
    format_type = sys.argv[2] if len(sys.argv) > 2 else 'auto'
    
    if not os.path.exists(file_path):
        print(f"✗ 文件不存在: {file_path}")
        return
    
    # 自动检测格式
    if format_type == 'auto':
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.json':
            format_type = 'json'
        elif ext == '.csv':
            format_type = 'csv'
        elif ext == '.md':
            format_type = 'markdown'
        else:
            format_type = 'text'
    
    print(f"\n文件: {file_path}")
    print(f"格式: {format_type}")
    print("=" * 60)
    
    concepts = []
    
    try:
        if format_type == 'text':
            concepts = extract_from_text_dictionary(file_path)
        elif format_type == 'markdown':
            concepts = extract_from_markdown_dictionary(file_path)
        elif format_type == 'structured':
            concepts = extract_from_structured_text(file_path)
        elif format_type == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    concepts = data
                elif isinstance(data, dict) and 'concepts' in data:
                    concepts = data['concepts']
        elif format_type == 'csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                concepts = list(reader)
        else:
            print(f"✗ 不支持的格式: {format_type}")
            return
        
        print(f"提取到 {len(concepts)} 条概念")
        
        if concepts:
            import_concepts_to_db(concepts)
        else:
            print("✗ 未能提取到概念数据")
            
    except Exception as e:
        print(f"✗ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()













