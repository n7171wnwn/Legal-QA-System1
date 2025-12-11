#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入DISC-LawLLM数据集到legal_concepts表
支持多种数据格式：JSON、CSV、TXT等
"""

import pymysql
import json
import csv
import sys
import os
import re
from datetime import datetime
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
    
    text_lower = text.lower()
    
    # 劳动法关键词
    if any(kw in text for kw in ['劳动', '加班', '工资', '劳动合同', '劳动争议', '用人单位', '劳动者', '工伤', '仲裁']):
        return '劳动法'
    
    # 刑法关键词
    if any(kw in text for kw in ['犯罪', '故意', '伤害', '诈骗', '盗窃', '刑事', '刑罚', '罪']):
        return '刑法'
    
    # 行政法关键词
    if any(kw in text for kw in ['行政', '政府', '机关', '处罚', '许可', '复议', '协议']):
        return '行政法'
    
    # 知识产权法关键词
    if any(kw in text for kw in ['专利', '商标', '著作权', '知识产权', '版权']):
        return '知识产权法'
    
    # 消费者权益保护法关键词
    if any(kw in text for kw in ['消费', '消费者', '经营者', '商品', '服务', '食品', '安全']):
        return '消费者权益保护法'
    
    # 程序法关键词
    if any(kw in text for kw in ['诉讼', '程序', '审理', '判决', '裁定', '上诉', '申诉']):
        return '程序法'
    
    # 默认民法
    return '民法'

def extract_related_concepts(text: str, all_concepts: List[str]) -> str:
    """从文本中提取相关概念"""
    if not text or not all_concepts:
        return ''
    
    related = []
    for concept in all_concepts:
        if concept in text and len(concept) > 1:
            related.append(concept)
    
    # 返回前10个相关概念
    return ','.join(related[:10])

def clean_text(text: str, max_length: int = None) -> str:
    """清理文本"""
    if not text:
        return ''
    
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 截断长度
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text

def import_from_json(file_path: str):
    """从JSON文件导入"""
    print(f"正在读取JSON文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    concepts = []
    
    # 处理不同的JSON结构
    if isinstance(data, list):
        concepts = data
    elif isinstance(data, dict):
        # 可能是 {'concepts': [...]} 格式
        if 'concepts' in data:
            concepts = data['concepts']
        elif 'data' in data:
            concepts = data['data']
        else:
            # 尝试将dict转换为list
            concepts = [data]
    
    print(f"找到 {len(concepts)} 条概念数据")
    return concepts

def import_from_csv(file_path: str):
    """从CSV文件导入"""
    print(f"正在读取CSV文件: {file_path}")
    
    concepts = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            concepts.append(row)
    
    print(f"找到 {len(concepts)} 条概念数据")
    return concepts

def import_from_txt(file_path: str):
    """从TXT文件导入（每行一个概念，格式：概念名|定义|解释|法律领域）"""
    print(f"正在读取TXT文件: {file_path}")
    
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
                    'explanation': parts[2].strip() if len(parts) > 2 else '',
                    'law_type': parts[3].strip() if len(parts) > 3 else ''
                }
                concepts.append(concept)
    
    print(f"找到 {len(concepts)} 条概念数据")
    return concepts

def normalize_concept(concept: Dict, all_concept_names: List[str] = None) -> Optional[Dict]:
    """标准化概念数据"""
    # 提取字段（支持多种字段名）
    name = concept.get('name') or concept.get('concept') or concept.get('term') or concept.get('名称') or concept.get('概念名')
    if not name:
        return None
    
    definition = concept.get('definition') or concept.get('def') or concept.get('定义') or concept.get('description') or ''
    explanation = concept.get('explanation') or concept.get('detail') or concept.get('详细解释') or concept.get('说明') or definition
    law_type = concept.get('law_type') or concept.get('lawType') or concept.get('法律领域') or concept.get('领域') or ''
    related = concept.get('related_concepts') or concept.get('relatedConcepts') or concept.get('相关概念') or concept.get('related') or ''
    
    # 清理和验证
    name = clean_text(name, 100)
    if not name:
        return None
    
    definition = clean_text(definition, 2000)
    explanation = clean_text(explanation, 5000)
    
    # 自动检测法律领域
    if not law_type:
        law_type = detect_law_type(name + ' ' + definition + ' ' + explanation)
    
    # 提取相关概念
    if not related and all_concept_names:
        related = extract_related_concepts(explanation, all_concept_names)
    elif isinstance(related, list):
        related = ','.join(related[:10])
    else:
        related = clean_text(str(related), 1000)
    
    return {
        'name': name,
        'definition': definition,
        'explanation': explanation,
        'law_type': law_type,
        'related_concepts': related
    }

def import_concepts_to_db(concepts: List[Dict], batch_size: int = 100):
    """将概念导入数据库"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"\n开始导入 {len(concepts)} 条概念到数据库...")
        print("=" * 60)
        
        # 先获取所有现有概念名称（用于提取相关概念）
        cursor.execute("SELECT name FROM legal_concepts")
        existing_names = [row[0] for row in cursor.fetchall()]
        
        # 标准化所有概念
        normalized_concepts = []
        all_names = existing_names.copy()
        
        for i, concept in enumerate(concepts):
            normalized = normalize_concept(concept, all_names)
            if normalized:
                normalized_concepts.append(normalized)
                all_names.append(normalized['name'])
        
        print(f"标准化后有效概念: {len(normalized_concepts)} 条")
        
        # 批量插入
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
        
        for i, concept in enumerate(normalized_concepts):
            try:
                cursor.execute(sql, (
                    concept['name'],
                    concept['definition'],
                    concept['explanation'],
                    concept['law_type'],
                    concept['related_concepts']
                ))
                success_count += 1
                
                if (i + 1) % 50 == 0:
                    conn.commit()
                    print(f"  已导入 {i + 1}/{len(normalized_concepts)} 条...")
            except pymysql.err.IntegrityError:
                # 重复键，跳过
                skip_count += 1
            except Exception as e:
                error_count += 1
                print(f"  ✗ 导入失败: {concept['name'][:30]}... - {e}")
        
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

