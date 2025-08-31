"""
性能优化模块
提供缓存、内存管理等优化功能
"""

import time
import threading
from typing import Dict, Any, Optional
from functools import wraps
from ..utils.logger import get_logger


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.metrics = {}
    
    def start_timer(self, name: str):
        """开始计时"""
        self.metrics[name] = {"start_time": time.time()}
    
    def end_timer(self, name: str) -> float:
        """结束计时并返回耗时"""
        if name in self.metrics:
            start_time = self.metrics[name]["start_time"]
            duration = time.time() - start_time
            self.metrics[name]["duration"] = duration
            self.logger.info(f"性能监控 - {name}: {duration:.3f}秒")
            return duration
        return 0.0


class Cache:
    """简单缓存类"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                return self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        with self.lock:
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times.keys(), 
                               key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()


def performance_monitor(func_name: str = None):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = PerformanceMonitor()
            name = func_name or func.__name__
            
            monitor.start_timer(name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.end_timer(name)
        
        return wrapper
    return decorator


class Optimizer:
    """优化器主类"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.monitor = PerformanceMonitor()
        self.cache = Cache()
    
    def optimize_synthesis(self, text: str, voice_pack: str) -> str:
        """优化合成参数"""
        text_length = len(text)
        
        if text_length < 50:
            return "high_quality"
        elif text_length < 200:
            return "balanced"
        else:
            return "fast"
    
    def cleanup_memory(self):
        """清理内存"""
        self.cache.clear()
        self.logger.info("内存清理完成")


# 全局优化器实例
optimizer = Optimizer() 