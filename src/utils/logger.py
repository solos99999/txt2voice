"""
日志管理模块
负责统一管理项目日志输出
"""

import os
import logging
import logging.handlers
from typing import Optional
from .config_loader import config_loader


def setup_logger(
    name: str = "cosyvoice_tts",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    max_size: str = "10MB",
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径
        max_size: 日志文件最大大小
        backup_count: 备份文件数量
        
    Returns:
        配置好的日志记录器
    """
    # 获取配置
    if level is None:
        level = config_loader.get('logging.level', 'INFO')
    
    if log_file is None:
        log_file = config_loader.get('logging.file', 'logs/tts.log')
    
    if max_size == "10MB":
        max_size = config_loader.get('logging.max_size', '10MB')
    
    if backup_count == 5:
        backup_count = config_loader.get('logging.backup_count', 5)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        try:
            # 创建日志目录
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # 解析文件大小
            size_map = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
            size_str = max_size.upper()
            max_bytes = 10 * 1024 * 1024  # 默认10MB
            for unit, multiplier in size_map.items():
                if size_str.endswith(unit):
                    try:
                        max_bytes = int(size_str[:-len(unit)]) * multiplier
                        break
                    except ValueError:
                        max_bytes = 10 * 1024 * 1024  # 默认10MB
                        break
            
            # 创建轮转文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"创建日志文件失败: {e}")
    
    return logger


def get_logger(name: str = "cosyvoice_tts") -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    logger = logging.getLogger(name)
    
    # 如果日志记录器还没有配置处理器，则进行配置
    if not logger.handlers:
        setup_logger(name)
    
    return logger


# 创建默认日志记录器
default_logger = setup_logger() 