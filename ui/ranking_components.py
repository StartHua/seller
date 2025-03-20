#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 排行榜UI组件

此文件实现排行榜相关的UI组件，使用Gradio库。
功能包括：
- 热门商品排行界面
- 上升商品排行界面
- 类别排行界面
- 价格区间排行界面

作者: AI助手
创建日期: 2023-06-01
"""

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class RankingComponents:
    """排行榜UI组件"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    def build_rankings_tab(self):
        """构建排行榜标签页"""
        with gr.Tab("热门排行"):
            with gr.Row():
                platform = gr.Dropdown(
                    choices=["全部", "tiktok", "amazon", "shopee"],
                    value="全部",
                    label="电商平台"
                )
                category = gr.Dropdown(
                    choices=["全部"],
                    value="全部",
                    label="商品类别"
                )
                time_range = gr.Radio(
                    choices=["日", "周", "月"],
                    value="周",
                    label="时间范围"
                )
            
            with gr.Row():
                refresh_btn = gr.Button("刷新数据")
            
            with gr.Row():
                ranking_table = gr.DataFrame(
                    headers=["排名", "商品名称", "平台", "类别", "价格", "销量", "评分", "评论数"],
                    label="热门商品排行"
                )
            
            with gr.Row():
                ranking_chart = gr.Plot(label="销量排行图表")
            
            # 处理平台和类别联动
            def update_categories(platform_val):
                if platform_val == "全部":
                    categories = self.orchestrator.get_categories()
                else:
                    categories = self.orchestrator.get_categories(platform=platform_val)
                
                return gr.Dropdown.update(choices=["全部"] + categories)
            
            platform.change(update_categories, inputs=platform, outputs=category)
            
            # 生成排行榜
            def generate_rankings(platform_val, category_val, time_range_val):
                platform_arg = None if platform_val == "全部" else platform_val
                category_arg = None if category_val == "全部" else category_val
                
                # 时间范围映射
                time_map = {"日": "day", "周": "week", "月": "month"}
                time_arg = time_map.get(time_range_val, "week")
                
                # 获取热门商品
                products = self.orchestrator.get_hot_products(
                    platform=platform_arg,
                    category=category_arg,
                    time_range=time_arg,
                    limit=50
                )
                
                # 转换为表格数据
                if products:
                    df = pd.DataFrame(products)
                    table_data = df[['rank', 'name', 'platform', 'category', 'price', 'sales_volume', 'rating', 'reviews_count']]
                    
                    # 创建图表
                    chart_df = df.sort_values('sales_volume', ascending=True).tail(20)  # 取销量最高的20个
                    fig = px.bar(
                        chart_df,
                        x='sales_volume',
                        y='name',
                        color='platform',
                        title="热门商品销量排行",
                        labels={'sales_volume': '销量', 'name': '商品名称'},
                        orientation='h'
                    )
                    
                    return table_data, fig
                
                return None, None
            
            refresh_btn.click(
                generate_rankings,
                inputs=[platform, category, time_range],
                outputs=[ranking_table, ranking_chart]
            )
            
        with gr.Tab("上升榜"):
            with gr.Row():
                rising_platform = gr.Dropdown(
                    choices=["全部", "tiktok", "amazon", "shopee"],
                    value="全部",
                    label="电商平台"
                )
                rising_category = gr.Dropdown(
                    choices=["全部"],
                    value="全部",
                    label="商品类别"
                )
                rising_days = gr.Slider(
                    minimum=1,
                    maximum=30,
                    value=7,
                    step=1,
                    label="天数"
                )
            
            with gr.Row():
                rising_refresh_btn = gr.Button("刷新数据")
            
            with gr.Row():
                rising_table = gr.DataFrame(
                    headers=["排名", "商品名称", "平台", "类别", "价格", "增长率(%)", "当前销量"],
                    label="上升最快商品"
                )
            
            with gr.Row():
                rising_chart = gr.Plot(label="增长率图表")
            
            # 处理平台和类别联动
            rising_platform.change(update_categories, inputs=rising_platform, outputs=rising_category)
            
            # 生成上升榜
            def generate_rising_rankings(platform_val, category_val, days):
                platform_arg = None if platform_val == "全部" else platform_val
                category_arg = None if category_val == "全部" else category_val
                
                # 获取上升最快的商品
                products = self.orchestrator.get_rising_products(
                    platform=platform_arg,
                    category=category_arg,
                    days=days,
                    limit=30
                )
                
                # 转换为表格数据
                if products:
                    df = pd.DataFrame(products)
                    table_data = df[['rank', 'name', 'platform', 'category', 'price', 'growth_rate', 'sales_volume']]
                    
                    # 创建图表
                    chart_df = df.sort_values('growth_rate', ascending=True).tail(15)  # 取增长率最高的15个
                    fig = px.bar(
                        chart_df,
                        x='growth_rate',
                        y='name',
                        color='platform',
                        title="商品增长率排行",
                        labels={'growth_rate': '增长率(%)', 'name': '商品名称'},
                        orientation='h'
                    )
                    
                    return table_data, fig
                
                return None, None
            
            rising_refresh_btn.click(
                generate_rising_rankings,
                inputs=[rising_platform, rising_category, rising_days],
                outputs=[rising_table, rising_chart]
            )
        
        with gr.Tab("类别排行"):
            with gr.Row():
                category_platform = gr.Dropdown(
                    choices=["全部", "tiktok", "amazon", "shopee"],
                    value="全部",
                    label="电商平台"
                )
                limit_per_category = gr.Slider(
                    minimum=5,
                    maximum=50,
                    value=10,
                    step=5,
                    label="每类显示商品数"
                )
            
            with gr.Row():
                category_refresh_btn = gr.Button("刷新数据")
            
            with gr.Row():
                category_tabs = gr.Tabs()
            
            # 生成类别排行榜
            def generate_category_rankings(platform_val, limit):
                platform_arg = None if platform_val == "全部" else platform_val
                
                # 获取类别排行
                category_rankings = self.orchestrator.get_category_rankings(
                    platform=platform_arg,
                    limit_per_category=limit
                )
                
                if not category_rankings:
                    return gr.Tabs(visible=False)
                
                # 为每个类别创建标签页
                tabs = []
                for category, products in category_rankings.items():
                    df = pd.DataFrame(products)
                    
                    # 选择要显示的列
                    display_df = df[['rank', 'name', 'platform', 'price', 'sales_volume', 'rating']]
                    
                    # 创建表格
                    with gr.Tab(category):
                        gr.DataFrame(
                            value=display_df,
                            headers=["排名", "商品名称", "平台", "价格", "销量", "评分"],
                            label=f"{category}热门商品"
                        )
                
                return gr.Tabs(visible=True)
            
            category_refresh_btn.click(
                generate_category_rankings,
                inputs=[category_platform, limit_per_category],
                outputs=[category_tabs]
            )
        
        return gr.Tabs() 