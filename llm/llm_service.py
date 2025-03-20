#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - LLM服务

此文件实现与大型语言模型的交互功能。
功能包括：
- 对接OpenAI、Azure等LLM提供商API
- 处理商品描述增强
- 回答用户业务问题
- 提供数据解释和见解
- 管理API密钥和请求限制

作者: AI助手
创建日期: 2023-06-01
"""

from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import logging
import openai
import re
import time

class LLMService:
    """大模型服务，封装与LLM的交互"""
    
    def __init__(self, config):
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.api_key = config.get("api_key")
        
        # 设置API密钥
        if self.provider == "openai":
            openai.api_key = self.api_key
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def generate_description(self, product_name, category=None):
        """根据产品名称生成描述"""
        try:
            prompt = f"你是一位电商产品描述专家。请为以下产品生成一段吸引人的描述，突出其主要特点和优势。产品名称: {product_name}"
            
            if category:
                prompt += f"\n产品类别: {category}"
            
            response = self._call_llm(prompt)
            return response
        except Exception as e:
            self.logger.error(f"Error generating description: {e}")
            return f"高品质的{product_name}，适合各种场景使用。"
    
    def enhance_description(self, description):
        """增强产品描述"""
        if not description:
            return ""
            
        try:
            prompt = f"""你是一位电商文案专家。请优化以下产品描述，使其更加吸引人、更有说服力，并突出产品的关键卖点:

{description}

请保持描述的准确性，但使其更具营销效果。不要添加虚假信息。"""
            
            response = self._call_llm(prompt)
            return response
        except Exception as e:
            self.logger.error(f"Error enhancing description: {e}")
            return description
    
    def analyze_sentiment(self, reviews):
        """分析评论情感"""
        if not reviews:
            return None
            
        try:
            reviews_text = "\n".join([f"- {review}" for review in reviews])
            
            prompt = f"""请分析以下产品评论，并给出一个情感得分（0-100分），其中0表示极度负面，100表示极度正面。
            
评论:
{reviews_text}

只需要返回一个0-100的数字作为情感得分，不需要其他文字。"""
            
            response = self._call_llm(prompt)
            
            # 尝试从回答中提取数字
            score_match = re.search(r'(\d+)', response)
            if score_match:
                score = int(score_match.group(1))
                # 限制分数范围
                score = max(0, min(score, 100))
                return score
            else:
                return 50  # 默认中性
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return 50  # 默认中性
    
    def extract_keywords(self, text):
        """从文本中提取关键词"""
        if not text:
            return []
            
        try:
            prompt = f"""你是一位SEO优化专家。请从以下文本中提取5-10个最重要的关键词或短语，这些关键词应该能够概括产品特点并有助于SEO优化:

{text}

请直接列出这些关键词，一行一个，不需要其他说明。"""
            
            response = self._call_llm(prompt)
            
            # 处理回答，提取关键词列表
            keywords = [keyword.strip() for keyword in response.split('\n') if keyword.strip()]
            
            return keywords
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []
    
    def analyze_market_trends(self, products_data):
        """分析市场趋势"""
        if not products_data:
            return "没有足够的数据进行市场趋势分析。"
            
        try:
            # 准备产品数据摘要
            summary = []
            
            # 限制数据量
            products_sample = products_data[:20] if len(products_data) > 20 else products_data
            
            for product in products_sample:
                summary.append(f"- 商品：{product.get('name')}, 类别：{product.get('category')}, 价格：{product.get('price')}, 销量：{product.get('sales_volume')}, 评分：{product.get('rating')}")
            
            products_summary = "\n".join(summary)
            
            prompt = f"""你是一位电商数据分析专家。请根据以下热卖商品数据，分析当前市场趋势和消费者偏好。

商品数据:
{products_summary}

请提供以下分析：
1. 整体市场趋势
2. 热门品类分析
3. 价格区间分析
4. 消费者偏好特征
5. 行业机会点

请给出详细但简洁的分析。"""
            
            response = self._call_llm(prompt)
            return response
        except Exception as e:
            self.logger.error(f"Error analyzing market trends: {e}")
            return "无法完成市场趋势分析，请稍后再试。"
    
    def predict_future_performance(self, product_id, historical_data):
        """预测商品未来表现"""
        if not historical_data:
            return "没有足够的历史数据进行预测。"
            
        try:
            # 准备历史数据摘要
            data_summary = []
            
            for record in historical_data:
                data_summary.append(f"- 日期：{record.get('date')}, 价格：{record.get('price')}, 销量：{record.get('sales_volume')}, 评分：{record.get('rating')}")
            
            history_summary = "\n".join(data_summary)
            
            prompt = f"""你是一位电商预测分析专家。请根据以下商品的历史数据，预测其未来的销售趋势和表现。

商品ID: {product_id}
历史数据:
{history_summary}

请提供以下预测分析：
1. 未来30天的销售趋势预测
2. 价格变动建议
3. 潜在风险因素
4. 机会点

