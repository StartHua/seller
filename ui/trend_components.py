#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 趋势分析UI组件

此文件实现趋势分析相关的UI组件，使用Gradio库。
功能包括：
- 销量趋势可视化
- 评分趋势可视化
- 类别增长率展示
- 趋势概览生成

作者: AI助手
创建日期: 2023-06-01
"""

import gradio as gr
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

class TrendComponents:
    """趋势分析UI组件"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    def build_trends_tab(self):
        """构建趋势分析标签页"""
        with gr.Tab("趋势分析"):
            with gr.Row():
                with gr.Column(scale=1):
                    trend_platform = gr.Dropdown(
                        choices=["全部", "tiktok", "amazon", "shopee"],
                        value="全部",
                        label="电商平台"
                    )
                    trend_category = gr.Dropdown(
                        choices=["全部"],
                        value="全部",
                        label="商品类别"
                    )
                    trend_days = gr.Slider(
                        minimum=7,
                        maximum=90,
                        value=30,
                        step=1,
                        label="分析天数"
                    )
                    trend_refresh_btn = gr.Button("分析趋势")
                
                with gr.Column(scale=2):
                    trend_summary = gr.Markdown(
                        label="市场趋势概览"
                    )
            
            with gr.Row():
                sales_chart = gr.Plot(label="销量趋势")
                rating_chart = gr.Plot(label="评分趋势")
            
            with gr.Row():
                category_growth_chart = gr.Plot(label="类别增长率")
            
            # 更新类别下拉列表
            def update_categories(platform_val):
                if platform_val == "全部":
                    categories = self.orchestrator.get_categories()
                else:
                    categories = self.orchestrator.get_categories(platform=platform_val)
                
                return gr.Dropdown.update(choices=["全部"] + categories)
                
            trend_platform.change(update_categories, inputs=trend_platform, outputs=trend_category)
            
            # 生成趋势分析
            def generate_trend_analysis(platform_val, category_val, days):
                platform_arg = None if platform_val == "全部" else platform_val
                category_arg = None if category_val == "全部" else category_val
                
                # 获取趋势概览
                trend_summary_data = self.orchestrator.get_trend_summary(
                    platform=platform_arg,
                    category=category_arg,
                    days=days
                )
                
                # 生成概览文本
                summary_text = self._generate_summary_text(trend_summary_data)
                
                # 生成销量趋势图
                sales_data = self.orchestrator.get_sales_trend(
                    platform=platform_arg,
                    category=category_arg,
                    days=days
                )
                
                sales_fig = None
                if sales_data.get('dates'):
                    df = pd.DataFrame({
                        'date': pd.to_datetime(sales_data['dates']),
                        'sales': sales_data['sales']
                    })
                    sales_fig = px.line(
                        df,
                        x='date',
                        y='sales',
                        title="销量趋势",
                        labels={'date': '日期', 'sales': '销量'}
                    )
                    # 添加趋势线
                    sales_fig.add_trace(
                        px.scatter(df, x='date', y='sales', trendline="ols").data[1]
                    )
                
                # 生成评分趋势图
                rating_data = self.orchestrator.get_rating_trend(
                    platform=platform_arg,
                    category=category_arg,
                    days=days
                )
                
                rating_fig = None
                if rating_data.get('dates'):
                    df = pd.DataFrame({
                        'date': pd.to_datetime(rating_data['dates']),
                        'rating': rating_data['ratings']
                    })
                    rating_fig = px.line(
                        df,
                        x='date',
                        y='rating',
                        title="评分趋势",
                        labels={'date': '日期', 'rating': '评分'}
                    )
                    # 设置Y轴范围为0-5
                    rating_fig.update_yaxes(range=[0, 5])
                
                # 生成类别增长率图
                category_growth_fig = None
                if trend_summary_data.get('category_trends'):
                    categories = []
                    growth_rates = []
                    
                    for category, data in trend_summary_data['category_trends'].items():
                        categories.append(category)
                        growth_rates.append(data['sales_growth'])
                    
                    # 创建DataFrame
                    cat_df = pd.DataFrame({
                        'category': categories,
                        'growth_rate': growth_rates
                    })
                    
                    # 按增长率排序
                    cat_df = cat_df.sort_values('growth_rate', ascending=False)
                    
                    # 创建柱状图
                    category_growth_fig = px.bar(
                        cat_df,
                        x='category',
                        y='growth_rate',
                        title="类别销量增长率(%)",
                        labels={'category': '类别', 'growth_rate': '增长率(%)'},
                        color='growth_rate',
                        color_continuous_scale='RdYlGn'  # 红黄绿配色
                    )
                
                return summary_text, sales_fig, rating_fig, category_growth_fig
            
            trend_refresh_btn.click(
                generate_trend_analysis,
                inputs=[trend_platform, trend_category, trend_days],
                outputs=[trend_summary, sales_chart, rating_chart, category_growth_chart]
            )
        
        return gr.Tab("趋势分析")
    
    def _generate_summary_text(self, trend_data):
        """生成趋势概览文本"""
        if not trend_data:
            return "暂无趋势数据可供分析。"
        
        # 格式化时间
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 整体趋势描述
        overall_trend = trend_data.get('overall_trend', 'stable')
        trend_desc = {
            'rising': "上升",
            'falling': "下降",
            'stable': "稳定"
        }.get(overall_trend, "稳定")
        
        sales_growth = trend_data.get('overall_sales_growth', 0)
        growth_sign = "+" if sales_growth > 0 else ""
        
        rating_trend = trend_data.get('overall_rating_trend', 'stable')
        rating_desc = {
            'rising': "上升",
            'falling': "下降",
            'stable': "保持稳定"
        }.get(rating_trend, "保持稳定")
        
        # 构建概览文本
        summary = f"""
## 市场趋势分析报告
**生成时间:** {now}

### 整体趋势
- **销量变化:** {growth_sign}{sales_growth:.2f}% ({trend_desc})
- **评分趋势:** {rating_desc}
- **整体市场表现:** 市场总体呈{trend_desc}趋势

"""
        
        # 如果存在最快增长的类别
        if trend_data.get('fastest_growing_category'):
            fastest_cat = trend_data['fastest_growing_category']
            fastest_rate = trend_data['fastest_growing_rate']
            summary += f"""
### 类别表现
- **增长最快类别:** {fastest_cat} ({fastest_rate:.2f}%)
"""
        
        # 添加各类别趋势
        if trend_data.get('category_trends'):
            summary += "\n### 各类别趋势\n"
            
            for category, data in trend_data['category_trends'].items():
                cat_growth = data['sales_growth']
                cat_trend = data['rating_trend']
                
                growth_sign = "+" if cat_growth > 0 else ""
                rating_desc = {
                    'rising': "上升",
                    'falling': "下降",
                    'stable': "稳定"
                }.get(cat_trend, "稳定")
                
                summary += f"- **{category}:** 销量{growth_sign}{cat_growth:.2f}%, 评分{rating_desc}\n"
        
        return summary 