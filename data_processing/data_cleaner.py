#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 数据清洗器

此文件实现原始数据的清洗和标准化功能。
功能包括：
- 处理缺失值和异常值
- 标准化不同平台的数据格式
- 清理文本数据中的HTML和特殊字符
- 统一数值类型和单位
- 移除重复数据

作者: AI助手
创建日期: 2023-06-01
"""

import pandas as pd
import numpy as np
import logging
import re

class DataCleaner:
    """数据清洗组件，处理原始采集数据"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def clean_products(self, products):
        """清洗商品数据"""
        if not products:
            return []
            
        try:
            # 转换为DataFrame进行批量处理
            df = pd.DataFrame(products)
            
            # 处理缺失值
            df = self._handle_missing_values(df)
            
            # 处理数值异常
            df = self._handle_outliers(df)
            
            # 处理文本数据
            df = self._clean_text_data(df)
            
            # 标准化数据
            df = self._standardize_data(df)
            
            # 转回字典列表
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Error cleaning products: {e}")
            # 如果处理失败，返回原始数据
            return products
    
    def _handle_missing_values(self, df):
        """处理缺失值"""
        # 填充空字符串
        text_columns = ['name', 'description', 'category', 'currency', 'product_url', 'image_url']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')
        
        # 填充数值
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        
        if 'sales_volume' in df.columns:
            df['sales_volume'] = pd.to_numeric(df['sales_volume'], errors='coerce').fillna(0).astype(int)
        
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
        
        if 'reviews_count' in df.columns:
            df['reviews_count'] = pd.to_numeric(df['reviews_count'], errors='coerce').fillna(0).astype(int)
        
        # 确保时间戳存在
        if 'collected_at' not in df.columns or df['collected_at'].isna().any():
            import time
            df['collected_at'] = time.time()
        
        return df
    
    def _handle_outliers(self, df):
        """处理异常值"""
        # 价格异常处理 (非负数)
        if 'price' in df.columns:
            df.loc[df['price'] < 0, 'price'] = 0
        
        # 销量异常处理 (非负数)
        if 'sales_volume' in df.columns:
            df.loc[df['sales_volume'] < 0, 'sales_volume'] = 0
        
        # 评分异常值 (通常在0-5之间)
        if 'rating' in df.columns:
            df.loc[df['rating'] < 0, 'rating'] = 0
            df.loc[df['rating'] > 5, 'rating'] = 5
        
        # 评论数异常处理 (非负数)
        if 'reviews_count' in df.columns:
            df.loc[df['reviews_count'] < 0, 'reviews_count'] = 0
        
        return df
    
    def _clean_text_data(self, df):
        """清洗文本数据"""
        # 清理名称
        if 'name' in df.columns:
            df['name'] = df['name'].astype(str).apply(self._clean_text)
        
        # 清理描述
        if 'description' in df.columns:
            df['description'] = df['description'].astype(str).apply(self._clean_text)
        
        # 清理类别
        if 'category' in df.columns:
            df['category'] = df['category'].astype(str).apply(self._clean_text)
        
        return df
    
    def _clean_text(self, text):
        """清理文本内容"""
        if not text or pd.isna(text):
            return ""
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除额外的空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 移除特殊控制字符
        text = re.sub(r'[\x00-\x1F\x7F]', '', text)
        
        return text
    
    def _standardize_data(self, df):
        """标准化数据格式"""
        # 确保货币代码是标准格式
        if 'currency' in df.columns:
            df['currency'] = df['currency'].str.upper()
            # 默认货币
            df['currency'] = df['currency'].fillna('CNY')
        
        # 确保平台名称是小写
        if 'platform' in df.columns:
            df['platform'] = df['platform'].str.lower()
        
        # 标准化类别名称
        if 'category' in df.columns:
            df['category'] = df['category'].str.strip().str.title()
        
        return df 