#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 数据采集基类

此文件定义了所有数据采集器的公共接口和方法。
功能包括：
- 定义统一的数据采集接口
- 提供请求管理与重试逻辑
- 处理请求代理和速率限制
- 实现会话管理和错误处理
- 提供日志记录功能

作者: AI助手
创建日期: 2023-06-01
"""

import requests
import logging
import time
import random
from abc import ABC, abstractmethod
from datetime import datetime

class BaseCollector(ABC):
    """数据采集基类，定义通用方法"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化会话
        self.session = requests.Session()
        
        # 设置代理
        if config.get('proxy'):
            self.session.proxies = {
                'http': config['proxy'],
                'https': config['proxy']
            }
            self.logger.info(f"Using proxy: {config['proxy']}")
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        })
    
    @abstractmethod
    def get_hot_products(self, category=None, limit=None):
        """
        获取热门商品列表
        
        Args:
            category: 商品类别
            limit: 返回商品数量限制
            
        Returns:
            list: 商品列表，每个商品应包含标准字段
        """
        pass
    
    def collect_with_retry(self, url, method="GET", data=None, retry_count=3, retry_delay=2):
        """通用的带重试的数据采集方法"""
        for attempt in range(retry_count):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, timeout=10)
                elif method.upper() == "POST":
                    response = self.session.post(url, json=data, timeout=10)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # 检查状态码
                response.raise_for_status()
                
                # 尝试解析JSON
                return response.json()
                
            except requests.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt+1}/{retry_count}): {e}")
                
                # 最后一次尝试失败
                if attempt == retry_count - 1:
                    self.logger.error(f"All retry attempts failed for URL: {url}")
                    raise
                
                # 添加延迟，避免频繁请求
                delay = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                self.logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
    
    def log_collection_task(self, platform, category, interval_hours=24):
        """记录数据采集任务"""
        return {
            "platform": platform,
            "category": category,
            "interval_hours": interval_hours,
            "last_collected": datetime.now().timestamp(),
            "next_collection": datetime.now().timestamp() + (interval_hours * 3600)
        } 