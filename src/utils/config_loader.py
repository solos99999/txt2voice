"""
配置加载器模块
负责读取和管理项目配置文件
"""

import os
import yaml
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"配置文件不存在: {self.config_path}")
                self.config = self._get_default_config()
                return self.config
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"成功加载配置文件: {self.config_path}")
            return self.config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.config = self._get_default_config()
            return self.config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的多级键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的多级键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self, path: Optional[str] = None) -> None:
        """
        保存配置文件
        
        Args:
            path: 保存路径，默认为原路径
        """
        save_path = path or self.config_path
        
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"配置文件已保存: {save_path}")
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            'model': {
                'name': 'cosyvoice2.0',
                'path': 'models/cosyvoice2.0.pth',
                'device': 'auto',
                'batch_size': 1,
                'max_text_length': 500
            },
            'audio': {
                'sample_rate': 22050,
                'hop_length': 256,
                'win_length': 1024,
                'n_fft': 1024,
                'mel_channels': 80,
                'mel_fmin': 0,
                'mel_fmax': 8000
            },
            'voice_packs': {
                'default': {
                    'name': '默认语音包',
                    'description': '标准中文语音包',
                    'speaker_id': 0,
                    'emotion': 'neutral',
                    'speed': 1.0,
                    'pitch': 0,
                    'energy': 1.0
                }
            },
            'output': {
                'format': 'wav',
                'quality': 'high',
                'normalize': True,
                'trim_silence': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/tts.log',
                'max_size': '10MB',
                'backup_count': 5
            }
        }


# 全局配置实例
config_loader = ConfigLoader() 