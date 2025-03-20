#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 排行分析引擎

此文件实现商品排行分析的核心逻辑，负责生成各类排行榜。
功能包括：
- 热门商品排行榜生成
- 快速上升商品排行
- 价格区间商品排行
- 跨平台商品对比分析
- 热门商品属性分析

作者: AI助手
创建日期: 2023-06-01
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import time

class RankingEngine:
    """排行分析引擎，负责生成各类商品排行榜"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_hot_products(self, platform=None, category=None, time_range='week', limit=20):
        """获取热门商品排行"""
        try:
            session = self.db.Session()
            
            # 构建基本查询
            query = session.query(self.db.models.Product)
            
            # 应用平台过滤
            if platform:
                query = query.filter(self.db.models.Product.platform == platform.lower())
            
            # 应用类别过滤
            if category:
                query = query.filter(self.db.models.Product.category == category)
            
            # 根据热度指标排序 (销量+评分+评论数的加权组合)
            # 使用SQLAlchemy的排序表达式
            query = query.order_by(
                (
                    (self.db.models.Product.sales_volume * 1.0) + 
                    (self.db.models.Product.rating * 20.0) + 
                    (self.db.models.Product.reviews_count * 0.1)
                ).desc()
            )
            
            # 限制结果数量
            query = query.limit(limit)
            
            # 执行查询并转换为字典列表
            products = [p.to_dict() for p in query.all()]
            
            # 添加排名
            for i, product in enumerate(products):
                product['rank'] = i + 1
            
            # 记录日志
            self.logger.info(f"Generated hot products ranking. Platform: {platform}, Category: {category}, Items: {len(products)}")
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error getting hot products: {e}")
            return []
        finally:
            session.close()
    
    def get_rising_products(self, platform=None, category=None, days=7, limit=20):
        """获取上升最快的商品排行"""
        try:
            session = self.db.Session()
            now = time.time()
            start_time = now - (days * 86400)  # 转换为秒
            
            # 获取所有符合条件的商品ID
            product_query = session.query(self.db.models.Product.product_id)
            
            if platform:
                product_query = product_query.filter(self.db.models.Product.platform == platform.lower())
            
            if category:
                product_query = product_query.filter(self.db.models.Product.category == category)
            
            product_ids = [p[0] for p in product_query.all()]
            
            if not product_ids:
                return []
            
            # 计算增长率
            products_with_growth = []
            
            for product_id in product_ids:
                try:
                    # 获取当前商品数据
                    product = session.query(self.db.models.Product).filter_by(product_id=product_id).first()
                    
                    if not product:
                        continue
                        
                    # 获取历史数据
                    history_query = session.query(self.db.models.ProductHistory)\
                        .filter(
                            self.db.models.ProductHistory.product_id == product_id,
                            self.db.models.ProductHistory.date >= start_time
                        )\
                        .order_by(self.db.models.ProductHistory.date.asc())
                    
                    history = history_query.all()
                    
                    # 计算增长率
                    growth_rate = 0
                    if history and len(history) > 1:
                        first_record = history[0]
                        last_record = history[-1]
                        
                        if first_record.sales_volume > 0:
                            growth_rate = ((last_record.sales_volume - first_record.sales_volume) / first_record.sales_volume) * 100
                    
                    # 创建包含增长率的商品数据
                    product_dict = product.to_dict()
                    product_dict['growth_rate'] = round(growth_rate, 2)
                    
                    products_with_growth.append(product_dict)
                    
                except Exception as e:
                    self.logger.error(f"Error calculating growth for product {product_id}: {e}")
                    continue
            
            # 按增长率排序
            products_with_growth.sort(key=lambda x: x.get('growth_rate', 0), reverse=True)
            
            # 限制结果数量
            products_with_growth = products_with_growth[:limit]
            
            # 添加排名
            for i, product in enumerate(products_with_growth):
                product['rank'] = i + 1
            
            return products_with_growth
            
        except Exception as e:
            self.logger.error(f"Error getting rising products: {e}")
            return []
        finally:
            session.close()
    
    def get_category_rankings(self, platform=None, limit_per_category=10):
        """获取按类别分组的排行榜"""
        try:
            session = self.db.Session()
            
            # 获取所有类别
            category_query = session.query(self.db.models.Product.category).distinct()
            
            if platform:
                category_query = category_query.filter(self.db.models.Product.platform == platform.lower())
            
            categories = [c[0] for c in category_query.all() if c[0]]
            
            # 为每个类别获取热门商品
            result = {}
            for category in categories:
                products = self.get_hot_products(
                    platform=platform,
                    category=category,
                    limit=limit_per_category
                )
                
                if products:
                    result[category] = products
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting category rankings: {e}")
            return {}
        finally:
            session.close()
    
    def get_price_range_rankings(self, platform=None, price_ranges=None, limit_per_range=10):
        """获取按价格区间分组的排行榜"""
        if not price_ranges:
            # 默认价格区间
            price_ranges = [
                {'min': 0, 'max': 50, 'label': '低价'},
                {'min': 50, 'max': 200, 'label': '中价'},
                {'min': 200, 'max': 1000, 'label': '高价'},
                {'min': 1000, 'max': float('inf'), 'label': '奢侈品'}
            ]
        
        try:
            session = self.db.Session()
            
            result = {}
            for price_range in price_ranges:
                min_price = price_range['min']
                max_price = price_range['max']
                label = price_range['label']
                
                # 构建查询
                query = session.query(self.db.models.Product)
                
                # 应用平台过滤
                if platform:
                    query = query.filter(self.db.models.Product.platform == platform.lower())
                
                # 应用价格区间过滤
                query = query.filter(self.db.models.Product.price >= min_price)
                if max_price != float('inf'):
                    query = query.filter(self.db.models.Product.price < max_price)
                
                # 按热度排序
                query = query.order_by(
                    (
                        (self.db.models.Product.sales_volume * 1.0) + 
                        (self.db.models.Product.rating * 20.0) + 
                        (self.db.models.Product.reviews_count * 0.1)
                    ).desc()
                )
                
                # 限制结果数量
                query = query.limit(limit_per_range)
                
                # 执行查询并转换为字典列表
                products = [p.to_dict() for p in query.all()]
                
                # 添加排名
                for i, product in enumerate(products):
                    product['rank'] = i + 1
                
                if products:
                    result[label] = products
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting price range rankings: {e}")
            return {}
        finally:
            session.close()
    
    def get_cross_platform_comparison(self, category=None, limit=10):
        """获取跨平台商品对比"""
        try:
            results = {}
            platforms = ['tiktok', 'amazon', 'shopee']
            
            for platform in platforms:
                products = self.get_hot_products(
                    platform=platform,
                    category=category,
                    limit=limit
                )
                
                if products:
                    results[platform] = products
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting cross platform comparison: {e}")
            return {}
    
    def get_popular_attributes(self, platform=None, category=None, limit=10):
        """分析热门商品的共同属性"""
        try:
            # 获取热门商品
            hot_products = self.get_hot_products(platform=platform, category=category, limit=50)
            
            if not hot_products:
                return {}
            
            # 分析关键词频率
            keywords = []
            for product in hot_products:
                if 'keywords' in product and product['keywords']:
                    keywords.extend(product['keywords'])
            
            # 计算关键词频率
            keyword_freq = pd.Series(keywords).value_counts().to_dict()
            
            # 提取最常见的关键词
            top_keywords = dict(sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:limit])
            
            # 分析价格范围
            prices = [product.get('price', 0) for product in hot_products if product.get('price', 0) > 0]
            price_stats = {
                'min': min(prices) if prices else 0,
                'max': max(prices) if prices else 0,
                'average': sum(prices) / len(prices) if prices else 0,
                'median': sorted(prices)[len(prices) // 2] if prices else 0
            }
            
            # 分析评分分布
            ratings = [product.get('rating', 0) for product in hot_products if product.get('rating', 0) > 0]
            rating_stats = {
                'average': sum(ratings) / len(ratings) if ratings else 0,
                'min': min(ratings) if ratings else 0,
                'max': max(ratings) if ratings else 0
            }
            
            # 返回分析结果
            return {
                'top_keywords': top_keywords,
                'price_stats': price_stats,
                'rating_stats': rating_stats,
                'total_products_analyzed': len(hot_products)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing popular attributes: {e}")
            return {}
    
    def get_price_performance_ranking(self, platform=None, category=None, limit=20):
        """获取性价比排行榜"""
        try:
            # 创建数据库会话
            session = self.db.Session()
            
            # 构建查询
            query = session.query(self.db.models.Product)
            
            # 平台筛选
            if platform:
                query = query.filter(self.db.models.Product.platform == platform)
            
            # 类别筛选
            if category:
                query = query.filter(self.db.models.Product.category == category)
            
            # 获取结果
            products = query.all()
            
            # 转换为DataFrame
            df = pd.DataFrame([product.to_dict() for product in products])
            
            # 确保必要的列存在
            if 'price' not in df.columns or 'rating' not in df.columns:
                return []
            
            # 过滤掉无效数据
            df = df[(df['price'] > 0) & (df['rating'] > 0)]
            
            if df.empty:
                return []
            
            # 计算性价比得分
            # 性价比 = 评分 / 价格的对数（使用对数是因为价格范围可能很大）
            df['value_score'] = df['rating'] / np.log1p(df['price'])
            
            # 按性价比排序
            df = df.sort_values('value_score', ascending=False).head(limit)
            
            # 转换回列表
            result = []
            for rank, (_, row) in enumerate(df.iterrows(), 1):
                product_dict = row.to_dict()
                product_dict['rank'] = rank
                result.append(product_dict)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting price performance ranking: {e}")
            return []
        finally:
            session.close()
    
    def _get_time_threshold(self, time_range):
        """根据时间范围获取时间阈值"""
        now = datetime.now()
        
        if time_range == 'day':
            return (now - timedelta(days=1)).timestamp()
        elif time_range == 'week':
            return (now - timedelta(weeks=1)).timestamp()
        elif time_range == 'month':
            return (now - timedelta(days=30)).timestamp()
        elif time_range == 'year':
            return (now - timedelta(days=365)).timestamp()
        else:
            # 默认为一周
            return (now - timedelta(weeks=1)).timestamp() 