#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - Web UI应用

此文件实现系统的Web用户界面，使用Gradio库创建交互式分析界面。
功能包括：
- 构建热门商品排行榜界面
- 提供趋势分析可视化
- 支持跨平台数据对比
- 实现人工智能问答功能
- 数据可视化与报表生成

作者: AI助手
创建日期: 2023-06-01
"""

from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager, login_required
import gradio as gr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
import json
from io import BytesIO
import base64
from datetime import datetime
import plotly.express as px

app = Flask(__name__)
login_manager = LoginManager(app)

class WebInterface:
    """Web界面，提供用户交互"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        
    def setup_routes(self, app):
        @app.route('/')
        def home():
            return render_template('dashboard.html')
            
        @app.route('/api/trending')
        def trending_products():
            # 获取热门商品
            products = self.orchestrator.get_trending_products()
            return jsonify(products)
            
        @app.route('/api/ask', methods=['POST'])
        def ask_ai():
            """允许用户直接向AI提问"""
            question = request.json.get('question')
            answer = self.orchestrator.llm_service.answer_business_question(question)
            return jsonify({"answer": answer}) 

class GradioApp:
    """基于Gradio的Web应用"""
    
    def __init__(self, orchestrator, config):
        self.orchestrator = orchestrator
        self.config = config['ui']
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 设置默认值
        self.default_platform = self.config.get('default_platform')
        self.default_category = self.config.get('default_category')
        self.default_time_range = self.config.get('default_time_range', 'week')
        
        # 创建Gradio应用
        self.app = self._build_app()
    
    def _build_app(self):
        """构建Gradio应用"""
        with gr.Blocks(title=self.config.get('title', "电商热卖排行分析系统")) as app:
            gr.Markdown(f"# {self.config.get('title', '电商热卖排行分析系统')}")
            
            with gr.Tabs():
                # 热门商品排行榜
                with gr.Tab("热门商品排行榜"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            platform_selector = gr.Dropdown(
                                choices=["全部", "tiktok", "amazon", "shopee"],
                                value=self.default_platform or "全部",
                                label="平台"
                            )
                            category_selector = gr.Dropdown(
                                choices=["全部"],
                                value="全部",
                                label="类别"
                            )
                            time_range_selector = gr.Radio(
                                choices=["day", "week", "month", "year"],
                                value=self.default_time_range,
                                label="时间范围"
                            )
                            limit_slider = gr.Slider(
                                minimum=10, maximum=100, value=20, step=10,
                                label="显示数量"
                            )
                            refresh_btn = gr.Button("刷新数据")
                        
                        with gr.Column(scale=3):
                            products_table = gr.DataFrame(
                                headers=["排名", "商品ID", "商品名称", "平台", "类别", "价格", "销量", "评分", "评论数"],
                                label="热门商品排行"
                            )
                    
                    # 更新类别选择器
                    platform_selector.change(
                        fn=self._update_categories,
                        inputs=platform_selector,
                        outputs=category_selector
                    )
                    
                    # 刷新数据
                    refresh_params = [platform_selector, category_selector, time_range_selector, limit_slider]
                    refresh_btn.click(
                        fn=self._get_hot_products,
                        inputs=refresh_params,
                        outputs=products_table
                    )
                    
                    # 初始加载数据
                    for param in refresh_params:
                        param.change(
                            fn=self._get_hot_products,
                            inputs=refresh_params,
                            outputs=products_table
                        )
                
                # 类别排行榜
                with gr.Tab("类别排行榜"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            category_platform_selector = gr.Dropdown(
                                choices=["全部", "tiktok", "amazon", "shopee"],
                                value=self.default_platform or "全部",
                                label="平台"
                            )
                            category_limit_slider = gr.Slider(
                                minimum=5, maximum=50, value=10, step=5,
                                label="每个类别显示数量"
                            )
                            category_refresh_btn = gr.Button("刷新数据")
                        
                        with gr.Column(scale=3):
                            category_tabs = gr.Tabs()
                    
                    # 刷新类别排行数据
                    category_refresh_btn.click(
                        fn=self._get_category_rankings,
                        inputs=[category_platform_selector, category_limit_slider],
                        outputs=category_tabs
                    )
                
                # 趋势分析
                with gr.Tab("趋势分析"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            trend_platform_selector = gr.Dropdown(
                                choices=["全部", "tiktok", "amazon", "shopee"],
                                value=self.default_platform or "全部",
                                label="平台"
                            )
                            trend_days_slider = gr.Slider(
                                minimum=7, maximum=90, value=30, step=7,
                                label="分析天数"
                            )
                            trend_refresh_btn = gr.Button("生成趋势分析")
                        
                        with gr.Column(scale=3):
                            trend_summary = gr.Markdown()
                            
                            with gr.Tabs():
                                with gr.Tab("销售趋势"):
                                    sales_trend_plot = gr.Plot()
                                
                                with gr.Tab("类别趋势"):
                                    category_trend_plot = gr.Plot()
                                
                                with gr.Tab("价格趋势"):
                                    price_trend_plot = gr.Plot()
                    
                    # 生成趋势分析
                    trend_refresh_btn.click(
                        fn=self._generate_trend_analysis,
                        inputs=[trend_platform_selector, trend_days_slider],
                        outputs=[trend_summary, sales_trend_plot, category_trend_plot, price_trend_plot]
                    )
                
                # 性价比排行
                with gr.Tab("性价比排行"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            value_platform_selector = gr.Dropdown(
                                choices=["全部", "tiktok", "amazon", "shopee"],
                                value=self.default_platform or "全部",
                                label="平台"
                            )
                            value_category_selector = gr.Dropdown(
                                choices=["全部"],
                                value="全部",
                                label="类别"
                            )
                            value_limit_slider = gr.Slider(
                                minimum=10, maximum=50, value=20, step=5,
                                label="显示数量"
                            )
                            value_refresh_btn = gr.Button("刷新数据")
                        
                        with gr.Column(scale=3):
                            value_table = gr.DataFrame(
                                headers=["排名", "商品名称", "平台", "类别", "价格", "评分", "性价比得分"],
                                label="性价比排行"
                            )
                    
                    # 更新类别选择器
                    value_platform_selector.change(
                        fn=self._update_categories,
                        inputs=value_platform_selector,
                        outputs=value_category_selector
                    )
                    
                    # 刷新数据
                    value_refresh_params = [value_platform_selector, value_category_selector, value_limit_slider]
                    value_refresh_btn.click(
                        fn=self._get_value_ranking,
                        inputs=value_refresh_params,
                        outputs=value_table
                    )
                
                # 智能分析
                with gr.Tab("智能分析"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            analysis_platform_selector = gr.Dropdown(
                                choices=["全部", "tiktok", "amazon", "shopee"],
                                value=self.default_platform or "全部",
                                label="平台"
                            )
                            analysis_type_selector = gr.Radio(
                                choices=["热门属性分析", "价格区间分析", "评分分布分析", "关键词分析"],
                                value="热门属性分析",
                                label="分析类型"
                            )
                            analysis_refresh_btn = gr.Button("生成分析")
                        
                        with gr.Column(scale=3):
                            analysis_result = gr.JSON(label="分析结果")
                            analysis_plot = gr.Plot(label="可视化")
                    
                    # 生成分析
                    analysis_refresh_btn.click(
                        fn=self._generate_analysis,
                        inputs=[analysis_platform_selector, analysis_type_selector],
                        outputs=[analysis_result, analysis_plot]
                    )
                
                # AI问答
                with gr.Tab("AI问答"):
                    question_input = gr.Textbox(
                        lines=2,
                        placeholder="在这里输入您的问题，例如：'哪个类别的商品增长最快？'",
                        label="问题"
                    )
                    ask_btn = gr.Button("提问")
                    answer_output = gr.Markdown(label="回答")
                    
                    # 提问
                    ask_btn.click(
                        fn=self._ask_question,
                        inputs=question_input,
                        outputs=answer_output
                    )
            
            # 页脚
            gr.Markdown("### 基于大语言模型和智能Agent的电商数据分析系统")
            gr.Markdown(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return app
    
    def launch(self):
        """启动Gradio应用"""
        # 创建UI组件
        from ui.ranking_components import RankingComponents
        from ui.trend_components import TrendComponents
        from ui.comparison_components import ComparisonComponents
        
        ranking_components = RankingComponents(self.orchestrator)
        trend_components = TrendComponents(self.orchestrator)
        comparison_components = ComparisonComponents(self.orchestrator)
        
        # 创建界面
        with gr.Blocks(title=self.config['ui']['title'], theme=self.config['ui']['theme']) as app:
            gr.Markdown(f"# {self.config['ui']['title']}")
            
            # 创建主标签页
            with gr.Tabs():
                # 首页/概览标签页
                with gr.Tab("市场概览"):
                    self._create_overview_tab()
                
                # 添加排行榜标签页
                ranking_components.build_rankings_tab()
                
                # 添加趋势分析标签页
                trend_components.build_trends_tab()
                
                # 添加平台对比标签页
                comparison_components.build_comparison_tab()
                
                # 添加数据导出标签页
                with gr.Tab("数据导出"):
                    self._create_export_tab()
        
        # 启动应用
        app.launch(
            server_name="0.0.0.0",
            server_port=self.config['ui']['port'],
            share=False
        )
    
    def _create_overview_tab(self):
        """创建概览标签页"""
        with gr.Row():
            gr.Markdown("""
            ## 电商热卖排行分析系统
            
            本系统提供多平台电商热门商品数据分析，包括：
            
            - **热门排行** - 查看各平台热销商品排行榜
            - **趋势分析** - 分析商品销量和评分趋势
            - **平台对比** - 对比不同平台商品数据
            - **数据导出** - 导出分析数据和报告
            
            使用左侧标签页导航不同功能模块。
            """)
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 数据概览")
                
                refresh_btn = gr.Button("刷新数据")
                
                stats_md = gr.Markdown()
                
                def refresh_stats():
                    product_count = self.orchestrator.db.get_product_count()
                    platform_stats = self.orchestrator.db.get_platform_stats()
                    category_count = len(self.orchestrator.get_categories())
                    
                    platforms_str = ", ".join([f"{p}: {c}件商品" for p, c in platform_stats.items()])
                    
                    return f"""
                    - **总商品数**: {product_count}件
                    - **覆盖平台**: {len(platform_stats)}个 ({platforms_str})
                    - **商品类别**: {category_count}个
                    - **最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                    """
                
                refresh_btn.click(refresh_stats, outputs=stats_md)
            
            with gr.Column():
                gr.Markdown("### 热门类别")
                cat_chart = gr.Plot()
                
                def create_category_chart():
                    categories = self.orchestrator.get_categories()
                    counts = []
                    
                    for category in categories:
                        count = self.orchestrator.db.get_category_count(category)
                        counts.append(count)
                    
                    # 只显示前10个类别
                    if len(categories) > 10:
                        sorted_data = sorted(zip(categories, counts), key=lambda x: x[1], reverse=True)
                        categories = [x[0] for x in sorted_data[:10]]
                        counts = [x[1] for x in sorted_data[:10]]
                    
                    fig = px.bar(
                        x=categories,
                        y=counts,
                        labels={"x": "类别", "y": "商品数量"},
                        title="热门类别商品数量"
                    )
                    
                    return fig
                
                refresh_btn.click(create_category_chart, outputs=cat_chart)
    
    def _create_export_tab(self):
        """创建数据导出标签页"""
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 导出商品数据")
                
                export_platform = gr.Dropdown(
                    choices=["全部", "tiktok", "amazon", "shopee"],
                    value="全部",
                    label="平台"
                )
                
                export_category = gr.Dropdown(
                    choices=["全部"],
                    value="全部",
                    label="类别"
                )
                
                export_limit = gr.Slider(
                    minimum=10,
                    maximum=1000,
                    value=100,
                    step=10,
                    label="导出数量上限"
                )
                
                export_format = gr.Radio(
                    choices=["CSV", "Excel", "JSON"],
                    value="CSV",
                    label="导出格式"
                )
                
                export_btn = gr.Button("生成导出文件")
                
                export_result = gr.File(label="导出文件")
                
                # 平台变化时更新类别
                def update_categories(platform_val):
                    if platform_val == "全部":
                        categories = self.orchestrator.get_categories()
                    else:
                        categories = self.orchestrator.get_categories(platform=platform_val)
                    
                    return gr.Dropdown.update(choices=["全部"] + categories)
                
                export_platform.change(update_categories, inputs=export_platform, outputs=export_category)
                
                # 导出数据
                def export_data(platform, category, limit, format):
                    platform_arg = None if platform == "全部" else platform
                    category_arg = None if category == "全部" else category
                    
                    # 获取数据
                    products = self.orchestrator.get_products(
                        platform=platform_arg,
                        category=category_arg,
                        limit=limit
                    )
                    
                    if not products:
                        return None
                    
                    df = pd.DataFrame(products)
                    
                    # 生成文件名
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    platform_str = platform if platform != "全部" else "all"
                    category_str = category if category != "全部" else "all"
                    filename = f"products_{platform_str}_{category_str}_{timestamp}"
                    
                    # 根据格式导出
                    if format == "CSV":
                        output_path = f"{filename}.csv"
                        df.to_csv(output_path, index=False, encoding='utf-8-sig')
                        return output_path
                    elif format == "Excel":
                        output_path = f"{filename}.xlsx"
                        df.to_excel(output_path, index=False)
                        return output_path
                    elif format == "JSON":
                        output_path = f"{filename}.json"
                        df.to_json(output_path, orient='records', force_ascii=False)
                        return output_path
                    
                    return None
                
                export_btn.click(
                    export_data,
                    inputs=[export_platform, export_category, export_limit, export_format],
                    outputs=export_result
                )
    
    def _update_categories(self, platform):
        """更新类别选择器"""
        try:
            categories = self.orchestrator.get_categories(platform if platform != "全部" else None)
            return gr.Dropdown.update(choices=["全部"] + categories)
        except Exception as e:
            self.logger.error(f"Error updating categories: {e}")
            return gr.Dropdown.update(choices=["全部"])
    
    def _get_hot_products(self, platform, category, time_range, limit):
        """获取热门商品数据"""
        try:
            # 处理参数
            platform = None if platform == "全部" else platform
            category = None if category == "全部" else category
            
            # 获取数据
            products = self.orchestrator.get_hot_products(
                platform=platform,
                category=category,
                time_range=time_range,
                limit=int(limit)
            )
            
            # 转换为DataFrame
            if products:
                df = pd.DataFrame(products)
                # 选择要显示的列
                columns = ['rank', 'product_id', 'name', 'platform', 'category', 'price', 'sales_volume', 'rating', 'reviews_count']
                # 确保所有列都存在
                for col in columns:
                    if col not in df.columns:
                        df[col] = None
                return df[columns]
            else:
                return pd.DataFrame(columns=['rank', 'product_id', 'name', 'platform', 'category', 'price', 'sales_volume', 'rating', 'reviews_count'])
        except Exception as e:
            self.logger.error(f"Error getting hot products: {e}")
            return pd.DataFrame(columns=['rank', 'product_id', 'name', 'platform', 'category', 'price', 'sales_volume', 'rating', 'reviews_count'])
    
    def _get_category_rankings(self, platform, limit_per_category):
        """获取各类别排行榜"""
        try:
            # 处理参数
            platform = None if platform == "全部" else platform
            
            # 获取数据
            category_rankings = self.orchestrator.get_category_rankings(
                platform=platform,
                limit_per_category=int(limit_per_category)
            )
            
            # 创建标签页
            tabs = []
            
            if not category_rankings:
                return gr.Tabs()
            
            # 为每个类别创建标签页
            for category, products in category_rankings.items():
                df = pd.DataFrame(products)
                # 选择要显示的列
                columns = ['rank', 'name', 'platform', 'price', 'sales_volume', 'rating', 'reviews_count']
                # 确保所有列都存在
                for col in columns:
                    if col not in df.columns:
                        df[col] = None
                
                # 创建标签页并添加DataFrame
                tab = gr.Tab(label=category)
                with tab:
                    gr.DataFrame(df[columns])
                tabs.append(tab)
            
            return gr.Tabs(*tabs)
        except Exception as e:
            self.logger.error(f"Error getting category rankings: {e}")
            return gr.Tabs()
    
    def _generate_trend_analysis(self, platform, days):
        """生成趋势分析"""
        try:
            # 处理参数
            platform = None if platform == "全部" else platform
            
            # 获取趋势分析
            trend_summary = self.orchestrator.get_trend_summary(platform=platform, days=int(days))
            
            if not trend_summary:
                return "无法生成趋势分析。", None, None, None
            
            # 提取数据
            summary_text = trend_summary.get('summary_text', "无法生成趋势摘要。")
            sales_trend = trend_summary.get('sales_trend', {})
            category_trend = trend_summary.get('category_trend', {})
            price_trend = trend_summary.get('price_trend', {})
            
            # 获取图表
            sales_plot = self._get_plot_from_base64(sales_trend.get('chart'))
            category_plot = self._get_plot_from_base64(category_trend.get('chart'))
            price_plot = self._get_plot_from_base64(price_trend.get('chart'))
            
            return summary_text, sales_plot, category_plot, price_plot
        except Exception as e:
            self.logger.error(f"Error generating trend analysis: {e}")
            return "生成趋势分析时发生错误。", None, None, None
    
    def _get_value_ranking(self, platform, category, limit):
        """获取性价比排行榜"""
        try:
            # 处理参数
            platform = None if platform == "全部" else platform
            category = None if category == "全部" else category
            
            # 获取数据
            products = self.orchestrator.get_price_performance_ranking(
                platform=platform,
                category=category,
                limit=int(limit)
            )
            
            # 转换为DataFrame
            if products:
                df = pd.DataFrame(products)
                # 选择要显示的列
                columns = ['rank', 'name', 'platform', 'category', 'price', 'rating', 'value_score']
                # 确保所有列都存在
                for col in columns:
                    if col not in df.columns:
                        df[col] = None
                return df[columns]
            else:
                return pd.DataFrame(columns=['rank', 'name', 'platform', 'category', 'price', 'rating', 'value_score'])
        except Exception as e:
            self.logger.error(f"Error getting value ranking: {e}")
            return pd.DataFrame(columns=['rank', 'name', 'platform', 'category', 'price', 'rating', 'value_score'])
    
    def _generate_analysis(self, platform, analysis_type):
        """生成智能分析"""
        try:
            # 处理参数
            platform = None if platform == "全部" else platform
            
            # 根据分析类型选择不同的分析方法
            if analysis_type == "热门属性分析":
                analysis_result = self.orchestrator.analyze_popular_attributes(platform=platform)
                plot = self._create_bar_chart(
                    analysis_result.get('top_attributes', {}),
                    title="热门商品属性分布",
                    xlabel="属性值",
                    ylabel="出现频率"
                )
            elif analysis_type == "价格区间分析":
                analysis_result = self.orchestrator.analyze_price_distribution(platform=platform)
                plot = self._create_histogram(
                    analysis_result.get('price_data', []),
                    bins=10,
                    title="商品价格分布",
                    xlabel="价格区间",
                    ylabel="商品数量"
                )
            elif analysis_type == "评分分布分析":
                analysis_result = self.orchestrator.analyze_rating_distribution(platform=platform)
                plot = self._create_bar_chart(
                    analysis_result.get('rating_distribution', {}),
                    title="商品评分分布",
                    xlabel="评分",
                    ylabel="商品数量"
                )
            elif analysis_type == "关键词分析":
                analysis_result = self.orchestrator.analyze_keywords(platform=platform)
                plot = self._create_bar_chart(
                    analysis_result.get('keyword_frequency', {}),
                    title="热门关键词分布",
                    xlabel="关键词",
                    ylabel="出现频率",
                    horizontal=True
                )
            else:
                return {"error": "未知的分析类型"}, None
            
            return analysis_result, plot
        except Exception as e:
            self.logger.error(f"Error generating analysis: {e}")
            return {"error": f"生成分析时发生错误: {str(e)}"}, None
    
    def _ask_question(self, question):
        """向AI提问"""
        try:
            if not question or question.strip() == "":
                return "请输入您的问题。"
            
            # 获取回答
            answer = self.orchestrator.ask_question(question)
            return answer
        except Exception as e:
            self.logger.error(f"Error asking question: {e}")
            return f"提问时发生错误: {str(e)}"
    
    def _get_plot_from_base64(self, base64_str):
        """从Base64字符串获取图表"""
        if not base64_str:
            return None
        
        try:
            # 解码Base64数据
            image_data = base64.b64decode(base64_str)
            # 创建BytesIO对象
            image_stream = BytesIO(image_data)
            # 加载图像
            img = plt.imread(image_stream)
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.imshow(img)
            ax.axis('off')
            
            return fig
        except Exception as e:
            self.logger.error(f"Error creating plot from base64: {e}")
            return None
    
    def _create_bar_chart(self, data, title="", xlabel="", ylabel="", horizontal=False):
        """创建柱状图"""
        if not data:
            return None
        
        try:
            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 获取数据
            labels = list(data.keys())
            values = list(data.values())
            
            # 限制显示的项目数量
            if len(labels) > 15:
                # 排序并只保留前15项
                sorted_data = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
                labels = [item[0] for item in sorted_data[:15]]
                values = [item[1] for item in sorted_data[:15]]
            
            # 水平柱状图或垂直柱状图
            if horizontal:
                ax.barh(labels, values)
                ax.set_xlabel(ylabel)
                ax.set_ylabel(xlabel)
            else:
                ax.bar(labels, values)
                ax.set_xlabel(xlabel)
                ax.set_ylabel(ylabel)
            
            # 设置标题
            ax.set_title(title)
            
            # 自动调整布局
            plt.tight_layout()
            
            return fig
        except Exception as e:
            self.logger.error(f"Error creating bar chart: {e}")
            return None
    
    def _create_histogram(self, data, bins=10, title="", xlabel="", ylabel=""):
        """创建直方图"""
        if not data:
            return None
        
        try:
            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 绘制直方图
            ax.hist(data, bins=bins)
            
            # 设置标签和标题
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            
            # 自动调整布局
            plt.tight_layout()
            
            return fig
        except Exception as e:
            self.logger.error(f"Error creating histogram: {e}")
            return None 