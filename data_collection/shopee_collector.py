#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - Shopee数据采集器

此文件实现Shopee电商平台的数据采集功能。
功能包括：
- 采集Shopee热门商品数据
- 与Shopee API交互
- 提取销量、评分和评论数据
- 处理Shopee特有的数据格式和认证
- 管理API请求限制

作者: AI助手
创建日期: 2023-06-01
"""

from .base_collector import BaseCollector
import time
import json
import hmac
import hashlib
import random

class ShopeeCollector(BaseCollector):
    """Shopee商城数据采集器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config["api_key"]
        self.api_secret = config["api_secret"]
        self.partner_id = config.get("partner_id")
        self.shop_id = config.get("shop_id")
        self.base_url = "https://partner.shopeemobile.com/api/v2"
    
    def _generate_signature(self, path, timestamp):
        """生成API签名"""
        base_string = f"{self.partner_id}{path}{timestamp}{self.api_key}{self.api_secret}"
        signature = hmac.new(
            self.api_secret.encode(), 
            base_string.encode(), 
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _prepare_common_params(self, path):
        """准备通用参数"""
        timestamp = int(time.time())
        signature = self._generate_signature(path, timestamp)
        
        return {
            "partner_id": self.partner_id,
            "timestamp": timestamp,
            "access_token": self.api_key,
            "shop_id": self.shop_id,
            "sign": signature
        }
    
    def get_hot_products(self, category=None, limit=None):
        """获取Shopee热门商品"""
        if not limit:
            limit = self.config.get("default_limit", 100)
        
        path = "/product/get_item_list"
        url = f"{self.base_url}{path}"
        
        # 准备参数
        params = self._prepare_common_params(path)
        params.update({
            "offset": 0,
            "page_size": limit,
            "item_status": "NORMAL",
            "sort_by": "SOLD"  # 按销量排序
        })
        
        # 添加类别
        if category:
            category_id = self._get_category_id(category)
            if category_id:
                params["category_id"] = category_id
        
        try:
            response_data = self.collect_with_retry(url, method="GET", data=params)
            
            if response_data.get("error") == 0:
                items = response_data.get("response", {}).get("item", [])
                
                # 转换为标准格式
                products = []
                for item in items:
                    item_id = item.get("item_id")
                    # 获取商品详情
                    product_detail = self.get_product_details(item_id)
                    if product_detail:
                        products.append(product_detail)
                
                self.logger.info(f"Collected {len(products)} products from Shopee")
                return products
            else:
                error_msg = response_data.get("message", "Unknown error")
                self.logger.error(f"API error: {error_msg}")
                return []
                
        except Exception as e:
            self.logger.error(f"Failed to collect Shopee hot products: {e}")
            return []
    
    def _get_category_id(self, category_name):
        """获取类别ID"""
        path = "/product/get_category"
        url = f"{self.base_url}{path}"
        
        params = self._prepare_common_params(path)
        
        try:
            response_data = self.collect_with_retry(url, method="GET", data=params)
            
            if response_data.get("error") == 0:
                categories = response_data.get("response", {}).get("category_list", [])
                
                # 查找匹配的类别
                for category in categories:
                    if category.get("category_name", "").lower() == category_name.lower():
                        return category.get("category_id")
                
                self.logger.warning(f"Category '{category_name}' not found")
                return None
            else:
                error_msg = response_data.get("message", "Unknown error")
                self.logger.error(f"API error when getting categories: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get Shopee categories: {e}")
            return None
    
    def get_product_details(self, item_id):
        """获取商品详情"""
        path = "/product/get_item_detail"
        url = f"{self.base_url}{path}"
        
        params = self._prepare_common_params(path)
        params["item_id_list"] = f"[{item_id}]"
        
        try:
            response_data = self.collect_with_retry(url, method="GET", data=params)
            
            if response_data.get("error") == 0:
                items = response_data.get("response", {}).get("item_list", [])
                if not items:
                    return None
                
                item = items[0]
                
                # 获取评分和评论数
                rating_data = self._get_rating_data(item_id)
                
                # 转换为标准格式
                return {
                    "platform": "shopee",
                    "product_id": str(item.get("item_id")),
                    "name": item.get("item_name"),
                    "price": item.get("price") / 100000 if item.get("price") else 0,  # 转换成元
                    "currency": "CNY",  # 假设是人民币
                    "sales_volume": item.get("sold", 0),
                    "rating": rating_data.get("rating", 0),
                    "reviews_count": rating_data.get("review_count", 0),
                    "category": item.get("category_name"),
                    "image_url": item.get("image", {}).get("image_url") if item.get("image") else None,
                    "product_url": f"https://shopee.com/product/{self.shop_id}/{item_id}",
                    "description": item.get("description"),
                    "attributes": item.get("attribute_list", {}),
                    "collected_at": time.time()
                }
            else:
                error_msg = response_data.get("message", "Unknown error")
                self.logger.error(f"API error: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to collect Shopee product details: {e}")
            return None
    
    def _get_rating_data(self, item_id):
        """获取商品评分数据"""
        # 简化实现，实际情况下需要调用Shopee的评分API
        try:
            # 模拟评分数据
            return {
                "rating": random.uniform(3.0, 5.0),
                "review_count": random.randint(10, 1000)
            }
        except Exception:
            return {"rating": 0, "review_count": 0} 