请给出详细但简洁的分析。"""
            
            response = self._call_llm(prompt)
            return response
        except Exception as e:
            self.logger.error(f"Error predicting future performance: {e}")
            return "无法完成未来表现预测，请稍后再试。"
    
    def analyze_competitors(self, product_data, competitor_data):
        """分析竞争对手"""
        if not product_data or not competitor_data:
            return "没有足够的数据进行竞争对手分析。"
            
        try:
            # 准备数据摘要
            product_summary = f"- 本商品：{product_data.get('name')}, 价格：{product_data.get('price')}, 销量：{product_data.get('sales_volume')}, 评分：{product_data.get('rating')}"
            
            competitor_summary = []
            for competitor in competitor_data:
                competitor_summary.append(f"- 竞品：{competitor.get('name')}, 价格：{competitor.get('price')}, 销量：{competitor.get('sales_volume')}, 评分：{competitor.get('rating')}")
            
            competitors = "\n".join(competitor_summary)
            
            prompt = f"""你是一位电商竞争分析专家。请根据以下数据，分析本商品与竞争对手的比较情况。

本商品:
{product_summary}

竞争对手:
{competitors}

请提供以下分析：
1. 价格竞争力分析
2. 销量对比分析
3. 评分和用户满意度对比
4. 本商品的优势和劣势
5. 改进建议

请给出详细但简洁的分析。"""
            
            response = self._call_llm(prompt)
            return response
        except Exception as e:
            self.logger.error(f"Error analyzing competitors: {e}")
            return "无法完成竞争对手分析，请稍后再试。"
    
    def answer_business_question(self, question):
        """回答业务问题"""
        if not question:
            return "请提出您的问题。"
            
        try:
            prompt = f"""你是一位电商数据分析和市场专家，擅长回答关于电商平台、产品趋势、市场分析等相关问题。请回答以下问题：

问题: {question}

请提供详细、准确、有洞察力的回答，如果可能的话引用一些行业数据或趋势。如果问题超出你的知识范围，请诚实说明。"""
            
            response = self._call_llm(prompt)
            return response
        except Exception as e:
            self.logger.error(f"Error answering business question: {e}")
            return "很抱歉，我无法处理您的问题，请稍后再试或换一种表述方式。"
    
    def personalized_recommendations(self, user_profile, user_history, products):
        """生成个性化推荐"""
        if not products:
            return []
            
        try:
            # 准备用户画像摘要
            profile_summary = ", ".join([f"{k}: {v}" for k, v in user_profile.items() if v])
            
            # 准备用户历史摘要
            history_summary = []
            for item in user_history[:10]:  # 限制数量
                history_summary.append(f"- 商品：{item.get('name')}, 价格：{item.get('price')}, 评分：{item.get('rating')}")
            
            history = "\n".join(history_summary)
            
            # 准备候选商品摘要
            product_summary = []
            for idx, product in enumerate(products[:30]):  # 限制数量
                product_summary.append(f"{idx+1}. 商品：{product.get('name')}, 类别：{product.get('category')}, 价格：{product.get('price')}, 评分：{product.get('rating')}")
            
            candidates = "\n".join(product_summary)
            
            prompt = f"""你是一位电商推荐系统专家。请根据用户画像和购买历史，从候选商品中推荐最适合该用户的5个商品。

用户画像:
{profile_summary}

购买历史:
{history}

候选商品:
{candidates}

请返回你推荐的5个商品的编号（如1,3,5,7,9），并简要解释每个推荐的理由。
格式为：
推荐商品：[商品编号列表]
推荐理由：
1. [商品1]理由
2. [商品2]理由
...
"""
            
            response = self._call_llm(prompt)
            
            # 解析回答，提取推荐商品
            recommended_indices = []
            pattern = r'推荐商品：\[?(\d+(?:,\s*\d+)*)\]?'
            indices_match = re.search(pattern, response)
            
            if indices_match:
                indices_str = indices_match.group(1)
                indices = [int(idx.strip()) for idx in indices_str.split(',')]
                recommended_indices = indices
            
            # 获取推荐商品
            recommendations = []
            for idx in recommended_indices:
                if 1 <= idx <= len(products):
                    product = products[idx-1]
                    recommendations.append({
                        'product': product,
                        'recommendation_reason': f"根据您的偏好和购买历史，我们推荐这款{product.get('name')}。"
                    })
            
            return recommendations
        except Exception as e:
            self.logger.error(f"Error generating personalized recommendations: {e}")
            return []
    
    def generate_recommendation_explanation(self, recommendation_id):
        """生成推荐解释"""
        try:
            prompt = f"""你是一位电商推荐系统专家。请为ID为{recommendation_id}的推荐商品生成一段解释，说明为什么向用户推荐该商品。

这段解释应该：
1. 简明扼要（100字左右）
2. 提到商品的主要优点
3. 与用户的偏好或浏览历史相关联
4. 有说服力但不夸大

请直接给出解释文本，不需要其他内容。"""
            
            response = self._call_llm(prompt)
            return response
        except Exception as e:
            self.logger.error(f"Error generating recommendation explanation: {e}")
            return "根据您的浏览历史和偏好，我们认为这款商品可能符合您的需求。"
    
    def _call_llm(self, prompt, max_retries=3):
        """调用大模型API"""
        retries = 0
        
        while retries < max_retries:
            try:
                if self.provider == "openai":
                    # OpenAI API调用
                    response = openai.ChatCompletion.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "你是一位专业的电商数据分析和产品专家。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    return response.choices[0].message.content.strip()
                else:
                    raise ValueError(f"Unsupported LLM provider: {self.provider}")
                
            except Exception as e:
                retries += 1
                wait_time = 2 ** retries  # 指数退避策略
                self.logger.error(f"LLM API call failed: {e}. Retrying in {wait_time}s... ({retries}/{max_retries})")
                time.sleep(wait_time)
        
        # 所有重试都失败
        raise Exception(f"Failed to call LLM API after {max_retries} retries") 