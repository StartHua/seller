#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI启动修复脚本
"""

import logging
import yaml
import os

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载配置文件
config_path = 'config/config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 导入系统协调器
logger.info("初始化系统...")
from business_logic.orchestrator import SystemOrchestrator
orchestrator = SystemOrchestrator(config)

# 创建并启动UI
try:
    logger.info("启动Web界面...")
    # 创建必要的UI配置，如果不存在
    if 'ui' not in config:
        logger.warning("UI配置缺失，使用默认配置")
        config['ui'] = {
            'title': "电商热卖排行分析系统",
            'theme': "default",
            'port': 7860,
            'debug': False,
            'default_platform': "全部",
            'default_category': "全部",
            'default_time_range': "week",
            'max_items_display': 100
        }
    
    # 启动UI
    import gradio as gr
    
    def display_welcome():
        return "## 欢迎使用电商热卖排行分析系统\n\n本系统目前正在维护中，部分功能可能不可用。"
    
    with gr.Blocks(title=config['ui'].get('title', "电商系统"), 
                  theme=config['ui'].get('theme', "default")) as app:
        with gr.Tab("首页"):
            gr.Markdown("# 电商热卖排行分析系统")
            gr.Markdown("本系统提供各大电商平台热门商品数据分析")
            
            refresh_btn = gr.Button("刷新数据")
            output = gr.Markdown()
            
            refresh_btn.click(display_welcome, inputs=[], outputs=[output])
        
        # 启动服务器
        port = config['ui'].get('port', 7860)
        app.launch(server_name="0.0.0.0", server_port=port)

except Exception as e:
    logger.error(f"启动UI失败: {e}")
    import traceback
    logger.error(traceback.format_exc()) 