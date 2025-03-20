#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 数据增强器

此文件实现商品数据的增强和扩展功能。
功能包括：
- 使用LLM生成商品增强描述
- 提取商品关键词和属性
- 计算商品情感得分
- 分析价格性价比
- 生成商品特征向量

作者: AI助手
创建日期: 2023-06-01
"""

import pandas as pd
import numpy as np
import logging
import re
from concurrent.futures import ThreadPoolExecutor

class DataEnricher:
    """数据增强组件，使用LLM和规则来丰富商品数据"""
    
    def __init__(self, llm_service):
        self.llm = llm_service
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def enrich_products(self, products, max_workers=5):
        """丰富商品数据"""
        if not products:
            return []
            
        try:
            # 记录开始时间
            import time
            start_time = time.time()
            self.logger.info(f"Starting enrichment of {len(products)} products")
            
            # 使用多线程处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                enriched_products = list(executor.map(self._enrich_product, products))
            
            # 记录完成时间
            duration = time.time() - start_time
            self.logger.info(f"Enrichment completed in {duration:.2f} seconds")
            
            return enriched_products
            
        except Exception as e:
            self.logger.error(f"Error enriching products: {e}")
            # 如果处理失败，返回原始数据
            return products
    
    def _enrich_product(self, product):
        """丰富单个商品数据"""
        try:
            # 创建一个新的字典，不修改原始数据
            enriched = product.copy()
            
            # 1. 增强描述
            if enriched.get('description'):
                enriched['enhanced_description'] = self.llm.enhance_description(enriched['description'])
            elif enriched.get('name'):
                # 如果没有描述，根据名称生成
                enriched['enhanced_description'] = self.llm.generate_description(
                    enriched['name'], 
                    enriched.get('category')
                )
            
            # 2. 提取关键词
            enriched['keywords'] = self._extract_keywords(enriched)
            
            # 3. 计算情感评分
            if enriched.get('reviews_data'):
                enriched['sentiment_score'] = self._calculate_sentiment(enriched)
            
            # 4. 计算流行度评分
            enriched['popularity_score'] = self._calculate_popularity_score(enriched)
            
            # 5. 价格分析
            enriched['price_rating'] = self._calculate_price_rating(enriched)
            
            return enriched
            
        except Exception as e:
            self.logger.error(f"Error enriching product {product.get('product_id')}: {e}")
            return product
    
    def _extract_keywords(self, product):
        """从商品数据中提取关键词"""
        try:
            # 结合名称和描述提取关键词
            text = f"{product.get('name', '')} {product.get('description', '')}"
            
            # 简单的规则提取
            words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{2,}\b', text)
            
            # 去除重复，保留最多10个关键词
            keywords = list(set([w.lower() for w in words]))[:10]
            
            return keywords
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []
    
    def _calculate_sentiment(self, product):
        """计算商品的情感评分"""
        try:
            # 如果有评论数据，使用LLM分析情感
            if product.get('reviews_data'):
                # 获取前10条评论用于分析
                reviews = product['reviews_data'][:10]
                
                # 调用LLM分析情感
                sentiment_score = self.llm.analyze_sentiment(reviews)
                return sentiment_score
            
            # 如果没有评论数据，根据评分估算
            elif product.get('rating'):
                # 将评分转换为情感分数 (0-100)
                return (product['rating'] / 5) * 100
            
            return 50  # 默认中性评分
            
        except Exception as e:
            self.logger.error(f"Error calculating sentiment: {e}")
            return 50
    
    def _calculate_popularity_score(self, product):
        """计算商品受欢迎程度评分"""
        try:
            score = 0
            
            # 基于销量的得分
            if product.get('sales_volume'):
                score += min(product['sales_volume'] / 100, 50)
            
            # 基于评论数量的得分
            if product.get('reviews_count'):
                score += min(product['reviews_count'] / 20, 25)
            
            # 基于评分的得分
            if product.get('rating'):
                score += (product['rating'] / 5) * 25
            
            return min(score, 100)  # 最高100分
            
        except Exception as e:
            self.logger.error(f"Error calculating popularity score: {e}")
            return 0
    
    def _calculate_price_rating(self, product):
        """计算价格评级"""
        try:
            # 如果没有价格或评分，无法计算性价比
            if not product.get('price') or not product.get('rating'):
                return "Unknown"
            
            price = product['price']
            rating = product['rating']
            
            # 计算简单的性价比 (评分除以价格的对数)
            price_rating_ratio = rating / (np.log1p(price) + 1)
            
            # 根据性价比分级
            if price_rating_ratio > 1:
                return "Good Value"
            elif price_rating_ratio > 0.5:
                return "Fair Value"
            else:
                return "Expensive"
                
        except Exception as e:
            self.logger.error(f"Error calculating price rating: {e}")
            return "Unknown" 