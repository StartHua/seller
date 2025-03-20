#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - 数据库管理器

此文件实现与数据库的交互功能，处理数据的存储和检索。
功能包括：
- 数据库连接管理
- 商品数据存储与检索
- 历史数据记录
- 统计数据生成

作者: AI助手
创建日期: 2023-06-01
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import os
from datetime import datetime
import json
import importlib

Base = declarative_base()

class Product(Base):
    """商品数据模型"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    tiktok_id = Column(String, unique=True)
    name = Column(String)
    price = Column(Float)
    category = Column(String)
    sales_volume = Column(Integer)
    rating = Column(Float)
    reviews_count = Column(Integer)
    enhanced_description = Column(String)
    sentiment_score = Column(Float)
    metadata = Column(JSON)
    
class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 导入数据模型
        from storage import models
        self.models = models
        
        # 获取数据库配置
        db_config = config.get('database', {})
        db_type = db_config.get('type', 'sqlite').lower()
        
        # 创建数据库引擎
        if db_type == 'sqlite':
            # SQLite连接
            db_path = db_config.get('path', './data/ecommerce.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
            self.logger.info(f"Connected to SQLite database: {db_path}")
        elif db_type == 'mysql':
            # MySQL连接
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 3306)
            user = db_config.get('user', 'root')
            password = db_config.get('password', '')
            database = db_config.get('database', 'ecommerce')
            charset = db_config.get('charset', 'utf8mb4')
            
            # 构建连接URL
            connection_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"
            self.engine = create_engine(connection_url, pool_recycle=3600, pool_size=10, max_overflow=20, echo=False)
            self.logger.info(f"Connected to MySQL database: {host}:{port}/{database}")
        elif db_type == 'postgresql':
            # PostgreSQL连接
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 5432)
            user = db_config.get('user', 'postgres')
            password = db_config.get('password', '')
            database = db_config.get('database', 'ecommerce')
            
            # 构建连接URL
            connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            self.engine = create_engine(connection_url, pool_size=10, max_overflow=20, echo=False)
            self.logger.info(f"Connected to PostgreSQL database: {host}:{port}/{database}")
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        # 创建会话工厂
        self.Session = sessionmaker(bind=self.engine)
        
        # 创建表
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        try:
            # 创建所有Model对应的表
            self.models.Base.metadata.create_all(self.engine)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Error creating database tables: {e}")
            raise
    
    def save_product(self, product_data):
        """保存商品数据"""
        try:
            session = self.Session()
            
            # 检查商品是否已存在
            product_id = product_data.get('product_id')
            platform = product_data.get('platform')
            
            if not product_id or not platform:
                self.logger.error("Missing product_id or platform in product data")
                return None
            
            existing_product = session.query(self.models.Product).filter_by(product_id=product_id).first()
            
            if existing_product:
                # 更新现有商品
                old_sales = existing_product.sales_volume or 0
                old_rating = existing_product.rating or 0
                old_reviews = existing_product.reviews_count or 0
                
                # 更新属性
                for key, value in product_data.items():
                    if hasattr(existing_product, key):
                        setattr(existing_product, key, value)
                
                # 更新时间戳
                existing_product.collected_at = time.time()
                
                # 计算流行度评分
                existing_product.calculate_popularity_score()
                
                # 创建历史记录
                history = self.models.ProductHistory(
                    product_id=product_id,
                    platform=platform,
                    category=existing_product.category,
                    date=time.time(),
                    price=existing_product.price,
                    sales_volume=existing_product.sales_volume,
                    rating=existing_product.rating,
                    reviews_count=existing_product.reviews_count
                )
                
                session.add(history)
                session.commit()
                
                self.logger.info(f"Updated product: {product_id}")
                return existing_product.id
            else:
                # 创建新商品
                new_product = self.models.Product(**product_data)
                new_product.collected_at = time.time()
                
                # 计算流行度评分
                new_product.calculate_popularity_score()
                
                session.add(new_product)
                session.commit()
                
                # 创建历史记录
                history = self.models.ProductHistory(
                    product_id=product_id,
                    platform=platform,
                    category=new_product.category,
                    date=time.time(),
                    price=new_product.price,
                    sales_volume=new_product.sales_volume,
                    rating=new_product.rating,
                    reviews_count=new_product.reviews_count
                )
                
                session.add(history)
                session.commit()
                
                self.logger.info(f"Created new product: {product_id}")
                return new_product.id
                
        except Exception as e:
            self.logger.error(f"Error saving product: {e}")
            session.rollback()
            return None
        finally:
            session.close()
    
    def get_product(self, product_id):
        """获取单个商品数据"""
        try:
            session = self.Session()
            product = session.query(self.models.Product).filter_by(product_id=product_id).first()
            
            if product:
                return product.to_dict()
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting product: {e}")
            return None
        finally:
            session.close()
    
    def get_products(self, platform=None, category=None, limit=100):
        """获取商品列表"""
        try:
            session = self.Session()
            query = session.query(self.models.Product)
            
            if platform:
                query = query.filter(self.models.Product.platform == platform)
            
            if category:
                query = query.filter(self.models.Product.category == category)
            
            # 按流行度排序
            query = query.order_by(self.models.Product.popularity_score.desc())
            
            # 限制结果数量
            query = query.limit(limit)
            
            # 转换为字典列表
            products = [p.to_dict() for p in query.all()]
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error getting products: {e}")
            return []
        finally:
            session.close()
    
    def get_categories(self, platform=None):
        """获取所有商品类别"""
        try:
            session = self.Session()
            query = session.query(self.models.Product.category).distinct()
            
            if platform:
                query = query.filter(self.models.Product.platform == platform)
            
            categories = [c[0] for c in query.all() if c[0]]
            
            return sorted(categories)
            
        except Exception as e:
            self.logger.error(f"Error getting categories: {e}")
            return []
        finally:
            session.close()
    
    def get_product_count(self):
        """获取商品数量"""
        try:
            session = self.Session()
            count = session.query(self.models.Product).count()
            return count
        except Exception as e:
            self.logger.error(f"Error getting product count: {e}")
            return 0
        finally:
            session.close()
    
    def get_platform_stats(self):
        """获取各平台商品统计"""
        try:
            session = self.Session()
            query = session.query(
                self.models.Product.platform, 
                func.count(self.models.Product.id)
            ).group_by(self.models.Product.platform)
            
            stats = {platform: count for platform, count in query.all()}
            return stats
        except Exception as e:
            self.logger.error(f"Error getting platform stats: {e}")
            return {}
        finally:
            session.close()
    
    def save_report(self, user_id, title, description, content, parameters):
        """保存分析报告"""
        try:
            session = self.Session()
            now = datetime.now().timestamp()
            
            report = self.models.Report(
                user_id=user_id,
                title=title,
                description=description,
                content=content,
                parameters=parameters,
                created_at=now,
                updated_at=now
            )
            
            session.add(report)
            session.commit()
            
            return report.id
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            session.rollback()
            return None
        finally:
            session.close() 