#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理系统配置中的测试数据脚本
"""

import asyncio
import sys
import os
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db
from models.system import SystemConfig


async def cleanup_test_configs():
    """清理测试配置数据"""
    print("开始清理测试配置数据...")
    
    # 初始化数据库
    await init_db()
    
    # 获取数据库会话
    async for db in get_db():
        try:
            # 查找所有测试相关的配置
            result = await db.execute(
                select(SystemConfig).where(
                    or_(
                        SystemConfig.key.like('test%'),
                        SystemConfig.category == 'test',
                        SystemConfig.category == '??',
                        SystemConfig.category == '测试',
                        SystemConfig.description.like('%test%'),
                        SystemConfig.description.like('%测试%'),
                        SystemConfig.description.like('%??%')
                    )
                )
            )
            test_configs = result.scalars().all()
            
            if not test_configs:
                print("没有找到测试配置数据")
                return
            
            print(f"找到 {len(test_configs)} 个测试配置:")
            for config in test_configs:
                print(f"  - ID: {config.id}, Key: {config.key}, Category: {config.category}, Description: {config.description}")
            
            # 确认删除
            confirm = input("\n确认删除这些测试配置吗？(y/N): ")
            if confirm.lower() != 'y':
                print("取消删除操作")
                return
            
            # 删除测试配置
            deleted_count = 0
            for config in test_configs:
                await db.delete(config)
                deleted_count += 1
                print(f"删除配置: {config.key}")
            
            # 提交事务
            await db.commit()
            print(f"\n成功删除 {deleted_count} 个测试配置！")
            
        except Exception as e:
            await db.rollback()
            print(f"清理测试配置失败: {e}")
            raise
        finally:
            await db.close()
        break


async def check_log_retention_config():
    """检查日志保留配置"""
    print("\n检查日志保留配置...")
    
    async for db in get_db():
        try:
            # 查找log.retention_days配置
            result = await db.execute(
                select(SystemConfig).where(SystemConfig.key == 'log.retention_days')
            )
            config = result.scalar_one_or_none()
            
            if config:
                print(f"找到日志保留配置:")
                print(f"  - ID: {config.id}")
                print(f"  - Key: {config.key}")
                print(f"  - Value: {config.value}")
                print(f"  - Category: {config.category}")
                print(f"  - Description: {config.description}")
                print(f"  - Is Editable: {config.is_editable}")
                print(f"  - Data Type: {config.data_type}")
                print(f"  - Requires Restart: {config.requires_restart}")
                
                if not config.is_editable:
                    print("\n警告: 该配置被标记为不可编辑！")
                    fix_editable = input("是否修复为可编辑状态？(y/N): ")
                    if fix_editable.lower() == 'y':
                        config.is_editable = True
                        await db.commit()
                        print("已修复为可编辑状态")
                else:
                    print("\n配置状态正常，应该可以编辑")
            else:
                print("未找到 log.retention_days 配置")
                
        except Exception as e:
            await db.rollback()
            print(f"检查配置失败: {e}")
            raise
        finally:
            await db.close()
        break


async def main():
    """主函数"""
    try:
        await cleanup_test_configs()
        await check_log_retention_config()
        print("\n操作完成！")
    except Exception as e:
        print(f"操作失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())