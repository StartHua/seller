#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 数据库初始化脚本
"""

import yaml
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保配置文件路径存在
config_path = 'config/config.yaml'
if not os.path.exists(config_path):
    logger.error(f"配置文件不存在: {config_path}")
    exit(1)

# 加载配置
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    logger.info("配置加载成功")
except Exception as e:
    logger.error(f"加载配置失败: {e}")
    exit(1)

# 初始化数据库管理器
try:
    from storage.database import DatabaseManager
    db_manager = DatabaseManager(config)
    
    # 显式调用创建表方法
    logger.info("正在创建数据库表...")
    db_manager._create_tables()
    logger.info("数据库表创建完成!")
except Exception as e:
    logger.error(f"数据库初始化失败: {e}")
    import traceback
    logger.error(traceback.format_exc())
    exit(1) 