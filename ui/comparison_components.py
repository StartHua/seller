#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 平台对比UI组件

此文件实现跨平台商品对比相关的UI组件，使用Gradio库。
功能包括：
- 跨平台销量对比
- 跨平台价格区间对比
- 跨平台评分对比
- 对比数据表格展示

作者: AI助手
创建日期: 2023-06-01
"""

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class ComparisonComponents:
    """跨平台商品对比UI组件"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    def build_comparison_tab(self):
        """构建平台对比标签页"""
        with gr.Tab("平台对比"):
            with gr.Row():
                category = gr.Dropdown(
                    choices=["全部"] + self.orchestrator.get_categories(),
                    value="全部",
                    label="商品类别"
                )
                limit = gr.Slider(
                    minimum=5,
                    maximum=30,
                    value=10,
                    step=5,
                    label="每平台商品数量"
                )
                refresh_btn = gr.Button("刷新对比")
            
            with gr.Row():
                sales_comparison = gr.Plot(label="销量对比")
                price_comparison = gr.Plot(label="价格区间对比")
            
            with gr.Row():
                ratings_comparison = gr.Plot(label="评分对比")
            
            with gr.Row():
                platform_tables = gr.Tabs()
            
            # 生成平台对比
            def generate_platform_comparison(category_val, limit_val):
                category_arg = None if category_val == "全部" else category_val
                
                # 获取跨平台商品对比数据
                comparison_data = self.orchestrator.get_cross_platform_comparison(
                    category=category_arg,
                    limit=limit_val
                )
                
                if not comparison_data:
                    return None, None, None, gr.Tabs(visible=False)
                
                # 准备销量对比图
                sales_fig = self._create_sales_comparison(comparison_data)
                
                # 准备价格对比图
                price_fig = self._create_price_comparison(comparison_data)
                
                # 准备评分对比图
                ratings_fig = self._create_ratings_comparison(comparison_data)
                
                # 创建平台数据表格标签页
                tabs = []
                for platform, products in comparison_data.items():
                    df = pd.DataFrame(products)
                    
                    # 选择要显示的列
                    display_df = df[['rank', 'name', 'price', 'sales_volume', 'rating', 'reviews_count']]
                    
                    # 创建表格
                    with gr.Tab(platform.title()):
                        gr.DataFrame(
                            value=display_df,
                            headers=["排名", "商品名称", "价格", "销量", "评分", "评论数"],
                            label=f"{platform.title()}热门商品"
                        )
                
                return sales_fig, price_fig, ratings_fig, gr.Tabs(visible=True)
            
            refresh_btn.click(
                generate_platform_comparison,
                inputs=[category, limit],
                outputs=[sales_comparison, price_comparison, ratings_comparison, platform_tables]
            )
        
        return gr.Tab("平台对比")
    
    def _create_sales_comparison(self, data):
        """创建销量对比图表"""
        platforms = []
        avg_sales = []
        max_sales = []
        
        for platform, products in data.items():
            if not products:
                continue
                
            df = pd.DataFrame(products)
            platforms.append(platform.title())
            avg_sales.append(df['sales_volume'].mean())
            max_sales.append(df['sales_volume'].max())
        
        # 创建图表
        fig = make_subplots(rows=1, cols=1)
        
        fig.add_trace(
            go.Bar(
                x=platforms,
                y=avg_sales,
                name="平均销量",
                marker_color='lightblue'
            )
        )
        
        fig.add_trace(
            go.Bar(
                x=platforms,
                y=max_sales,
                name="最高销量",
                marker_color='darkblue'
            )
        )
        
        fig.update_layout(
            title="平台销量对比",
            xaxis_title="平台",
            yaxis_title="销量",
            barmode='group',
            height=400
        )
        
        return fig
    
    def _create_price_comparison(self, data):
        """创建价格对比图表"""
        all_data = []
        
        for platform, products in data.items():
            if not products:
                continue
                
            df = pd.DataFrame(products)
            for _, row in df.iterrows():
                all_data.append({
                    'platform': platform.title(),
                    'price': row['price']
                })
        
        df = pd.DataFrame(all_data)
        
        # 创建箱型图
        fig = px.box(
            df,
            x='platform',
            y='price',
            color='platform',
            title="平台价格分布",
            labels={'platform': '平台', 'price': '价格'}
        )
        
        return fig
    
    def _create_ratings_comparison(self, data):
        """创建评分对比图表"""
        platforms = []
        avg_ratings = []
        review_counts = []
        
        for platform, products in data.items():
            if not products:
                continue
                
            df = pd.DataFrame(products)
            platforms.append(platform.title())
            avg_ratings.append(df['rating'].mean())
            review_counts.append(df['reviews_count'].sum())
        
        # 创建复合图表
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 添加评分条形图
        fig.add_trace(
            go.Bar(
                x=platforms,
                y=avg_ratings,
                name="平均评分",
                marker_color='green'
            ),
            secondary_y=False
        )
        
        # 添加评论数线图
        fig.add_trace(
            go.Scatter(
                x=platforms,
                y=review_counts,
                name="评论总数",
                mode="lines+markers",
                marker=dict(size=10),
                line=dict(width=4, color='orange')
            ),
            secondary_y=True
        )
        
        # 更新布局
        fig.update_layout(
            title="平台评分与评论数对比",
            xaxis_title="平台",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 更新Y轴标题
        fig.update_yaxes(title_text="平均评分", secondary_y=False, range=[0, 5])
        fig.update_yaxes(title_text="评论总数", secondary_y=True)
        
        return fig 