def download_disc_lawllm_sample():
    """创建示例数据（如果无法直接下载DISC-LawLLM）"""
    print("正在创建示例法律概念数据...")
    
    sample_concepts = [
        {
            "name": "合同",
            "definition": "当事人之间设立、变更、终止民事权利义务关系的协议",
            "explanation": "合同是民事法律行为的一种，是平等主体的自然人、法人、其他组织之间设立、变更、终止民事权利义务关系的协议。合同具有以下特征：1.合同是双方或多方的法律行为；2.合同是当事人意思表示一致的协议；3.合同以设立、变更、终止民事权利义务关系为目的。",
            "law_type": "民法",
            "related_concepts": "协议,民事行为,权利义务,要约,承诺"
        },
        {
            "name": "故意伤害罪",
            "definition": "故意非法损害他人身体健康的行为",
            "explanation": "故意伤害罪是指故意非法损害他人身体健康的行为。本罪的构成要件包括：1.客体要件：侵犯的是他人的身体健康权；2.客观要件：实施了非法损害他人身体健康的行为；3.主体要件：一般主体，年满14周岁具有刑事责任能力的自然人；4.主观要件：故意，包括直接故意和间接故意。",
            "law_type": "刑法",
            "related_concepts": "故意,伤害,犯罪,刑事责任,身体健康"
        },
        {
            "name": "劳动争议",
            "definition": "劳动关系当事人之间因劳动权利和劳动义务发生的争议",
            "explanation": "劳动争议是指劳动关系当事人之间因劳动权利和劳动义务发生的争议。主要包括：1.因确认劳动关系发生的争议；2.因订立、履行、变更、解除和终止劳动合同发生的争议；3.因除名、辞退和辞职、离职发生的争议；4.因工作时间、休息休假、社会保险、福利、培训以及劳动保护发生的争议；5.因劳动报酬、工伤医疗费、经济补偿或者赔偿金等发生的争议。",
            "law_type": "劳动法",
            "related_concepts": "劳动关系,劳动合同,劳动仲裁,用人单位,劳动者"
        },
        {
            "name": "行政行为",
            "definition": "行政主体依法行使行政职权，对行政相对人产生法律效果的行为",
            "explanation": "行政行为是指行政主体依法行使行政职权，对行政相对人产生法律效果的行为。行政行为具有以下特征：1.主体是行政主体；2.是行使行政职权的行为；3.是具有法律意义的行为；4.是对外产生法律效果的行为。行政行为包括行政许可、行政处罚、行政强制、行政征收等。",
            "law_type": "行政法",
            "related_concepts": "行政主体,行政职权,行政相对人,行政许可,行政处罚"
        },
        {
            "name": "知识产权",
            "definition": "权利人对其智力劳动所创作的成果和经营活动中的标记、信誉所依法享有的专有权利",
            "explanation": "知识产权是指权利人对其智力劳动所创作的成果和经营活动中的标记、信誉所依法享有的专有权利。主要包括：1.著作权（版权）；2.专利权；3.商标权；4.商业秘密；5.其他知识产权。知识产权具有专有性、地域性、时间性等特征。",
            "law_type": "知识产权法",
            "related_concepts": "著作权,专利权,商标权,商业秘密,智力成果"
        },
        {
            "name": "消费者权益",
            "definition": "消费者在购买、使用商品或接受服务时依法享有的权利",
            "explanation": "消费者权益是指消费者在购买、使用商品或接受服务时依法享有的权利。主要包括：1.安全保障权；2.知悉真情权；3.自主选择权；4.公平交易权；5.依法求偿权；6.依法结社权；7.获得知识权；8.受尊重权；9.监督批评权。",
            "law_type": "消费者权益保护法",
            "related_concepts": "消费者,经营者,商品,服务,安全保障"
        }
    ]
    
    return sample_concepts

def main():
    """主函数"""
    print("=" * 60)
    print("DISC-LawLLM 法律概念导入工具")
    print("=" * 60)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        
        if not os.path.exists(file_path):
            print(f"✗ 文件不存在: {file_path}")
            return
        
        # 根据文件扩展名选择导入方法
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.json':
            concepts = import_from_json(file_path)
        elif ext == '.csv':
            concepts = import_from_csv(file_path)
        elif ext == '.txt':
            concepts = import_from_txt(file_path)
        else:
            print(f"✗ 不支持的文件格式: {ext}")
            print("支持格式: .json, .csv, .txt")
            return
        
        # 导入数据库
        import_concepts_to_db(concepts)
        
    else:
        # 没有提供文件，使用示例数据
        print("\n未指定数据文件，使用示例数据...")
        print("使用方法: python import_disc_lawllm_concepts.py <数据文件路径>")
        print("\n支持格式:")
        print("  - JSON: [{'name': '...', 'definition': '...', ...}, ...]")
        print("  - CSV: name,definition,explanation,law_type,related_concepts")
        print("  - TXT: 概念名|定义|解释|法律领域")
        print("\n是否使用示例数据导入? (y/n): ", end='')
        
        # 直接使用示例数据
        concepts = download_disc_lawllm_sample()
        import_concepts_to_db(concepts)

if __name__ == '__main__':
    main()













