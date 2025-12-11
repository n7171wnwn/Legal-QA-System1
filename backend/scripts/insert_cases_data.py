#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插入案例示例数据
"""

import pymysql
import sys
from datetime import datetime, timedelta
import random

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'hjj060618',
    'database': 'legal_qa',
    'charset': 'utf8mb4'
}

# 案例数据
CASE_DATA = [
    # 劳动法案例
    {
        'title': '张某诉某公司加班费纠纷案',
        'case_type': '劳动争议',
        'content': '张某于2020年3月入职某公司，担任销售经理。工作期间，张某经常需要加班处理客户订单和业务报表。公司未按照法律规定支付加班费，张某多次与公司协商未果。2022年5月，张某向劳动争议仲裁委员会申请仲裁，要求公司支付2020年3月至2022年4月期间的加班费共计8万元。公司辩称张某的加班属于自愿行为，且已通过调休方式补偿。仲裁委员会经审理认为，张某的加班有考勤记录和邮件记录为证，公司应当支付加班费。最终裁决公司支付张某加班费6.5万元。',
        'court_name': '某市劳动争议仲裁委员会',
        'judge_date': datetime(2022, 8, 15),
        'dispute_point': '1. 张某的加班是否属于自愿行为；2. 公司是否应当支付加班费；3. 加班费的计算标准和金额。',
        'judgment_result': '仲裁委员会支持张某的请求，裁决公司支付加班费6.5万元。主要理由：1. 张某的加班有充分证据证明；2. 公司未按照《劳动法》规定支付加班费；3. 调休不能替代加班费的支付。',
        'law_type': '劳动法'
    },
    {
        'title': '李某诉某企业违法解除劳动合同案',
        'case_type': '劳动合同纠纷',
        'content': '李某在某企业工作5年，担任技术主管。2021年10月，企业以李某"严重违反公司规章制度"为由解除劳动合同。李某认为企业解除合同违法，向劳动争议仲裁委员会申请仲裁，要求企业支付违法解除劳动合同的赔偿金。企业辩称李某在工作期间多次迟到早退，且在工作时间处理私事，严重违反公司规定。经审理查明，李某确实存在迟到早退的情况，但次数不多，且企业未能提供充分证据证明李某的行为达到"严重违反"的程度。',
        'court_name': '某市劳动争议仲裁委员会',
        'judge_date': datetime(2022, 1, 20),
        'dispute_point': '1. 李某的行为是否构成严重违反公司规章制度；2. 企业解除劳动合同是否合法；3. 企业是否应当支付赔偿金。',
        'judgment_result': '仲裁委员会认定企业违法解除劳动合同，裁决企业支付李某赔偿金10万元（工作年限5年×月工资1万元×2倍）。',
        'law_type': '劳动法'
    },
    # 民法案例
    {
        'title': '王某诉赵某房屋买卖合同纠纷案',
        'case_type': '房屋买卖合同纠纷',
        'content': '2021年6月，王某与赵某签订房屋买卖合同，约定王某以200万元购买赵某名下的一套房产。合同签订后，王某支付了首付款60万元。但在办理过户手续时，发现该房屋已被法院查封，无法办理过户。王某要求解除合同并返还首付款，赵某拒绝。王某遂向法院提起诉讼。经查，该房屋因赵某的其他债务纠纷被法院查封。',
        'court_name': '某市中级人民法院',
        'judge_date': datetime(2022, 3, 10),
        'dispute_point': '1. 房屋被查封是否构成根本违约；2. 合同是否应当解除；3. 赵某是否应当返还首付款并承担违约责任。',
        'judgment_result': '法院判决解除合同，赵某返还王某首付款60万元，并支付违约金20万元。法院认为，房屋被查封导致无法过户，构成根本违约，王某有权解除合同并要求赔偿。',
        'law_type': '民法'
    },
    {
        'title': '刘某诉某汽车销售公司买卖合同纠纷案',
        'case_type': '买卖合同纠纷',
        'content': '2021年8月，刘某在某汽车销售公司购买了一辆新车，价格为25万元。提车后不久，刘某发现车辆存在多处质量问题，包括发动机异响、刹车系统故障等。刘某多次要求公司维修或更换车辆，但公司只同意维修，拒绝更换。刘某遂向法院起诉，要求解除合同并退还购车款。',
        'court_name': '某区人民法院',
        'judge_date': datetime(2022, 5, 18),
        'dispute_point': '1. 车辆质量问题是否达到解除合同的程度；2. 公司是否应当承担违约责任；3. 刘某是否有权要求解除合同。',
        'judgment_result': '法院认定车辆存在严重质量问题，影响安全使用，判决解除合同，公司退还购车款25万元，并赔偿刘某损失3万元。',
        'law_type': '民法'
    },
    # 刑法案例
    {
        'title': '张某故意伤害案',
        'case_type': '故意伤害罪',
        'content': '2021年9月，张某与李某因停车位问题发生争执。争执过程中，张某用拳头击打李某面部，导致李某鼻骨骨折，经鉴定为轻伤二级。案发后，张某主动投案，如实供述犯罪事实，并积极赔偿李某医疗费等损失共计5万元，取得李某谅解。',
        'court_name': '某区人民法院',
        'judge_date': datetime(2022, 2, 25),
        'dispute_point': '1. 张某的行为是否构成故意伤害罪；2. 张某的投案自首和赔偿行为是否可以从轻处罚；3. 量刑标准。',
        'judgment_result': '法院认定张某构成故意伤害罪，鉴于其有自首情节，积极赔偿并取得谅解，判处有期徒刑六个月，缓刑一年。',
        'law_type': '刑法'
    },
    {
        'title': '李某诈骗案',
        'case_type': '诈骗罪',
        'content': '2020年3月至2021年8月，李某虚构投资项目，以高额回报为诱饵，先后骗取20余名被害人共计300余万元。李某将骗取的款项用于个人消费和偿还债务。案发后，李某被公安机关抓获，如实供述犯罪事实，但已无力退赔大部分款项。',
        'court_name': '某市中级人民法院',
        'judge_date': datetime(2022, 6, 30),
        'dispute_point': '1. 李某的行为是否构成诈骗罪；2. 诈骗金额的认定；3. 量刑标准。',
        'judgment_result': '法院认定李某构成诈骗罪，诈骗数额特别巨大，判处有期徒刑十二年，并处罚金50万元，责令退赔被害人经济损失。',
        'law_type': '刑法'
    },
    # 合同法案例
    {
        'title': '某建筑公司诉某材料供应商合同纠纷案',
        'case_type': '建设工程合同纠纷',
        'content': '2021年4月，某建筑公司与某材料供应商签订材料供应合同，约定供应商向建筑公司提供钢材500吨，总价款250万元。合同约定供应商应在2021年6月30日前交付全部材料。但供应商因自身原因，仅交付了300吨材料，剩余200吨未能按时交付，导致建筑公司工程进度延误，造成经济损失50万元。建筑公司遂向法院起诉，要求供应商承担违约责任。',
        'court_name': '某市中级人民法院',
        'judge_date': datetime(2022, 4, 12),
        'dispute_point': '1. 供应商是否构成违约；2. 建筑公司的损失如何认定；3. 违约责任如何承担。',
        'judgment_result': '法院认定供应商构成违约，判决供应商支付违约金25万元，并赔偿建筑公司经济损失30万元，共计55万元。',
        'law_type': '民法'
    },
    {
        'title': '某科技公司诉某软件公司技术服务合同纠纷案',
        'case_type': '技术服务合同纠纷',
        'content': '2021年1月，某科技公司与某软件公司签订技术服务合同，约定软件公司为科技公司开发一套管理系统，合同价款80万元。合同约定系统应在2021年6月30日前完成开发并交付使用。但软件公司开发的系统存在多处功能缺陷，无法正常使用。科技公司多次要求软件公司修复，但软件公司未能解决。科技公司遂向法院起诉，要求解除合同并返还已支付的款项。',
        'court_name': '某区人民法院',
        'judge_date': datetime(2022, 3, 28),
        'dispute_point': '1. 软件公司是否构成根本违约；2. 合同是否应当解除；3. 已支付款项是否应当返还。',
        'judgment_result': '法院认定软件公司构成根本违约，判决解除合同，软件公司返还科技公司已支付的款项60万元，并支付违约金16万元。',
        'law_type': '民法'
    },
    # 侵权责任案例
    {
        'title': '王某诉某商场人身损害赔偿案',
        'case_type': '人身损害赔偿纠纷',
        'content': '2021年7月，王某在某商场购物时，因商场地面湿滑未设置警示标志，不慎摔倒，导致右腿骨折。王某住院治疗20天，花费医疗费3万元，后续还需康复治疗。王某要求商场赔偿医疗费、误工费、护理费等共计8万元。商场辩称王某自身未尽注意义务，应承担部分责任。',
        'court_name': '某区人民法院',
        'judge_date': datetime(2022, 2, 15),
        'dispute_point': '1. 商场是否尽到安全保障义务；2. 王某是否应当承担部分责任；3. 赔偿金额如何认定。',
        'judgment_result': '法院认定商场未尽到安全保障义务，应承担主要责任，判决商场赔偿王某各项损失共计6.5万元。王某未尽到合理注意义务，承担次要责任。',
        'law_type': '民法'
    },
    {
        'title': '李某诉某网络公司名誉权纠纷案',
        'case_type': '名誉权纠纷',
        'content': '2021年5月，某网络公司在未经李某同意的情况下，在其运营的网站上发布了一篇关于李某的负面文章，文章内容不实，对李某的名誉造成损害。李某发现后，要求网络公司删除文章并公开道歉，但网络公司拒绝。李某遂向法院起诉，要求网络公司停止侵害、删除文章、公开道歉并赔偿精神损害抚慰金。',
        'court_name': '某区人民法院',
        'judge_date': datetime(2022, 1, 10),
        'dispute_point': '1. 网络公司是否构成名誉侵权；2. 李某是否有权要求精神损害赔偿；3. 赔偿金额如何确定。',
        'judgment_result': '法院认定网络公司构成名誉侵权，判决网络公司立即删除相关文章，在网站首页公开道歉，并赔偿李某精神损害抚慰金2万元。',
        'law_type': '民法'
    },
    # 婚姻家庭案例
    {
        'title': '张某诉李某离婚纠纷案',
        'case_type': '离婚纠纷',
        'content': '张某与李某于2015年结婚，婚后育有一子。2020年起，双方因性格不合经常发生争吵，感情破裂。2021年8月，张某向法院提起离婚诉讼。双方对离婚无异议，但在子女抚养和财产分割问题上存在争议。张某要求获得子女抚养权，并要求分割夫妻共同财产。李某也要求获得子女抚养权，并认为部分财产属于其个人财产。',
        'court_name': '某区人民法院',
        'judge_date': datetime(2022, 3, 5),
        'dispute_point': '1. 子女抚养权的归属；2. 夫妻共同财产的认定和分割；3. 抚养费的支付标准。',
        'judgment_result': '法院判决准予离婚，子女由张某抚养，李某每月支付抚养费2000元。夫妻共同财产按双方贡献和实际情况进行分割，张某获得60%，李某获得40%。',
        'law_type': '民法'
    },
    {
        'title': '王某诉赵某继承纠纷案',
        'case_type': '继承纠纷',
        'content': '王某的父亲于2021年去世，留下房产一套、存款50万元。王某的父亲生前立有遗嘱，将房产留给王某，存款留给王某的弟弟。但王某的继母认为遗嘱无效，要求按照法定继承分割遗产。王某遂向法院起诉，要求确认遗嘱效力并按照遗嘱继承。',
        'court_name': '某区人民法院',
        'judge_date': datetime(2022, 4, 20),
        'dispute_point': '1. 遗嘱是否有效；2. 继母是否有继承权；3. 遗产如何分割。',
        'judgment_result': '法院认定遗嘱有效，判决按照遗嘱执行，房产归王某所有，存款归王某的弟弟所有。继母作为法定继承人，有权继承王某父亲的其他遗产（如有）。',
        'law_type': '民法'
    }
]

def insert_cases_data():
    """插入案例数据"""
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print(f"✓ 成功连接到数据库: {DB_CONFIG['database']}")
        
        # 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM legal_cases")
        existing_count = cursor.fetchone()[0]
        print(f"当前案例库已有 {existing_count} 条数据")
        
        # 插入数据
        insert_sql = """
        INSERT INTO legal_cases (title, case_type, content, court_name, judge_date, dispute_point, judgment_result, law_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        inserted_count = 0
        for data in CASE_DATA:
            try:
                cursor.execute(insert_sql, (
                    data['title'],
                    data['case_type'],
                    data['content'],
                    data['court_name'],
                    data['judge_date'],
                    data['dispute_point'],
                    data['judgment_result'],
                    data['law_type']
                ))
                inserted_count += 1
            except pymysql.IntegrityError as e:
                print(f"⚠ 跳过重复数据: {data['title'][:30]}...")
            except Exception as e:
                print(f"✗ 插入失败: {data['title'][:30]}... 错误: {e}")
        
        # 提交事务
        connection.commit()
        print(f"✓ 成功插入 {inserted_count} 条案例数据")
        
        # 查询最终数量
        cursor.execute("SELECT COUNT(*) FROM legal_cases")
        final_count = cursor.fetchone()[0]
        print(f"✓ 案例库现在共有 {final_count} 条数据")
        
        # 按法律领域统计
        cursor.execute("SELECT law_type, COUNT(*) as count FROM legal_cases GROUP BY law_type")
        print("\n按法律领域统计:")
        print("法律领域 | 数量")
        print("-" * 30)
        for row in cursor.fetchall():
            print(f"{row[0]:<10} | {row[1]}")
        
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
    print("开始插入案例示例数据...")
    success = insert_cases_data()
    if success:
        print("\n✓ 数据插入完成！")
        sys.exit(0)
    else:
        print("\n✗ 数据插入失败！")
        sys.exit(1)













