#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 趋势分析器

此文件实现商品和市场趋势分析功能，处理时间序列数据。
功能包括：
- 销量趋势分析
- 评分趋势分析
- 价格变化趋势分析
- 类别增长率分析
- 趋势可视化

作者: AI助手
创建日期: 2023-06-01
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import time

class TrendAnalyzer:
    """趋势分析器，分析商品历史趋势和市场变化"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_sales_trend(self, product_id=None, platform=None, category=None, days=30):
        """获取销量趋势数据"""
        try:
            session = self.db.Session()
            now = time.time()
            start_time = now - (days * 86400)  # 转换为秒
            
            # 构建查询
            query = session.query(
                self.db.models.ProductHistory.date,
                self.db.models.ProductHistory.sales_volume
            ).filter(self.db.models.ProductHistory.date >= start_time)
            
            # 应用过滤
            if product_id:
                query = query.filter(self.db.models.ProductHistory.product_id == product_id)
            
            if platform:
                query = query.filter(self.db.models.ProductHistory.platform == platform.lower())
            
            if category:
                query = query.filter(self.db.models.ProductHistory.category == category)
            
            # 按时间排序
            query = query.order_by(self.db.models.ProductHistory.date.asc())
            
            # 执行查询
            results = query.all()
            
            # 处理结果
            if not results:
                return {
                    'dates': [],
                    'sales': [],
                    'growth_rate': 0
                }
            
            # 转换为pandas DataFrame方便处理
            df = pd.DataFrame(results, columns=['date', 'sales_volume'])
            
            # 转换时间戳为日期
            df['date'] = pd.to_datetime(df['date'], unit='s').dt.date
            
            # 如果是单个商品，直接返回时间序列
            if product_id:
                dates = [d.strftime('%Y-%m-%d') for d in df['date'].tolist()]
                sales = df['sales_volume'].tolist()
                
                # 计算增长率
                growth_rate = 0
                if len(sales) > 1 and sales[0] > 0:
                    growth_rate = ((sales[-1] - sales[0]) / sales[0]) * 100
                
                return {
                    'dates': dates,
                    'sales': sales,
                    'growth_rate': round(growth_rate, 2)
                }
            
            # 如果是类别或平台，按日期分组并求和
            daily_sales = df.groupby('date').agg({'sales_volume': 'sum'}).reset_index()
            
            dates = [d.strftime('%Y-%m-%d') for d in daily_sales['date'].tolist()]
            sales = daily_sales['sales_volume'].tolist()
            
            # 计算增长率
            growth_rate = 0
            if len(sales) > 1 and sales[0] > 0:
                growth_rate = ((sales[-1] - sales[0]) / sales[0]) * 100
            
            return {
                'dates': dates,
                'sales': sales,
                'growth_rate': round(growth_rate, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting sales trend: {e}")
            return {
                'dates': [],
                'sales': [],
                'growth_rate': 0
            }
        finally:
            session.close()
    
    def get_rating_trend(self, product_id=None, platform=None, category=None, days=30):
        """获取评分趋势数据"""
        try:
            session = self.db.Session()
            now = time.time()
            start_time = now - (days * 86400)  # 转换为秒
            
            # 构建查询
            query = session.query(
                self.db.models.ProductHistory.date,
                self.db.models.ProductHistory.rating
            ).filter(self.db.models.ProductHistory.date >= start_time)
            
            # 应用过滤
            if product_id:
                query = query.filter(self.db.models.ProductHistory.product_id == product_id)
            
            if platform:
                query = query.filter(self.db.models.ProductHistory.platform == platform.lower())
            
            if category:
                query = query.filter(self.db.models.ProductHistory.category == category)
            
            # 按时间排序
            query = query.order_by(self.db.models.ProductHistory.date.asc())
            
            # 执行查询
            results = query.all()
            
            # 处理结果
            if not results:
                return {
                    'dates': [],
                    'ratings': [],
                    'trend': 'stable'
                }
            
            # 转换为pandas DataFrame方便处理
            df = pd.DataFrame(results, columns=['date', 'rating'])
            
            # 转换时间戳为日期
            df['date'] = pd.to_datetime(df['date'], unit='s').dt.date
            
            # 如果是单个商品，直接返回时间序列
            if product_id:
                dates = [d.strftime('%Y-%m-%d') for d in df['date'].tolist()]
                ratings = df['rating'].tolist()
                
                # 计算评分趋势
                trend = 'stable'
                if len(ratings) > 1:
                    if ratings[-1] > ratings[0]:
                        trend = 'rising'
                    elif ratings[-1] < ratings[0]:
                        trend = 'falling'
                
                return {
                    'dates': dates,
                    'ratings': ratings,
                    'trend': trend
                }
            
            # 如果是类别或平台，按日期分组并求平均
            daily_ratings = df.groupby('date').agg({'rating': 'mean'}).reset_index()
            
            dates = [d.strftime('%Y-%m-%d') for d in daily_ratings['date'].tolist()]
            ratings = daily_ratings['rating'].tolist()
            
            # 计算评分趋势
            trend = 'stable'
            if len(ratings) > 1:
                if ratings[-1] > ratings[0]:
                    trend = 'rising'
                elif ratings[-1] < ratings[0]:
                    trend = 'falling'
            
            return {
                'dates': dates,
                'ratings': ratings,
                'trend': trend
            }
            
        except Exception as e:
            self.logger.error(f"Error getting rating trend: {e}")
            return {
                'dates': [],
                'ratings': [],
                'trend': 'stable'
            }
        finally:
            session.close()
    
    def get_trend_summary(self, platform=None, days=30):
        """获取总体趋势概览"""
        try:
            session = self.db.Session()
            now = time.time()
            start_time = now - (days * 86400)  # 转换为秒
            
            # 获取类别列表
            category_query = session.query(self.db.models.Product.category).distinct()
            if platform:
                category_query = category_query.filter(self.db.models.Product.platform == platform.lower())
            
            categories = [c[0] for c in category_query.all() if c[0]]
            
            # 整体销量趋势
            sales_trend = self.get_sales_trend(platform=platform, days=days)
            
            # 整体评分趋势
            rating_trend = self.get_rating_trend(platform=platform, days=days)
            
            # 各类别趋势
            category_trends = {}
            for category in categories:
                cat_sales = self.get_sales_trend(platform=platform, category=category, days=days)
                cat_ratings = self.get_rating_trend(platform=platform, category=category, days=days)
                
                category_trends[category] = {
                    'sales_growth': cat_sales['growth_rate'],
                    'rating_trend': cat_ratings['trend'],
                }
            
            # 找出增长最快的类别
            if category_trends:
                fastest_growing = max(category_trends.items(), key=lambda x: x[1]['sales_growth'])
                
                # 判断整体趋势
                overall_trend = 'stable'
                if sales_trend['growth_rate'] > 5:
                    overall_trend = 'rising'
                elif sales_trend['growth_rate'] < -5:
                    overall_trend = 'falling'
                
                return {
                    'overall_sales_growth': sales_trend['growth_rate'],
                    'overall_rating_trend': rating_trend['trend'],
                    'overall_trend': overall_trend,
                    'fastest_growing_category': fastest_growing[0],
                    'fastest_growing_rate': fastest_growing[1]['sales_growth'],
                    'category_trends': category_trends
                }
            
            return {
                'overall_sales_growth': sales_trend['growth_rate'],
                'overall_rating_trend': rating_trend['trend'],
                'overall_trend': 'stable',
                'category_trends': {}
            }
            
        except Exception as e:
            self.logger.error(f"Error getting trend summary: {e}")
            return {
                'overall_sales_growth': 0,
                'overall_rating_trend': 'stable',
                'overall_trend': 'stable',
                'category_trends': {}
            }
        finally:
            session.close()
    
    def generate_trend_chart(self, data_type, data, title=''):
        """生成趋势图表"""
        try:
            # 如果没有数据，返回None
            if not data or not data.get('dates'):
                return None
            
            dates = data['dates']
            
            # 根据数据类型选择值
            if data_type == 'sales':
                values = data['sales']
                ylabel = '销量'
            elif data_type == 'rating':
                values = data['ratings']
                ylabel = '评分'
            else:
                return None
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 绘制趋势线
            ax.plot(dates, values, marker='o', linestyle='-', linewidth=2)
            
            # 设置标题和标签
            ax.set_title(title)
            ax.set_xlabel('日期')
            ax.set_ylabel(ylabel)
            
            # 设置x轴标签旋转，以防止重叠
            plt.xticks(rotation=45)
            
            # 添加网格线
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # 自动调整布局
            fig.tight_layout()
            
            # 将图表转换为base64编码的PNG
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            
            # 关闭图表以释放内存
            plt.close(fig)
            
            # 返回base64编码的图像
            return base64.b64encode(image_png).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Error generating trend chart: {e}")
            return None

    def analyze_sales_trend(self, platform=None, category=None, days=30):
        """分析销售趋势"""
        try:
            # 创建数据库会话
            session = self.db.Session()
            
            # 获取当前时间和起始时间戳
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            start_timestamp = start_time.timestamp()
            
            # 构建查询
            query = session.query(
                self.db.models.ProductHistory.date,
                self.db.models.ProductHistory.platform,
                self.db.models.ProductHistory.category,
                self.db.models.ProductHistory.sales_volume
            ).filter(self.db.models.ProductHistory.date >= start_timestamp)
            
            # 平台筛选
            if platform:
                query = query.filter(self.db.models.ProductHistory.platform == platform)
            
            # 类别筛选
            if category:
                query = query.filter(self.db.models.ProductHistory.category == category)
            
            # 执行查询
            results = query.all()
            
            # 转换为DataFrame
            df = pd.DataFrame(results, columns=['date', 'platform', 'category', 'sales_volume'])
            
            # 转换时间戳为日期
            df['date'] = pd.to_datetime(df['date'], unit='s').dt.date
            
            # 按日期和平台/类别分组，计算每日销量
            if platform and not category:
                # 按类别分组
                grouped = df.groupby(['date', 'category'])['sales_volume'].sum().reset_index()
                pivot_df = grouped.pivot(index='date', columns='category', values='sales_volume').fillna(0)
            elif category and not platform:
                # 按平台分组
                grouped = df.groupby(['date', 'platform'])['sales_volume'].sum().reset_index()
                pivot_df = grouped.pivot(index='date', columns='platform', values='sales_volume').fillna(0)
            elif platform and category:
                # 不分组，只看总体趋势
                grouped = df.groupby('date')['sales_volume'].sum().reset_index()
                pivot_df = grouped.set_index('date')
            else:
                # 按平台和类别分组
                grouped = df.groupby(['date', 'platform', 'category'])['sales_volume'].sum().reset_index()
                # 为简单起见，这里只按平台分组
                grouped = grouped.groupby(['date', 'platform'])['sales_volume'].sum().reset_index()
                pivot_df = grouped.pivot(index='date', columns='platform', values='sales_volume').fillna(0)
            
            # 确保日期连续
            date_range = pd.date_range(start=start_time.date(), end=end_time.date())
            pivot_df = pivot_df.reindex(date_range).fillna(0)
            
            # 计算总销量趋势
            pivot_df['total'] = pivot_df.sum(axis=1)
            
            # 绘制趋势图
            fig, ax = plt.subplots(figsize=(10, 6))
            
            for column in pivot_df.columns:
                ax.plot(pivot_df.index, pivot_df[column], label=column)
            
            ax.set_title('销量趋势分析')
            ax.set_xlabel('日期')
            ax.set_ylabel('销量')
            ax.legend()
            ax.grid(True)
            
            # 保存图表为Base64字符串
            buffer = BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            # 计算增长率
            first_day_total = pivot_df['total'].iloc[0] if not pivot_df.empty else 0
            last_day_total = pivot_df['total'].iloc[-1] if not pivot_df.empty else 0
            
            if first_day_total > 0:
                growth_rate = (last_day_total - first_day_total) / first_day_total * 100
            else:
                growth_rate = 0
            
            # 返回分析结果
            return {
                'trend_data': pivot_df.to_dict(),
                'growth_rate': growth_rate,
                'chart_image': f"data:image/png;base64,{image_base64}",
                'analysis_period': {
                    'start_date': start_time.strftime('%Y-%m-%d'),
                    'end_date': end_time.strftime('%Y-%m-%d')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing sales trend: {e}")
            return {}
        finally:
            session.close()
    
    def analyze_category_trend(self, platform=None, days=30):
        """分析类别趋势"""
        try:
            # 创建数据库会话
            session = self.db.Session()
            
            # 获取当前时间和起始时间戳
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            start_timestamp = start_time.timestamp()
            
            # 构建查询
            query = session.query(
                self.db.models.ProductHistory.date,
                self.db.models.ProductHistory.category,
                self.db.models.ProductHistory.sales_volume
            ).filter(self.db.models.ProductHistory.date >= start_timestamp)
            
            # 平台筛选
            if platform:
                query = query.filter(self.db.models.ProductHistory.platform == platform)
            
            # 执行查询
            results = query.all()
            
            # 转换为DataFrame
            df = pd.DataFrame(results, columns=['date', 'category', 'sales_volume'])
            
            # 转换时间戳为日期
            df['date'] = pd.to_datetime(df['date'], unit='s').dt.date
            
            # 按日期和类别分组，计算每日销量
            grouped = df.groupby(['date', 'category'])['sales_volume'].sum().reset_index()
            
            # 获取每个类别的总销量
            category_totals = grouped.groupby('category')['sales_volume'].sum().sort_values(ascending=False)
            top_categories = category_totals.head(5).index.tolist()
            
            # 筛选出前5个类别的数据
            filtered_df = grouped[grouped['category'].isin(top_categories)]
            
            # 透视表
            pivot_df = filtered_df.pivot(index='date', columns='category', values='sales_volume').fillna(0)
            
            # 确保日期连续
            date_range = pd.date_range(start=start_time.date(), end=end_time.date())
            pivot_df = pivot_df.reindex(date_range).fillna(0)
            
            # 绘制趋势图
            fig, ax = plt.subplots(figsize=(10, 6))
            
            for column in pivot_df.columns:
                ax.plot(pivot_df.index, pivot_df[column], label=column)
            
            ax.set_title('类别销量趋势分析')
            ax.set_xlabel('日期')
            ax.set_ylabel('销量')
            ax.legend()
            ax.grid(True)
            
            # 保存图表为Base64字符串
            buffer = BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            # 计算类别增长率
            growth_rates = {}
            for category in pivot_df.columns:
                first_day = pivot_df[category].iloc[0]
                last_day = pivot_df[category].iloc[-1]
                
                if first_day > 0:
                    growth_rate = (last_day - first_day) / first_day * 100
                else:
                    growth_rate = 0
                
                growth_rates[category] = growth_rate
            
            # 绘制饼图显示各类别占比
            category_percentages = category_totals / category_totals.sum() * 100
            
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(category_percentages.head(5), labels=category_percentages.head(5).index, autopct='%1.1f%%')
            ax.set_title('类别销量占比')
            
            # 保存饼图为Base64字符串
            buffer2 = BytesIO()
            fig.savefig(buffer2, format='png')
            buffer2.seek(0)
            pie_image_base64 = base64.b64encode(buffer2.getvalue()).decode('utf-8')
            plt.close(fig)
            
            # 返回分析结果
            return {
                'trend_data': pivot_df.to_dict(),
                'category_totals': category_totals.to_dict(),
                'growth_rates': growth_rates,
                'trend_chart': f"data:image/png;base64,{image_base64}",
                'pie_chart': f"data:image/png;base64,{pie_image_base64}",
                'analysis_period': {
                    'start_date': start_time.strftime('%Y-%m-%d'),
                    'end_date': end_time.strftime('%Y-%m-%d')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing category trend: {e}")
            return {}
        finally:
            session.close()
    
    def analyze_price_trend(self, platform=None, category=None, days=30):
        """分析价格趋势"""
        try:
            # 创建数据库会话
            session = self.db.Session()
            
            # 获取当前时间和起始时间戳
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            start_timestamp = start_time.timestamp()
            
            # 构建查询
            query = session.query(
                self.db.models.ProductHistory.date,
                self.db.models.ProductHistory.platform,
                self.db.models.ProductHistory.category,
                self.db.models.ProductHistory.price
            ).filter(self.db.models.ProductHistory.date >= start_timestamp)
            
            # 平台筛选
            if platform:
                query = query.filter(self.db.models.ProductHistory.platform == platform)
            
            # 类别筛选
            if category:
                query = query.filter(self.db.models.ProductHistory.category == category)
            
            # 执行查询
            results = query.all()
            
            # 转换为DataFrame
            df = pd.DataFrame(results, columns=['date', 'platform', 'category', 'price'])
            
            # 转换时间戳为日期
            df['date'] = pd.to_datetime(df['date'], unit='s').dt.date
            
            # 按日期分组，计算平均价格
            if platform and category:
                # 不分组，直接计算平均价格
                grouped = df.groupby('date')['price'].mean().reset_index()
                pivot_df = grouped.set_index('date')
                pivot_df.columns = ['average_price']
            elif platform:
                # 按类别分组
                grouped = df.groupby(['date', 'category'])['price'].mean().reset_index()
                pivot_df = grouped.pivot(index='date', columns='category', values='price').fillna(0)
            elif category:
                # 按平台分组
                grouped = df.groupby(['date', 'platform'])['price'].mean().reset_index()
                pivot_df = grouped.pivot(index='date', columns='platform', values='price').fillna(0)
            else:
                # 按平台分组
                grouped = df.groupby(['date', 'platform'])['price'].mean().reset_index()
                pivot_df = grouped.pivot(index='date', columns='platform', values='price').fillna(0)
            
            # 确保日期连续
            date_range = pd.date_range(start=start_time.date(), end=end_time.date())
            pivot_df = pivot_df.reindex(date_range).fillna(method='ffill')
            
            # 计算平均价格趋势
            if 'average_price' not in pivot_df.columns:
                pivot_df['average_price'] = pivot_df.mean(axis=1)
            
            # 绘制趋势图
            fig, ax = plt.subplots(figsize=(10, 6))
            
            for column in pivot_df.columns:
                ax.plot(pivot_df.index, pivot_df[column], label=column)
            
            ax.set_title('价格趋势分析')
            ax.set_xlabel('日期')
            ax.set_ylabel('价格')
            ax.legend()
            ax.grid(True)
            
            # 保存图表为Base64字符串
            buffer = BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            # 计算价格变动率
            first_day_avg = pivot_df['average_price'].iloc[0] if 'average_price' in pivot_df.columns and not pivot_df.empty else 0
            last_day_avg = pivot_df['average_price'].iloc[-1] if 'average_price' in pivot_df.columns and not pivot_df.empty else 0
            
            if first_day_avg > 0:
                price_change_rate = (last_day_avg - first_day_avg) / first_day_avg * 100
            else:
                price_change_rate = 0
            
            # 返回分析结果
            return {
                'trend_data': pivot_df.to_dict(),
                'price_change_rate': price_change_rate,
                'chart_image': f"data:image/png;base64,{image_base64}",
                'analysis_period': {
                    'start_date': start_time.strftime('%Y-%m-%d'),
                    'end_date': end_time.strftime('%Y-%m-%d')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing price trend: {e}")
            return {}
        finally:
            session.close()
    
    def get_trend_summary(self, platform=None, days=30):
        """获取趋势综合分析"""
        # 销售趋势
        sales_trend = self.analyze_sales_trend(platform=platform, days=days)
        
        # 类别趋势
        category_trend = self.analyze_category_trend(platform=platform, days=days)
        
        # 价格趋势
        price_trend = self.analyze_price_trend(platform=platform, days=days)
        
        # 生成摘要
        if not sales_trend or not category_trend or not price_trend:
            return {
                'error': 'Failed to generate trend summary',
                'sales_trend': sales_trend,
                'category_trend': category_trend,
                'price_trend': price_trend
            }
        
        # 获取增长最快的类别
        growth_rates = category_trend.get('growth_rates', {})
        fastest_growing = max(growth_rates.items(), key=lambda x: x[1]) if growth_rates else (None, 0)
        
        # 获取销量最高的类别
        category_totals = category_trend.get('category_totals', {})
        top_category = max(category_totals.items(), key=lambda x: x[1]) if category_totals else (None, 0)
        
        # 价格变动趋势
        price_change = price_trend.get('price_change_rate', 0)
        
        # 生成摘要文本
        summary_text = f"""
        ## 电商热销趋势分析摘要
        
        分析周期: {sales_trend.get('analysis_period', {}).get('start_date')} 至 {sales_trend.get('analysis_period', {}).get('end_date')}
        
        ### 销售趋势
        - 整体销售增长率: {sales_trend.get('growth_rate', 0):.2f}%
        
        ### 类别趋势
        - 销量最高的类别: {top_category[0]} (总销量: {top_category[1]})
        - 增长最快的类别: {fastest_growing[0]} (增长率: {fastest_growing[1]:.2f}%)
        
        ### 价格趋势
        - 整体价格变动率: {price_change:.2f}%
        
        ### 综合分析
        """
        
        # 根据数据添加综合分析
        if sales_trend.get('growth_rate', 0) > 20:
            summary_text += "- 整体市场呈现强劲增长趋势\n"
        elif sales_trend.get('growth_rate', 0) < -10:
            summary_text += "- 整体市场呈现下滑趋势，可能需要调整策略\n"
        else:
            summary_text += "- 整体市场相对稳定\n"
        
        if fastest_growing[1] > 50:
            summary_text += f"- {fastest_growing[0]} 类别呈现爆发性增长，建议重点关注\n"
        
        if price_change > 10:
            summary_text += "- 价格整体呈上升趋势，市场可能处于卖方市场\n"
        elif price_change < -10:
            summary_text += "- 价格整体呈下降趋势，市场竞争可能加剧\n"
        
        # 返回综合分析结果
        return {
            'summary_text': summary_text,
            'sales_trend': sales_trend,
            'category_trend': category_trend,
            'price_trend': price_trend
        } 