#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - TikTok数据采集器

此文件实现TikTok Shop电商平台的数据采集功能。
功能包括：
- 通过TikTok Shop API获取商品数据
- 提取热门商品、销量和评分信息
- 处理TikTok特有的认证和签名机制
- 解析短视频相关商品信息
- 管理API请求限制和令牌刷新

作者: AI助手
创建日期: 2023-06-01
"""

from .base_collector import BaseCollector
import hmac
import hashlib
import time
import json

class TikTokCollector(BaseCollector):
    """TikTok商店数据采集器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config["api_key"]
        self.api_secret = config["api_secret"]
        self.shop_id = config.get("shop_id")
        self.base_url = "https://open-api.tiktokglobalshop.com"
    
    def _generate_signature(self, path, timestamp):
        """生成API签名"""
        string_to_sign = f"{self.api_key}{timestamp}{path}"
        signature = hmac.new(
            self.api_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _prepare_headers(self, path):
        """准备请求头"""
        timestamp = str(int(time.time()))
        signature = self._generate_signature(path, timestamp)
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "x-timestamp": timestamp,
            "x-signature": signature
        }
        return headers
    
    def get_hot_products(self, category=None, limit=None):
        """获取TikTok热门商品"""
        if not limit:
            limit = self.config.get("default_limit", 100)
        
        path = "/api/products/search"
        url = f"{self.base_url}{path}"
        
        # 准备请求参数
        params = {
            "page_size": limit,
            "page_number": 1,
            "sort_by": "popularity",
            "sort_type": "desc"
        }
        
        # 添加类别筛选
        if category:
            params["category_id"] = self._get_category_id(category)
        
        self.session.headers.update(self._prepare_headers(path))
        
        try:
            response_data = self.collect_with_retry(url, method="POST", data=params)
            
            if response_data.get("code") == 0:
                products_data = response_data.get("data", {}).get("products", [])
                
                # 转换为标准格式
                products = []
                for product in products_data:
                    # 获取商品详情
                    product_detail = self.get_product_details(product.get("id"))
                    if product_detail:
                        products.append(product_detail)
                
                self.logger.info(f"Collected {len(products)} products from TikTok")
                return products
            else:
                error_msg = response_data.get("message", "Unknown error")
                self.logger.error(f"API error: {error_msg}")
                return []
                
        except Exception as e:
            self.logger.error(f"Failed to collect TikTok hot products: {e}")
            return []
    
    def _get_category_id(self, category_name):
        """获取类别ID"""
        path = "/api/categories"
        url = f"{self.base_url}{path}"
        
        self.session.headers.update(self._prepare_headers(path))
        
        try:
            response_data = self.collect_with_retry(url)
            
            if response_data.get("code") == 0:
                categories = response_data.get("data", {}).get("categories", [])
                
                # 查找匹配的类别
                for cat in categories:
                    if cat.get("name", "").lower() == category_name.lower():
                        return cat.get("id")
                
                self.logger.warning(f"Category '{category_name}' not found")
                return None
            else:
                error_msg = response_data.get("message", "Unknown error")
                self.logger.error(f"API error when getting categories: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get TikTok categories: {e}")
            return None
    
    def get_product_details(self, product_id):
        """获取商品详情"""
        path = f"/api/products/{product_id}"
        url = f"{self.base_url}{path}"
        
        self.session.headers.update(self._prepare_headers(path))
        
        try:
            response_data = self.collect_with_retry(url)
            
            if response_data.get("code") == 0:
                product = response_data.get("data", {}).get("product", {})
                
                # 转换为标准格式
                return {
                    "platform": "tiktok",
                    "product_id": product.get("id"),
                    "name": product.get("name"),
                    "price": product.get("price", {}).get("original_price"),
                    "currency": product.get("price", {}).get("currency"),
                    "sales_volume": product.get("sales", {}).get("sales_30_day", 0),
                    "rating": product.get("rating", {}).get("average_rating", 0),
                    "reviews_count": product.get("rating", {}).get("rating_count", 0),
                    "category": product.get("category_name"),
                    "image_url": product.get("images", [])[0] if product.get("images") else None,
                    "product_url": product.get("product_url"),
                    "description": product.get("description"),
                    "attributes": product.get("attributes", {}),
                    "collected_at": time.time()
                }
            else:
                error_msg = response_data.get("message", "Unknown error")
                self.logger.error(f"API error: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to collect TikTok product details: {e}")
            return None 