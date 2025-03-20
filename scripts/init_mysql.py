#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商数据排行分析系统 - MySQL数据库初始化脚本

此脚本用于初始化MySQL数据库，包括:
- 创建数据库
- 创建用户
- 授予权限
- 初始化表结构

作者: AI助手
创建日期: 2023-06-01
"""

import mysql.connector
import yaml
import argparse
import sys
import getpass

def parse_args():
    parser = argparse.ArgumentParser(description='Initialize MySQL database for ecommerce ranking system')
    parser.add_argument('--config', default='config/config.yaml', help='Path to config file')
    parser.add_argument('--root-password', help='MySQL root password')
    return parser.parse_args()

def create_database_and_user(config, root_password):
    # 从配置获取数据库设置
    db_config = config.get('database', {})
    host = db_config.get('host', 'localhost')
    port = db_config.get('port', 3306)
    user = db_config.get('user', 'ecommerce_user')
    password = db_config.get('password', 'strong_password')
    database = db_config.get('database', 'ecommerce')
    
    # 连接到MySQL
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user="root",
            password=root_password
        )
        
        cursor = connection.cursor()
        
        # 创建数据库
        print(f"Creating database '{database}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        # 创建用户并授权
        print(f"Creating user '{user}'...")
        cursor.execute(f"CREATE USER IF NOT EXISTS '{user}'@'%' IDENTIFIED BY '{password}'")
        cursor.execute(f"GRANT ALL PRIVILEGES ON {database}.* TO '{user}'@'%'")
        cursor.execute("FLUSH PRIVILEGES")
        
        print("Database and user created successfully")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        sys.exit(1)
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def main():
    args = parse_args()
    
    # 加载配置
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # 获取MySQL root密码
    root_password = args.root_password
    if not root_password:
        root_password = getpass.getpass("Enter MySQL root password: ")
    
    # 创建数据库和用户
    create_database_and_user(config, root_password)

if __name__ == "__main__":
    main() 