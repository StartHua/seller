#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 业务逻辑协调器

此文件实现系统的业务逻辑协调功能，负责组合各个组件。
功能包括：
- 初始化各个子系统
- 协调数据采集、处理和分析流程
- 提供统一接口给UI层调用
- 管理任务调度和系统状态

作者: AI助手
创建日期: 2023-06-01
"""

import logging
import time
import threading
import schedule
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class SystemOrchestrator:
    """系统业务逻辑协调器，负责连接各个组件"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing System Orchestrator...")
        
        # 初始化数据库管理器
        from storage.database import DatabaseManager
        self.db_manager = DatabaseManager(config)
        self.logger.info("Database manager initialized")
        
        # 初始化数据处理组件
        from data_processing.data_cleaner import DataCleaner
        from data_processing.data_enricher import DataEnricher
        self.data_cleaner = DataCleaner()
        self.logger.info("Data cleaner initialized")
        
        # 初始化LLM服务（如果配置）
        if 'llm' in config and config['llm'].get('enabled', False):
            from llm.llm_service import LLMService
            self.llm_service = LLMService(config['llm'])
            self.data_enricher = DataEnricher(self.llm_service)
            self.logger.info("LLM service and data enricher initialized")
        else:
            self.llm_service = None
            self.data_enricher = None
            self.logger.info("LLM service disabled")
        
        # 初始化数据采集器
        self.collectors = self._init_collectors()
        
        # 初始化分析引擎
        from analytics.ranking_engine import RankingEngine
        from analytics.trend_analyzer import TrendAnalyzer
        
        self.ranking_engine = RankingEngine(self.db_manager)
        self.trend_analyzer = TrendAnalyzer(self.db_manager)
        self.logger.info("Analytics engines initialized")
        
        # 设置定时任务
        self._setup_scheduled_tasks()
        
        self.logger.info("System Orchestrator initialized successfully")
    
    def _init_collectors(self):
        """初始化各平台数据采集器"""
        collectors = {}
        
        # 获取平台配置
        platforms_config = self.config.get('platforms', {})
        
        # 初始化TikTok采集器
        if platforms_config.get('tiktok', {}).get('enabled', False):
            from data_collection.tiktok_collector import TikTokCollector
            collectors['tiktok'] = TikTokCollector(platforms_config['tiktok'])
            self.logger.info("TikTok collector initialized")
        
        # 初始化Amazon采集器
        if platforms_config.get('amazon', {}).get('enabled', False):
            from data_collection.amazon_collector import AmazonCollector
            collectors['amazon'] = AmazonCollector(platforms_config['amazon'])
            self.logger.info("Amazon collector initialized")
        
        # 初始化Shopee采集器
        if platforms_config.get('shopee', {}).get('enabled', False):
            from data_collection.shopee_collector import ShopeeCollector
            collectors['shopee'] = ShopeeCollector(platforms_config['shopee'])
            self.logger.info("Shopee collector initialized")
        
        return collectors
    
    def _setup_scheduled_tasks(self):
        """设置定时任务"""
        collection_interval = self.config.get('collection', {}).get('schedule_interval_hours', 24)
        
        # 设置定时采集任务
        schedule.every(collection_interval).hours.do(self.collect_data)
        self.logger.info(f"Scheduled data collection every {collection_interval} hours")
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Scheduler thread started")
    
    def _run_scheduler(self):
        """运行调度器线程"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    def collect_data(self, platform=None, category=None, limit=None):
        """从各平台采集商品数据"""
        self.logger.info(f"Starting data collection. Platform: {platform}, Category: {category}")
        
        results = []
        collectors_to_use = {}
        
        # 确定要使用的采集器
        if platform:
            if platform in self.collectors:
                collectors_to_use[platform] = self.collectors[platform]
            else:
                self.logger.warning(f"Collector for {platform} not found")
                return []
        else:
            collectors_to_use = self.collectors
        
        # 从每个平台采集数据
        for platform_name, collector in collectors_to_use.items():
            try:
                self.logger.info(f"Collecting data from {platform_name}...")
                
                # 采集热门商品
                platform_products = collector.get_hot_products(category=category, limit=limit)
                
                if platform_products:
                    self.logger.info(f"Collected {len(platform_products)} products from {platform_name}")
                    
                    # 数据清洗
                    cleaned_products = self.data_cleaner.clean_products(platform_products)
                    
                    # 数据增强
                    if self.data_enricher:
                        enriched_products = self.data_enricher.enrich_products(cleaned_products)
                    else:
                        enriched_products = cleaned_products
                    
                    # 保存到数据库
                    for product in enriched_products:
                        self.db_manager.save_product(product)
                    
                    results.extend(enriched_products)
                else:
                    self.logger.warning(f"No products collected from {platform_name}")
            
            except Exception as e:
                self.logger.error(f"Error collecting data from {platform_name}: {e}", exc_info=True)
        
        self.logger.info(f"Data collection completed. Total products: {len(results)}")
        return results
    
    def get_categories(self, platform=None):
        """获取所有商品类别"""
        return self.db_manager.get_categories(platform=platform)
    
    def get_hot_products(self, platform=None, category=None, time_range='week', limit=20):
        """获取热门商品排行"""
        return self.ranking_engine.get_hot_products(
            platform=platform,
            category=category,
            time_range=time_range,
            limit=limit
        )
    
    def get_rising_products(self, platform=None, category=None, days=7, limit=20):
        """获取快速上升的商品"""
        return self.ranking_engine.get_rising_products(
            platform=platform,
            category=category,
            days=days,
            limit=limit
        )
    
    def get_price_range_rankings(self, platform=None, category=None, limit_per_range=5):
        """获取不同价格区间的商品排行"""
        return self.ranking_engine.get_price_range_rankings(
            platform=platform,
            category=category,
            limit_per_range=limit_per_range
        )
    
    def get_category_rankings(self, platform=None, limit_per_category=5):
        """获取各类别热门商品"""
        categories = self.get_categories(platform=platform)
        result = {}
        
        for category in categories[:10]:  # 限制最多处理10个类别
            products = self.get_hot_products(
                platform=platform,
                category=category,
                limit=limit_per_category
            )
            if products:
                result[category] = products
        
        return result
    
    def get_cross_platform_comparison(self, category=None, limit=10):
        """获取跨平台商品对比"""
        return self.ranking_engine.get_cross_platform_comparison(
            category=category,
            limit=limit
        )
    
    def get_sales_trend(self, platform=None, category=None, days=30):
        """获取销量趋势数据"""
        return self.trend_analyzer.get_sales_trend(
            platform=platform,
            category=category,
            days=days
        )
    
    def get_rating_trend(self, platform=None, category=None, days=30):
        """获取评分趋势数据"""
        return self.trend_analyzer.get_rating_trend(
            platform=platform,
            category=category,
            days=days
        )
    
    def get_market_trend_analysis(self, platform=None, category=None, days=30):
        """获取市场趋势分析"""
        return self.trend_analyzer.analyze_market_trend(
            platform=platform,
            category=category,
            days=days
        )
    
    def get_category_growth_rates(self, platform=None, days=30, limit=10):
        """获取类别增长率"""
        return self.trend_analyzer.get_category_growth_rates(
            platform=platform,
            days=days,
            limit=limit
        )
    
    def get_popular_attributes(self, platform=None, category=None, limit=10):
        """分析热门商品的共同属性"""
        return self.ranking_engine.get_popular_attributes(
            platform=platform,
            category=category,
            limit=limit
        )
    
    def get_system_stats(self):
        """获取系统统计信息"""
        try:
            # 获取商品数量
            product_count = self.db_manager.get_product_count()
            
            # 获取平台统计信息
            platform_stats = self.db_manager.get_platform_stats()
            
            # 获取类别数量
            categories = self.get_categories()
            category_count = len(categories)
            
            # 最后更新时间
            last_update = self.db_manager.get_last_update_time()
            
            return {
                'product_count': product_count,
                'platform_stats': platform_stats,
                'category_count': category_count,
                'last_update': last_update,
                'collector_count': len(self.collectors),
                'system_version': self.config.get('system', {}).get('version', '1.0.0')
            }
        except Exception as e:
            self.logger.error(f"Error getting system stats: {e}")
            return {
                'error': str(e)
            }
    
    def ask_ai_question(self, question, context=None):
        """向AI提问"""
        if not self.llm_service:
            return "AI服务未启用"
        
        try:
            return self.llm_service.answer_business_question(question, context)
        except Exception as e:
            self.logger.error(f"Error asking AI question: {e}")
            return f"处理问题时出错: {str(e)}"
    
    def get_platforms(self):
        """获取所有平台"""
        try:
            # 创建会话
            session = self.db_manager.Session()
            
            # 查询不同的平台
            platforms = [platform[0] for platform in session.query(
                self.db_manager.models.Product.platform).distinct().all() if platform[0]]
            
            # 按字母排序
            platforms.sort()
            
            return platforms
        except Exception as e:
            self.logger.error(f"Error getting platforms: {e}")
            return []
        finally:
            session.close()
    
    def get_trend_summary(self, platform=None, days=30):
        """获取趋势综合分析"""
        try:
            trend_summary = self.trend_analyzer.get_trend_summary(
                platform=platform,
                days=days
            )
            return trend_summary
        except Exception as e:
            self.logger.error(f"Error getting trend summary: {e}")
            return {}
    
    def analyze_price_distribution(self, platform=None):
        """分析价格分布"""
        try:
            # 创建会话
            session = self.db_manager.Session()
            
            # 构建查询
            query = session.query(self.db_manager.models.Product.price)
            
            # 平台筛选
            if platform:
                query = query.filter(self.db_manager.models.Product.platform == platform)
            
            # 执行查询
            prices = [price[0] for price in query.all() if price[0] and price[0] > 0]
            
            # 计算统计数据
            if prices:
                # 转换为NumPy数组
                price_array = np.array(prices)
                
                # 计算基本统计数据
                stats = {
                    'count': len(price_array),
                    'min': float(np.min(price_array)),
                    'max': float(np.max(price_array)),
                    'mean': float(np.mean(price_array)),
                    'median': float(np.median(price_array)),
                    'p25': float(np.percentile(price_array, 25)),
                    'p75': float(np.percentile(price_array, 75)),
                    'std': float(np.std(price_array))
                }
                
                return {
                    'price_stats': stats,
                    'price_data': prices
                }
            
            return {}
        except Exception as e:
            self.logger.error(f"Error analyzing price distribution: {e}")
            return {}
        finally:
            session.close()
    
    def analyze_rating_distribution(self, platform=None):
        """分析评分分布"""
        try:
            # 创建会话
            session = self.db_manager.Session()
            
            # 构建查询
            query = session.query(self.db_manager.models.Product.rating)
            
            # 平台筛选
            if platform:
                query = query.filter(self.db_manager.models.Product.platform == platform)
            
            # 执行查询
            ratings = [rating[0] for rating in query.all() if rating[0] and rating[0] > 0]
            
            # 计算统计数据
            if ratings:
                # 转换为NumPy数组
                rating_array = np.array(ratings)
                
                # 计算基本统计数据
                stats = {
                    'count': len(rating_array),
                    'min': float(np.min(rating_array)),
                    'max': float(np.max(rating_array)),
                    'mean': float(np.mean(rating_array)),
                    'median': float(np.median(rating_array)),
                    'rating_std': float(np.std(rating_array))
                }
                
                # 创建评分分布
                rating_distribution = {}
                for i in range(0, 6):
                    lower = i - 0.5 if i > 0 else 0
                    upper = i + 0.5 if i < 5 else 5
                    count = ((rating_array >= lower) & (rating_array < upper)).sum()
                    rating_distribution[str(i)] = int(count)
                
                return {
                    'rating_stats': stats,
                    'rating_distribution': rating_distribution
                }
            
            return {}
        except Exception as e:
            self.logger.error(f"Error analyzing rating distribution: {e}")
            return {}
        finally:
            session.close()
    
    def analyze_keywords(self, platform=None, limit=20):
        """分析关键词频率"""
        try:
            # 创建会话
            session = self.db_manager.Session()
            
            # 构建查询
            query = session.query(self.db_manager.models.Product.keywords)
            
            # 平台筛选
            if platform:
                query = query.filter(self.db_manager.models.Product.platform == platform)
            
            # 执行查询
            keywords_lists = [kw for kw in query.all() if kw[0]]
            
            # 统计关键词频率
            keyword_frequency = {}
            for keywords in keywords_lists:
                if not keywords[0]:
                    continue
                    
                for keyword in keywords[0]:
                    keyword = keyword.strip().lower()
                    if keyword:
                        keyword_frequency[keyword] = keyword_frequency.get(keyword, 0) + 1
            
            # 获取最频繁的关键词
            sorted_keywords = sorted(keyword_frequency.items(), key=lambda x: x[1], reverse=True)
            top_keywords = dict(sorted_keywords[:limit])
            
            return {
                'keyword_frequency': top_keywords,
                'total_keywords': len(keyword_frequency)
            }
        except Exception as e:
            self.logger.error(f"Error analyzing keywords: {e}")
            return {}
        finally:
            session.close()
    
    def ask_question(self, question):
        """回答业务问题"""
        try:
            # 获取相关数据以提供给LLM参考
            hot_products = self.get_hot_products(limit=10)
            trend_summary = self.get_trend_summary()
            categories = self.get_categories()
            
            # 调用LLM回答问题
            answer = self.llm_service.answer_business_question(
                question=question,
                context={
                    'hot_products': hot_products,
                    'trend_summary': trend_summary,
                    'categories': categories
                }
            )
            
            return answer
        except Exception as e:
            self.logger.error(f"Error answering question: {e}")
            return f"很抱歉，我无法回答这个问题。错误：{str(e)}"
    
    def run_scheduled_tasks(self):
        """运行定时任务"""
        try:
            # 收集最新数据
            self.collect_data()
            
            # 记录任务完成
            self.logger.info(f"Scheduled tasks completed at {datetime.now()}")
            
            return {
                "status": "success",
                "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            self.logger.error(f"Error running scheduled tasks: {e}")
            return {
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            } 