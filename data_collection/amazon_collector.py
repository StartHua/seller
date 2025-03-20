#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 亚马逊数据采集器

此文件实现亚马逊电商平台的数据采集功能。
功能包括：
- 采集亚马逊热门商品数据
- 解析商品详情页面
- 提取销量、评分和评论数据
- 处理亚马逊特有的数据格式
- 规避反爬虫机制

作者: AI助手
创建日期: 2023-06-01
"""

from .base_collector import BaseCollector
import time
from bs4 import BeautifulSoup
import re

class AmazonCollector(BaseCollector):
    """亚马逊数据采集器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.base_url = "https://www.amazon.com"
        
        # 亚马逊反爬虫机制很强，需要设置更加真实的UA
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        })
    
    def get_hot_products(self, category=None, limit=None):
        """获取亚马逊热门商品"""
        if not limit:
            limit = self.config.get("default_limit", 100)
            
        # 构建URL
        if category:
            category_path = self._get_category_path(category)
            url = f"{self.base_url}/gp/bestsellers/{category_path}/ref=zg_bs_nav_0"
        else:
            url = f"{self.base_url}/gp/bestsellers/ref=zg_bs_nav_0"
        
        try:
            # 获取网页内容
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找到所有商品元素
            product_elements = soup.select('.zg-item-immersion')
            
            products = []
            count = 0
            
            # 处理每个商品
            for element in product_elements:
                if count >= limit:
                    break
                    
                try:
                    # 提取商品ID
                    link_element = element.select_one('a[href*="/dp/"]')
                    if not link_element:
                        continue
                        
                    # 解析ASIN (Amazon标准识别号)
                    product_url = link_element.get('href', '')
                    asin_match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
                    if not asin_match:
                        continue
                        
                    product_id = asin_match.group(1)
                    
                    # 获取商品详情
                    product_detail = self.get_product_details(product_id)
                    if product_detail:
                        products.append(product_detail)
                        count += 1
                
                except Exception as e:
                    self.logger.warning(f"Error processing product element: {e}")
                    continue
            
            self.logger.info(f"Collected {len(products)} products from Amazon")
            return products
            
        except Exception as e:
            self.logger.error(f"Failed to collect Amazon hot products: {e}")
            return []
    
    def _get_category_path(self, category_name):
        """获取类别路径"""
        # 亚马逊类别映射 (简化版)
        category_map = {
            "electronics": "electronics",
            "computers": "computers",
            "books": "books",
            "home": "home-garden",
            "kitchen": "kitchen",
            "toys": "toys-games",
            "beauty": "beauty",
            "fashion": "fashion",
            "health": "hpc",
            "sports": "sporting-goods"
        }
        
        # 查找匹配的类别
        normalized_category = category_name.lower().strip()
        for key, value in category_map.items():
            if key in normalized_category:
                return value
        
        # 默认返回所有类别
        return ""
    
    def get_product_details(self, product_id):
        """获取商品详情"""
        url = f"{self.base_url}/dp/{product_id}/ref=cm_sw_r_cp_api_glt_i_XXX"
        
        try:
            # 随机延迟以避免被封IP
            import random
            time.sleep(random.uniform(1, 3))
            
            # 获取网页内容
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取商品名称
            name_element = soup.select_one('#productTitle')
            name = name_element.text.strip() if name_element else "Unknown Product"
            
            # 提取价格
            price_element = soup.select_one('.a-price .a-offscreen')
            price_text = price_element.text.strip() if price_element else "$0.00"
            # 从价格文本中提取数字
            price = self._extract_price(price_text)
            
            # 提取评分
            rating_element = soup.select_one('#acrPopover .a-icon-alt')
            rating_text = rating_element.text.strip() if rating_element else "0 out of 5 stars"
            rating = self._extract_rating(rating_text)
            
            # 提取评论数
            reviews_element = soup.select_one('#acrCustomerReviewText')
            reviews_text = reviews_element.text.strip() if reviews_element else "0 ratings"
            reviews_count = self._extract_numbers(reviews_text)
            
            # 提取类别
            category_element = soup.select_one('#wayfinding-breadcrumbs_feature_div .a-link-normal:last-child')
            category = category_element.text.strip() if category_element else ""
            
            # 提取图片URL
            image_element = soup.select_one('#landingImage')
            image_url = image_element.get('src') if image_element else ""
            
            # 提取描述
            description_element = soup.select_one('#productDescription p')
            description = description_element.text.strip() if description_element else ""
            
            # 标准化数据
            return {
                "platform": "amazon",
                "product_id": product_id,
                "name": name,
                "price": price,
                "currency": "USD",  # 亚马逊美国站默认美元
                "sales_volume": 0,  # 亚马逊不直接显示销量
                "rating": rating,
                "reviews_count": reviews_count,
                "category": category,
                "image_url": image_url,
                "product_url": url,
                "description": description,
                "attributes": {},
                "collected_at": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect Amazon product details for {product_id}: {e}")
            return None
    
    def _extract_price(self, price_text):
        """从价格文本中提取数字"""
        try:
            # 移除货币符号和逗号，提取数字
            price_str = re.sub(r'[^\d.]', '', price_text)
            return float(price_str) if price_str else 0
        except Exception:
            return 0
    
    def _extract_rating(self, rating_text):
        """从评分文本中提取数字"""
        try:
            # 匹配评分 (例如: "4.5 out of 5 stars")
            rating_match = re.search(r'([\d.]+)\s+out\s+of\s+5', rating_text)
            if rating_match:
                return float(rating_match.group(1))
            return 0
        except Exception:
            return 0
    
    def _extract_numbers(self, text):
        """从文本中提取数字"""
        try:
            # 匹配数字 (例如: "1,234 ratings")
            num_match = re.search(r'[\d,]+', text)
            if num_match:
                return int(num_match.group(0).replace(',', ''))
            
            return 0
        except Exception:
            return 0 