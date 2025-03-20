#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 主程序入口

此文件是系统的入口点，负责初始化所有组件并启动应用。
功能包括：
- 加载配置文件
- 设置日志系统
- 初始化业务逻辑协调器
- 启动Web界面
- 处理命令行参数

作者: AI助手
创建日期: 2023-06-01
"""

import yaml
import logging
import argparse
import sys
import time
import os
from datetime import datetime

def load_config(config_path):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)

def setup_logging(config):
    """设置日志记录"""
    log_level = config.get('system', {}).get('log_level', 'INFO')
    log_dir = os.path.join(config.get('system', {}).get('data_dir', './data'), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"ecommerce_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Level: {log_level}")
    return logger

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="电商热卖排行分析系统")
    parser.add_argument('--config', default='./config/config.yaml', help='配置文件路径')
    parser.add_argument('--collect', action='store_true', help='启动时收集数据')
    parser.add_argument('--port', type=int, help='Web应用端口，覆盖配置文件设置')
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 应用命令行参数覆盖配置
    if args.port:
        config['ui']['port'] = args.port
    
    # 设置日志记录
    logger = setup_logging(config)
    
    try:
        logger.info("Initializing system...")
        
        # 导入组件
        from business_logic.orchestrator import SystemOrchestrator
        from ui.app import GradioApp
        
        # 初始化系统协调器
        orchestrator = SystemOrchestrator(config)
        logger.info("System orchestrator initialized")
        
        # 如果指定了--collect参数，先收集数据
        if args.collect:
            logger.info("Collecting initial data...")
            orchestrator.collect_data()
            logger.info("Initial data collection completed")
        
        # 初始化Web应用
        logger.info("Starting web application...")
        app = GradioApp(orchestrator, config)
        app.launch()
        
    except Exception as e:
        logger.error(f"Error starting system: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 