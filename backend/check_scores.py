import sqlite3
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routers.diagnosis import get_score_assessment

# 测试分数评估函数
print("测试分数评估函数:")
test_scores = [8.57, 0.857, 95.5, 0.955, 150.0, 1.5, 45.2, 0.452]

for score in test_scores:
    level, description = get_score_assessment(score)
    print(f"分数: {score} -> 等级: {level}, 描述: {description}")

print("\n" + "="*50)

# 连接数据库查看表结构
try:
    conn = sqlite3.connect('easysight.db')
    cursor = conn.cursor()
    
    # 查看所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print('\n数据库中的表:')
    for table in tables:
        print(f'  {table[0]}')
    
    # 查找诊断结果相关的表
    for table in tables:
        table_name = table[0]
        if 'diagnosis' in table_name.lower() or 'result' in table_name.lower():
            print(f'\n表: {table_name}')
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f'  {col[1]} ({col[2]})')
            
            # 如果有score字段，查看数据
            column_names = [col[1] for col in columns]
            if 'score' in column_names:
                print(f'\n{table_name}表中的分数数据:')
                try:
                    cursor.execute(f"SELECT score, threshold FROM {table_name} ORDER BY score DESC LIMIT 10")
                    results = cursor.fetchall()
                    if results:
                        for r in results:
                            print(f'  分数: {r[0]}, 阈值: {r[1]}')
                    else:
                        print('  没有数据')
                except Exception as e:
                    print(f'  查询错误: {e}')
    
    conn.close()
except Exception as e:
    print(f'数据库连接错误: {e}')