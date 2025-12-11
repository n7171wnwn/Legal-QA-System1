#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Laws 仓库导入案例数据到 MySQL 数据库的 legal_cases 表
"""

import os
import re
import sys
import pymysql
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse

# 数据库配置
DEFAULT_DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

# 案例类型映射（从子文件夹名称映射到数据库中的law_type）
CASE_TYPE_MAPPING = {
    '劳动人事': '劳动法',
    '民法典': '民法',
    '消费购物': '消费者权益保护法',
    '行政协议诉讼': '行政法',
    '其他': '其他'
}


class CaseDataImporter:
    def __init__(self, db_config: Dict, laws_repo_path: str):
        """
        初始化导入器
        
        Args:
            db_config: 数据库配置
            laws_repo_path: Laws 仓库路径
        """
        self.db_config = db_config
        self.laws_repo_path = Path(laws_repo_path)
        self.connection = None
        self.stats = {
            'total_files': 0,
            'imported_cases': 0,
            'skipped_cases': 0,
            'errors': []
        }

    def connect_db(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(**self.db_config)
            print(f"✓ 成功连接到数据库: {self.db_config['database']}")
        except Exception as e:
            print(f"✗ 数据库连接失败: {e}")
            sys.exit(1)

    def close_db(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("✓ 数据库连接已关闭")

    def parse_case_file(self, file_path: Path) -> Optional[Dict]:
        """
        解析案例markdown文件，提取案例信息
        
        Args:
            file_path: markdown文件路径
            
        Returns:
            案例信息字典，包含 title, case_type, content, court_name, judge_date, 
            dispute_point, judgment_result, law_type 等字段
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.stats['errors'].append(f"读取文件失败 {file_path}: {e}")
            return None

        if not content.strip():
            return None

        # 提取标题（从文件第一行或文件名）
        title = file_path.stem
        title_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        # 提取案由（从标题或内容中提取）
        case_type = None
        # 尝试从标题中提取案由关键词
        case_type_keywords = ['纠纷', '争议', '案', '合同', '侵权', '赔偿', '劳动争议', '劳动纠纷']
        for keyword in case_type_keywords:
            if keyword in title:
                # 尝试提取更具体的案由
                match = re.search(r'(.+?' + re.escape(keyword) + ')', title)
                if match:
                    case_type = match.group(1)
                    break
        # 如果没找到，尝试从内容中提取
        if not case_type:
            case_type_match = re.search(r'案由[：:]\s*(.+?)(?:\n|$)', content)
            if case_type_match:
                case_type = case_type_match.group(1).strip()

        # 提取审理法院
        court_name = None
        court_patterns = [
            r'审理法院[：:]\s*(.+?)(?:\n|$)',
            r'法院[：:]\s*(.+?)(?:\n|$)',
            r'诉至(.+?法院)',
            r'(.+?人民法院)',
            r'(.+?仲裁委员会)',
        ]
        for pattern in court_patterns:
            match = re.search(pattern, content)
            if match:
                court_name = match.group(1).strip()
                # 清理可能的额外内容
                if '诉至' in court_name:
                    court_name = court_name.replace('诉至', '').strip()
                if len(court_name) < 100:  # 避免匹配到太长的内容
                    break

        # 提取判决日期
        judge_date = None
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
        dispute_point = None
        dispute_patterns = [
            r'争议焦点[：:]\s*(.+?)(?:\n\n|##|$)',
            r'核心争议[：:]\s*(.+?)(?:\n\n|##|$)',
            r'争议点[：:]\s*(.+?)(?:\n\n|##|$)',
            r'本案争议焦点[是：:]\s*(.+?)(?:\n\n|##|$)',
        ]
        for pattern in dispute_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                dispute_point = match.group(1).strip()
                # 清理markdown格式
                dispute_point = re.sub(r'[*_`]', '', dispute_point)
                dispute_point = dispute_point[:2000]  # 限制长度
                break

        # 提取判决结果
        judgment_result = None
        result_patterns = [
            r'裁判结果[：:]\s*(.+?)(?:\n\n|##|$)',
            r'判决结果[：:]\s*(.+?)(?:\n\n|##|$)',
            r'一审法院判决[：:]\s*(.+?)(?:\n\n|##|$)',
            r'法院判决[：:]\s*(.+?)(?:\n\n|##|$)',
        ]
        for pattern in result_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                judgment_result = match.group(1).strip()
                # 清理markdown格式
                judgment_result = re.sub(r'[*_`]', '', judgment_result)
                judgment_result = judgment_result[:2000]  # 限制长度
                break

        # 获取法律领域（从文件路径推断）
        law_type = self.get_law_type_from_path(file_path)

        # 完整的案例内容（清理markdown注释）
        full_content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        full_content = full_content.strip()

        return {
            'title': title,
            'case_type': case_type,
            'content': full_content[:5000] if len(full_content) > 5000 else full_content,  # 限制长度
            'court_name': court_name,
            'judge_date': judge_date,
            'dispute_point': dispute_point,
            'judgment_result': judgment_result,
            'law_type': law_type
        }

    def get_law_type_from_path(self, file_path: Path) -> Optional[str]:
        """
        从文件路径推断法律类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            法律类型
        """
        try:
            # 获取文件相对于案例目录的路径
            case_dir = self.laws_repo_path / '案例'
            relative_path = file_path.relative_to(case_dir)
            # 获取第一级子目录名（如：劳动人事、民法典等）
            if len(relative_path.parts) > 1:
                sub_dir = relative_path.parts[0]
                if sub_dir in CASE_TYPE_MAPPING:
                    return CASE_TYPE_MAPPING[sub_dir]
        except:
            pass
        
        return '其他'

    def import_case(self, case_data: Dict) -> bool:
        """
        导入单个案例到数据库
        
        Args:
            case_data: 案例数据
            
        Returns:
            是否成功
        """
        try:
            cursor = self.connection.cursor()
            
            # 检查是否已存在（根据title）
            check_sql = """
                SELECT id FROM legal_cases 
                WHERE title = %s
            """
            cursor.execute(check_sql, (case_data['title'],))
            existing = cursor.fetchone()
            
            if existing:
                self.stats['skipped_cases'] += 1
                return False
            
            # 插入新记录
            insert_sql = """
                INSERT INTO legal_cases 
                (title, case_type, content, court_name, judge_date, 
                 dispute_point, judgment_result, law_type, create_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            cursor.execute(insert_sql, (
                case_data['title'],
                case_data['case_type'],
                case_data['content'],
                case_data['court_name'],
                case_data['judge_date'],
                case_data['dispute_point'],
                case_data['judgment_result'],
                case_data['law_type']
            ))
            
            self.connection.commit()
            self.stats['imported_cases'] += 1
            return True
            
        except Exception as e:
            self.connection.rollback()
            error_msg = f"导入案例失败 {case_data.get('title', 'Unknown')}: {e}"
            self.stats['errors'].append(error_msg)
            print(f"  ✗ {error_msg}")
            return False

    def import_cases_directory(self, directory: Path):
        """
        导入目录下的所有案例文件
        
        Args:
            directory: 案例目录路径
        """
        if not directory.exists():
            print(f"✗ 目录不存在: {directory}")
            return
        
        print(f"\n处理案例目录: {directory.name}")
        
        # 查找所有markdown文件（排除_index.md）
        md_files = [f for f in directory.rglob('*.md') 
                   if f.name != '_index.md' and '案例' in str(f)]
        self.stats['total_files'] += len(md_files)
        
        for md_file in md_files:
            print(f"  处理文件: {md_file.name}")
            case_data = self.parse_case_file(md_file)
            
            if case_data:
                if self.import_case(case_data):
                    print(f"    ✓ 导入成功: {case_data['title']}")
            else:
                print(f"    ✗ 解析失败")

    def import_all(self):
        """导入所有案例数据"""
        case_dir = self.laws_repo_path / '案例'
        
        if not case_dir.exists():
            print(f"✗ 案例目录不存在: {case_dir}")
            return
        
        print(f"开始导入案例数据从: {case_dir}")
        
        # 遍历案例子目录
        for sub_dir in case_dir.iterdir():
            if sub_dir.is_dir() and not sub_dir.name.startswith('.'):
                self.import_cases_directory(sub_dir)
        
        # 打印统计信息
        print("\n" + "="*50)
        print("导入完成！统计信息：")
        print(f"  总文件数: {self.stats['total_files']}")
        print(f"  成功导入: {self.stats['imported_cases']} 条案例")
        print(f"  跳过记录: {self.stats['skipped_cases']} 条（已存在）")
        print(f"  错误数量: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\n错误列表（前10个）：")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")


def main():
    parser = argparse.ArgumentParser(description='从 Laws 仓库导入案例数据到 MySQL 数据库')
    parser.add_argument('--repo-path', type=str, required=True,
                       help='Laws 仓库路径')
    parser.add_argument('--host', type=str, default=DEFAULT_DB_CONFIG['host'],
                       help='数据库主机')
    parser.add_argument('--port', type=int, default=DEFAULT_DB_CONFIG['port'],
                       help='数据库端口')
    parser.add_argument('--user', type=str, default=DEFAULT_DB_CONFIG['user'],
                       help='数据库用户名')
    parser.add_argument('--password', type=str, default=DEFAULT_DB_CONFIG['password'],
                       help='数据库密码')
    parser.add_argument('--database', type=str, default=DEFAULT_DB_CONFIG['database'],
                       help='数据库名称')
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.host,
        'port': args.port,
        'user': args.user,
        'password': args.password,
        'database': args.database,
        'charset': 'utf8mb4'
    }
    
    importer = CaseDataImporter(db_config, args.repo_path)
    
    try:
        importer.connect_db()
        importer.import_all()
    finally:
        importer.close_db()


if __name__ == '__main__':
    main()

