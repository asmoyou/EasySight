#!/usr/bin/env python3
"""
更新诊断模块数据库模型
修复字段名不匹配问题
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from database import async_engine

async def update_diagnosis_models():
    """更新诊断模块数据库模型"""
    engine = async_engine
    
    async with engine.begin() as conn:
        print("开始更新诊断模块数据库模型...")
        
        # 删除现有的诊断相关表（如果存在）
        await conn.execute(text("DROP TABLE IF EXISTS diagnosis_statistics"))
        await conn.execute(text("DROP TABLE IF EXISTS diagnosis_alarms"))
        await conn.execute(text("DROP TABLE IF EXISTS diagnosis_results"))
        await conn.execute(text("DROP TABLE IF EXISTS diagnosis_templates"))
        await conn.execute(text("DROP TABLE IF EXISTS diagnosis_tasks"))
        
        print("已删除旧的诊断表")
        
        # 创建新的诊断任务表
        await conn.execute(text("""
            CREATE TABLE diagnosis_tasks (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                camera_ids JSON DEFAULT '[]',
                camera_groups JSON DEFAULT '[]',
                diagnosis_types JSON DEFAULT '[]',
                diagnosis_config JSON DEFAULT '{}',
                schedule_type VARCHAR(50),
                schedule_config JSON DEFAULT '{}',
                cron_expression VARCHAR(100),
                interval_minutes INTEGER,
                threshold_config JSON DEFAULT '{}',
                status VARCHAR(20) DEFAULT 'pending',
                is_active BOOLEAN DEFAULT TRUE,
                last_run_time TIMESTAMP,
                next_run_time TIMESTAMP,
                total_runs INTEGER DEFAULT 0,
                success_runs INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(50)
            )
        """))
        
        # 创建新的诊断结果表
        await conn.execute(text("""
            CREATE TABLE diagnosis_results (
                id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL,
                camera_id INTEGER,
                camera_name VARCHAR(100),
                diagnosis_type VARCHAR(50),
                diagnosis_status VARCHAR(20) NOT NULL,
                score REAL,
                threshold REAL,
                is_abnormal BOOLEAN DEFAULT FALSE,
                image_url VARCHAR(500),
                thumbnail_url VARCHAR(500),
                image_timestamp TIMESTAMP,
                processing_time REAL,
                error_message TEXT,
                suggestions JSON DEFAULT '[]',
                metrics JSON DEFAULT '{}',
                result_data JSON DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建新的诊断告警表
        await conn.execute(text("""
            CREATE TABLE diagnosis_alarms (
                id SERIAL PRIMARY KEY,
                result_id INTEGER NOT NULL,
                alarm_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) DEFAULT 'warning',
                title VARCHAR(200) NOT NULL,
                description TEXT,
                threshold_config JSON DEFAULT '{}',
                current_value REAL,
                threshold_value REAL,
                is_acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by INTEGER,
                acknowledged_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建新的诊断模板表
        await conn.execute(text("""
            CREATE TABLE diagnosis_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                diagnosis_types JSON DEFAULT '[]',
                default_config JSON DEFAULT '{}',
                default_schedule JSON DEFAULT '{}',
                threshold_config JSON DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                is_system BOOLEAN DEFAULT FALSE,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(50)
            )
        """))
        
        # 创建诊断统计表
        await conn.execute(text("""
            CREATE TABLE diagnosis_statistics (
                id SERIAL PRIMARY KEY,
                date TIMESTAMP NOT NULL,
                camera_id INTEGER,
                diagnosis_type VARCHAR(50),
                total_checks INTEGER DEFAULT 0,
                normal_count INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                critical_count INTEGER DEFAULT 0,
                avg_score REAL,
                min_score REAL,
                max_score REAL,
                avg_processing_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        print("已创建新的诊断表")
        
        # 插入一些示例模板
        await conn.execute(text("""
            INSERT INTO diagnosis_templates (name, description, diagnosis_types, default_config, threshold_config, created_by)
            VALUES 
                ('亮度检测模板', '检测摄像头画面亮度是否正常', '["brightness"]', '{}', '{"min_brightness": 30, "max_brightness": 200}', '1'),
                ('清晰度检测模板', '检测摄像头画面清晰度', '["clarity"]', '{}', '{"min_clarity_score": 0.7}', '1'),
                ('噪声检测模板', '检测摄像头画面噪声水平', '["noise"]', '{}', '{"max_noise_level": 0.3}', '1')
        """))
        
        print("已插入示例模板")
        
    print("诊断模块数据库模型更新完成！")

if __name__ == "__main__":
    asyncio.run(update_diagnosis_models())