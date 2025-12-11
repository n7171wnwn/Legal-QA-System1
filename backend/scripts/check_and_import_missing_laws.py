#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中已有的法律，并从指定文件夹导入未导入的法律
"""

import os
import re
import sys
import pymysql
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
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

# 法律类型映射
LAW_TYPE_MAPPING = {
    '刑法': '刑法',
    '民法典': '民法',
    '民法商法': '民法',
    '宪法': '宪法',
    '宪法相关法': '宪法相关法',
    '行政法': '行政法',
    '行政法规': '行政法规',
    '经济法': '经济法',
    '社会法': '社会法',
    '诉讼与非诉讼程序法': '程序法',
    '部门规章': '部门规章',
    '司法解释': '司法解释',
    '案例': '案例',
    '其他': '其他'
}


class LawCheckerAndImporter:
    def __init__(self, db_config: Dict, laws_repo_path: str):
        self.db_config = db_config
        self.laws_repo_path = Path(laws_repo_path)
        self.connection = None
        self.stats = {
            'total_files': 0,
            'imported_articles': 0,
            'skipped_articles': 0,
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

    def get_existing_laws(self) -> Set[str]:
        """获取数据库中已有的法律名称"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT DISTINCT title FROM legal_articles WHERE is_valid = true")
            results = cursor.fetchall()
            existing_laws = {row[0] for row in results}
            print(f"✓ 数据库中已有 {len(existing_laws)} 部法律")
            return existing_laws
        except Exception as e:
            print(f"✗ 查询数据库失败: {e}")
            return set()

    def get_law_title_from_file(self, file_path: Path) -> Optional[str]:
        """从文件中提取法律名称"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试从文件内容中提取法律名称（通常在文件开头）
            title_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
            if title_match:
                return title_match.group(1).strip()
            
            # 如果没有找到，使用文件名（去掉扩展名）
            return file_path.stem
        except Exception as e:
            print(f"  警告：读取文件失败 {file_path}: {e}")
            return None

    def scan_law_files(self) -> Dict[str, Path]:
        """扫描文件夹中的所有法律文件，返回 {法律名称: 文件路径} 的字典"""
        law_files = {}
        
        if not self.laws_repo_path.exists():
            print(f"✗ 文件夹不存在: {self.laws_repo_path}")
            return law_files
        
        print(f"\n扫描文件夹: {self.laws_repo_path}")
        
        # 查找所有markdown文件
        md_files = list(self.laws_repo_path.rglob('*.md'))
        print(f"找到 {len(md_files)} 个markdown文件")
        
        for md_file in md_files:
            # 跳过一些不需要的文件
            if any(skip in md_file.name for skip in ['README', 'readme', '.git']):
                continue
            
            law_title = self.get_law_title_from_file(md_file)
            if law_title:
                # 如果同一个法律名称有多个文件，保留第一个
                if law_title not in law_files:
                    law_files[law_title] = md_file
                else:
                    print(f"  注意：发现重复的法律名称 '{law_title}'，跳过: {md_file}")
        
        print(f"✓ 提取了 {len(law_files)} 部法律")
        return law_files

    def parse_markdown_file(self, file_path: Path) -> List[Dict]:
        """解析markdown文件，提取法条信息"""
        articles = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.stats['errors'].append(f"读取文件失败 {file_path}: {e}")
            return articles

        # 获取文件名作为法律名称
        law_title = file_path.stem
        
        # 尝试从文件内容中提取法律名称
        title_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        if title_match:
            law_title = title_match.group(1).strip()
        
        # 提取发布机构和日期
        publish_org = None
        publish_date = None
        
        org_patterns = [
            r'发布[机关|机构][：:]\s*(.+?)(?:\n|$)',
            r'制定[机关|机构][：:]\s*(.+?)(?:\n|$)',
            r'颁布[机关|机构][：:]\s*(.+?)(?:\n|$)',
        ]
        for pattern in org_patterns:
            org_match = re.search(pattern, content)
            if org_match:
                publish_org = org_match.group(1).strip()
                break
        
        date_patterns = [
            r'发布[日期|时间][：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?)',
            r'颁布[日期|时间][：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?)',
            r'施行[日期|时间][：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?)',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, content)
            if date_match:
                if len(date_match.groups()) == 3:
                    year, month, day = date_match.groups()
                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    date_str = date_match.group(1).replace('年', '-').replace('月', '-').replace('日', '')
                
                date_str = re.sub(r'[年月日]', '-', date_str).strip('-')
                parts = date_str.split('-')
                if len(parts) >= 3:
                    date_str = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                elif len(parts) == 2:
                    date_str = f"{parts[0]}-{parts[1].zfill(2)}-01"
                
                try:
                    publish_date = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    try:
                        publish_date = datetime.strptime(date_str, '%Y-%m')
                    except:
                        pass
                if publish_date:
                    break

        # 解析法条内容
        article_markers = []
        
        # 匹配中文数字格式
        for match in re.finditer(r'^第([一二三四五六七八九十百千万\d]+)([条章节款项])', content, re.MULTILINE):
            article_markers.append({
                'pos': match.start(),
                'number': match.group(1),
                'type': match.group(2),
                'full': match.group(0)
            })
        
        # 如果没找到中文数字，尝试阿拉伯数字格式
        if not article_markers:
            for match in re.finditer(r'^第(\d+)([条章节款项])', content, re.MULTILINE):
                article_markers.append({
                    'pos': match.start(),
                    'number': match.group(1),
                    'type': match.group(2),
                    'full': match.group(0)
                })
        
        # 根据条号位置分割内容
        if article_markers:
            article_markers.sort(key=lambda x: x['pos'])
            
            for i, marker in enumerate(article_markers):
                article_number = f"第{marker['number']}{marker['type']}"
                
                start_pos = marker['pos'] + len(marker['full'])
                end_pos = article_markers[i + 1]['pos'] if i + 1 < len(article_markers) else len(content)
                
                article_content = content[start_pos:end_pos].strip()
                article_content = re.sub(r'^\s*\n+', '', article_content)
                article_content = re.sub(r'\n+$', '', article_content)
                
                if article_content and len(article_content) > 10:
                    articles.append({
                        'title': law_title,
                        'article_number': article_number,
                        'content': article_content[:5000],
                        'publish_org': publish_org,
                        'publish_date': publish_date
                    })
        
        # 如果仍然没有找到，将整个文件内容作为一条记录
        if not articles and content.strip():
            clean_content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
            clean_content = clean_content.strip()
            
            if len(clean_content) > 50:
                articles.append({
                    'title': law_title,
                    'article_number': None,
                    'content': clean_content[:5000],
                    'publish_org': publish_org,
                    'publish_date': publish_date
                })

        return articles

    def get_law_type_from_path(self, file_path: Path) -> Optional[str]:
        """从文件路径推断法律类型"""
        try:
            relative_path = file_path.relative_to(self.laws_repo_path)
            first_dir = relative_path.parts[0] if relative_path.parts else None
            
            if first_dir and first_dir in LAW_TYPE_MAPPING:
                return LAW_TYPE_MAPPING[first_dir]
        except:
            pass
        
        return None

    def import_article(self, article: Dict, law_type: Optional[str]) -> bool:
        """导入单条法条到数据库"""
        try:
            cursor = self.connection.cursor()
            
            # 检查是否已存在
            check_sql = """
                SELECT id FROM legal_articles 
                WHERE title = %s AND (article_number = %s OR (%s IS NULL AND article_number IS NULL))
            """
            cursor.execute(check_sql, (article['title'], article['article_number'], article['article_number']))
            existing = cursor.fetchone()
            
            if existing:
                self.stats['skipped_articles'] += 1
                return False
            
            # 插入新记录
            insert_sql = """
                INSERT INTO legal_articles 
                (title, article_number, content, law_type, publish_org, publish_date, is_valid, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            
            cursor.execute(insert_sql, (
                article['title'],
                article['article_number'],
                article['content'],
                law_type,
                article['publish_org'],
                article['publish_date'],
                True
            ))
            
            self.connection.commit()
            self.stats['imported_articles'] += 1
            return True
            
        except Exception as e:
            self.connection.rollback()
            error_msg = f"导入法条失败 {article.get('title', 'Unknown')}: {e}"
            self.stats['errors'].append(error_msg)
            print(f"  ✗ {error_msg}")
            return False

    def import_law_file(self, file_path: Path):
        """导入单个法律文件"""
        print(f"\n处理文件: {file_path.name}")
        articles = self.parse_markdown_file(file_path)
        
        if not articles:
            print(f"  ⚠ 未找到法条，跳过")
            return
        
        law_type = self.get_law_type_from_path(file_path)
        imported_count = 0
        
        for article in articles:
            if self.import_article(article, law_type):
                imported_count += 1
        
        print(f"  ✓ 成功导入 {imported_count} 条法条，跳过 {len(articles) - imported_count} 条（已存在）")

    def check_and_import(self):
        """检查并导入未导入的法律"""
        import sys
        sys.stdout.flush()
        print("="*70)
        print("开始检查数据库和导入未导入的法律")
        print("="*70)
        sys.stdout.flush()
        
        # 1. 获取数据库中已有的法律
        existing_laws = self.get_existing_laws()
        
        # 2. 扫描文件夹中的法律文件
        law_files = self.scan_law_files()
        
        # 3. 找出未导入的法律
        missing_laws = {}
        for law_title, file_path in law_files.items():
            if law_title not in existing_laws:
                missing_laws[law_title] = file_path
        
        print("\n" + "="*70)
        print(f"检查结果：")
        print(f"  数据库中已有: {len(existing_laws)} 部法律")
        print(f"  文件夹中找到: {len(law_files)} 部法律")
        print(f"  未导入的法律: {len(missing_laws)} 部")
        print("="*70)
        
        if missing_laws:
            print("\n未导入的法律列表：")
            for i, (law_title, file_path) in enumerate(missing_laws.items(), 1):
                print(f"  {i}. {law_title} ({file_path.name})")
            
            # 自动导入
            print(f"\n开始自动导入这 {len(missing_laws)} 部法律...")
            self.stats['total_files'] = len(missing_laws)
            
            for law_title, file_path in missing_laws.items():
                self.import_law_file(file_path)
            
            # 打印统计信息
            print("\n" + "="*70)
            print("导入完成！统计信息：")
            print(f"  处理文件数: {self.stats['total_files']}")
            print(f"  成功导入: {self.stats['imported_articles']} 条法条")
            print(f"  跳过记录: {self.stats['skipped_articles']} 条（已存在）")
            print(f"  错误数量: {len(self.stats['errors'])}")
            
            if self.stats['errors']:
                print("\n错误列表：")
                for error in self.stats['errors'][:10]:
                    print(f"  - {error}")
        else:
            print("\n✓ 所有法律都已导入，无需导入新数据")


def main():
    parser = argparse.ArgumentParser(description='检查数据库并导入未导入的法律')
    parser.add_argument('--repo-path', type=str, default=r'E:\Laws\Laws',
                       help='法律文件文件夹路径（默认: E:\\Laws\\Laws）')
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
    
    importer = LawCheckerAndImporter(db_config, args.repo_path)
    
    try:
        importer.connect_db()
        importer.check_and_import()
    finally:
        importer.close_db()


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    try:
        main()
    except Exception as e:
        import traceback
        print(f"错误: {e}")
        traceback.print_exc()
        sys.exit(1)
