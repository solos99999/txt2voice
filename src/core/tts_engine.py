"""
TTS引擎
支持多个TTS引擎的统一接口
"""

import os
import torch
import numpy as np
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.config_loader import config_loader
from .voice_pack_manager import voice_pack_manager
from .performance_optimizer import optimizer, performance_monitor

# 导入各个引擎
from .edge_tts_integration import edge_tts_integration
from .gtts_integration import gtts_integration
from .pyttsx3_integration import pyttsx3_integration
from .real_cosyvoice_integration import real_cosyvoice2_integration

logger = get_logger(__name__)


class TTSEngine:
    """TTS引擎类"""
    
    def __init__(self):
        self.model_path = config_loader.get("model.path", "models/cosyvoice2.0.pth")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.available_engines = []
        self.current_engine = None
        
        logger.info(f"TTS引擎初始化完成，设备: {self.device}")
    
    def load_model(self) -> bool:
        """加载TTS模型"""
        try:
            logger.info("正在加载TTS引擎...")
            
            # 按优先级尝试加载各个引擎
            engines = [
                ("edge_tts", edge_tts_integration, "Edge-TTS (微软TTS服务)"),
                ("gtts", gtts_integration, "gTTS (Google TTS服务)"),
                ("pyttsx3", pyttsx3_integration, "pyttsx3 (离线TTS)"),
                ("cosyvoice", real_cosyvoice2_integration, "CosyVoice2.0 (真实版)")
            ]
            
            for engine_name, engine_instance, engine_desc in engines:
                try:
                    if engine_instance.load_model():
                        self.available_engines.append(engine_name)
                        if self.current_engine is None:
                            self.current_engine = engine_name
                        logger.info(f"✓ {engine_desc} 加载成功")
                    else:
                        logger.warning(f"✗ {engine_desc} 加载失败")
                except Exception as e:
                    logger.warning(f"✗ {engine_desc} 加载异常: {e}")
            
            if not self.available_engines:
                logger.error("没有可用的TTS引擎")
                return False
            
            logger.info(f"成功加载 {len(self.available_engines)} 个TTS引擎: {', '.join(self.available_engines)}")
            logger.info(f"当前使用引擎: {self.current_engine}")
            return True
            
        except Exception as e:
            logger.error(f"加载TTS引擎失败: {e}")
            return False
    
    def get_available_engines(self) -> List[str]:
        """获取可用的引擎列表"""
        return self.available_engines.copy()
    
    def set_current_engine(self, engine_name: str) -> bool:
        """设置当前使用的引擎"""
        if engine_name in self.available_engines:
            self.current_engine = engine_name
            logger.info(f"切换到引擎: {engine_name}")
            return True
        else:
            logger.error(f"引擎 {engine_name} 不可用")
            return False
    
    def get_current_engine(self) -> str:
        """获取当前使用的引擎"""
        return self.current_engine
    
    def synthesize(self, text: str, voice_pack: str = "default", 
                   speed: float = 1.0, pitch: int = 0, energy: float = 1.0) -> Optional[np.ndarray]:
        """语音合成"""
        try:
            if not self.available_engines:
                logger.error("没有可用的TTS引擎")
                return None
            
            logger.info(f"开始合成文本: {text[:50]}...")
            
            # 使用当前引擎进行合成
            if self.current_engine == "edge_tts":
                return edge_tts_integration.synthesize(text, voice_pack, speed, pitch, energy)
            elif self.current_engine == "gtts":
                return gtts_integration.synthesize(text, voice_pack, speed, pitch, energy)
            elif self.current_engine == "pyttsx3":
                return pyttsx3_integration.synthesize(text, voice_pack, speed, pitch, energy)
            elif self.current_engine == "cosyvoice":
                return real_cosyvoice2_integration.synthesize(text, voice_pack, speed, pitch, energy)
            else:
                logger.error(f"未知的引擎: {self.current_engine}")
                return None
                
        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            return None
    
    def get_engine_info(self, engine_name: str = None) -> Dict[str, Any]:
        """获取引擎信息"""
        if engine_name is None:
            engine_name = self.current_engine
        
        if engine_name == "edge_tts":
            return edge_tts_integration.get_model_info()
        elif engine_name == "gtts":
            return gtts_integration.get_model_info()
        elif engine_name == "pyttsx3":
            return pyttsx3_integration.get_model_info()
        elif engine_name == "cosyvoice":
            return real_cosyvoice2_integration.get_model_info()
        else:
            return {"error": f"未知引擎: {engine_name}"}
    
    def get_all_engines_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有引擎的信息"""
        info = {}
        for engine_name in self.available_engines:
            info[engine_name] = self.get_engine_info(engine_name)
        return info
    
    def get_voice_packs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有可用的语音包"""
        return voice_pack_manager.get_all_voice_packs()
    
    def get_engine_voice_packs(self, engine_name: str) -> Dict[str, Dict[str, Any]]:
        """获取指定引擎的所有语音包"""
        return voice_pack_manager.get_engine_voice_packs(engine_name)
    
    def get_all_engine_voice_packs(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """获取所有引擎的语音包"""
        return voice_pack_manager.get_all_engine_voice_packs()
    
    def get_available_voice_packs(self) -> List[str]:
        """获取可用的语音包列表（兼容性方法）"""
        return voice_pack_manager.get_available_voice_packs()
    
    def get_available_engine_voice_packs(self, engine_name: str) -> List[str]:
        """获取指定引擎可用的语音包列表"""
        return voice_pack_manager.get_available_engine_voice_packs(engine_name)
    
    def get_voice_pack_info(self, voice_pack_name: str, engine_name: str = None) -> Optional[Dict[str, Any]]:
        """获取语音包信息，包括引擎特定信息"""
        return voice_pack_manager.get_voice_pack_info(voice_pack_name, engine_name)
    
    def get_engine_voice_pack_info(self, engine_name: str, voice_pack_name: str) -> Optional[Dict[str, Any]]:
        """获取指定引擎的指定语音包信息"""
        return voice_pack_manager.get_engine_voice_pack(engine_name, voice_pack_name)
    
    def is_engine_voice_pack_available(self, engine_name: str, voice_pack_name: str) -> bool:
        """检查指定引擎的指定语音包是否可用"""
        return voice_pack_manager.is_engine_voice_pack_available(engine_name, voice_pack_name)


# 全局实例
tts_engine = TTSEngine() 