#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 数据库模型

此文件定义系统使用的数据库模型和表结构。
模型包括：
- 商品数据模型
- 商品历史数据模型
- 用户数据模型
- 报告数据模型

作者: AI助手
创建日期: 2023-06-01
"""

from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import LONGTEXT, MEDIUMTEXT

Base = declarative_base()

class Product(Base):
    """商品数据模型"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), index=True)                     # 平台名称
    product_id = Column(String(100), unique=True, index=True)     # 平台上的商品ID
    name = Column(String(255), nullable=False)                    # 商品名称
    price = Column(Float)                                         # 商品价格
    currency = Column(String(10), default='CNY')                  # 货币单位
    sales_volume = Column(Integer, default=0)                     # 销量
    rating = Column(Float, default=0)                             # 评分 (0-5)
    reviews_count = Column(Integer, default=0)                    # 评论数量
    category = Column(String(100), index=True)                    # 商品类别
    image_url = Column(String(255))                               # 主图URL
    product_url = Column(String(255))                             # 商品链接
    description = Column(MEDIUMTEXT)                              # 商品描述，使用MySQL特定类型
    enhanced_description = Column(MEDIUMTEXT)                     # 增强描述
    sentiment_score = Column(Float)                               # 情感评分
    popularity_score = Column(Float, default=0, index=True)       # 流行度评分
    keywords = Column(JSON)                                       # 关键词列表
    attributes = Column(JSON)                                     # 商品属性
    discount_percentage = Column(Float, default=0)                # 折扣百分比
    original_price = Column(Float)                                # 原价
    stock_status = Column(String(20))                             # 库存状态
    shipping_info = Column(JSON)                                  # 物流信息
    seller_id = Column(String(100), index=True)                   # 卖家ID
    seller_name = Column(String(100))                             # 卖家名称
    seller_rating = Column(Float, default=0)                      # 卖家评分
    created_at = Column(Float)                                    # 创建时间戳
    updated_at = Column(Float)                                    # 更新时间戳
    last_collected = Column(Float)                                # 最后采集时间戳
    
    # MySQL特定的表选项
    __table_args__ = (
        Index('idx_platform_category', 'platform', 'category'),
        Index('idx_sales_volume', 'sales_volume', 'platform'),
        Index('idx_rating', 'rating', 'platform'),
        Index('idx_price', 'price'),
        Index('idx_popularity', 'popularity_score'),
        Index('idx_created_at', 'created_at'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'platform': self.platform,
            'product_id': self.product_id,
            'name': self.name,
            'price': self.price,
            'currency': self.currency,
            'sales_volume': self.sales_volume,
            'rating': self.rating,
            'reviews_count': self.reviews_count,
            'category': self.category,
            'image_url': self.image_url,
            'product_url': self.product_url,
            'description': self.description,
            'enhanced_description': self.enhanced_description,
            'sentiment_score': self.sentiment_score,
            'popularity_score': self.popularity_score,
            'keywords': self.keywords,
            'attributes': self.attributes,
            'discount_percentage': self.discount_percentage,
            'original_price': self.original_price,
            'stock_status': self.stock_status,
            'shipping_info': self.shipping_info,
            'seller_id': self.seller_id,
            'seller_name': self.seller_name,
            'seller_rating': self.seller_rating,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_collected': self.last_collected
        }

    def calculate_popularity_score(self):
        """计算商品流行度评分"""
        # 销量权重 60%
        sales_factor = min(self.sales_volume / 1000, 1) * 60
        
        # 评分权重 25%
        rating_factor = (self.rating / 5) * 25
        
        # 评论数权重 15%
        reviews_factor = min(self.reviews_count / 500, 1) * 15
        
        # 计算总分
        self.popularity_score = sales_factor + rating_factor + reviews_factor
        
        return self.popularity_score


class ProductHistory(Base):
    """商品历史数据模型"""
    __tablename__ = 'product_history'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(String(100), index=True)                 # 关联商品ID
    platform = Column(String(50), index=True)                    # 平台名称
    category = Column(String(100), index=True)                   # 商品类别
    date = Column(Float, index=True)                             # 记录日期时间戳
    price = Column(Float)                                        # 历史价格
    sales_volume = Column(Integer, default=0)                    # 历史销量
    rating = Column(Float, default=0)                            # 历史评分
    reviews_count = Column(Integer, default=0)                   # 历史评论数
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'platform': self.platform,
            'category': self.category,
            'date': self.date,
            'price': self.price,
            'sales_volume': self.sales_volume,
            'rating': self.rating,
            'reviews_count': self.reviews_count
        }


class User(Base):
    """用户数据模型"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)  # 用户名
    email = Column(String(100), unique=True, nullable=False)    # 邮箱
    password_hash = Column(String(255), nullable=False)         # 密码哈希
    is_admin = Column(Boolean, default=False)                   # 是否为管理员
    last_login = Column(Float)                                  # 最后登录时间戳
    preferences = Column(JSON)                                  # 用户偏好设置
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'last_login': self.last_login,
            'preferences': self.preferences
        }


class Report(Base):
    """报告数据模型"""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))           # 关联用户ID
    title = Column(String(255), nullable=False)                 # 报告标题
    description = Column(Text)                                  # 报告描述
    content = Column(JSON)                                      # 报告内容
    parameters = Column(JSON)                                   # 报告参数
    created_at = Column(Float)                                  # 创建时间戳
    updated_at = Column(Float)                                  # 更新时间戳
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'parameters': self.parameters,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        } 