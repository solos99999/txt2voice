"""
语音包管理器
管理所有TTS引擎的语音包
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.config_loader import config_loader

logger = get_logger(__name__)


class VoicePackManager:
    """语音包管理器"""
    
    def __init__(self):
        self.voice_packs = {}
        self.engine_voice_packs = {}
        self.load_voice_packs()
    
    def load_voice_packs(self):
        """加载语音包配置"""
        try:
            # 加载基础语音包配置
            voice_packs_config = config_loader.get("voice_packs", {})
            
            # 基础语音包
            base_voice_packs = {
                "default": {
                    "name": "默认语音包",
                    "description": "标准中文语音包",
                    "speaker_id": 0,
                    "emotion": "neutral",
                    "speed": 1.0,
                    "pitch": 0,
                    "energy": 1.0,
                    "language": "zh-CN",
                    "gender": "unknown",
                    "style": "neutral"
                },
                "female": {
                    "name": "女声语音包",
                    "description": "温柔女声",
                    "speaker_id": 1,
                    "emotion": "gentle",
                    "speed": 1.0,
                    "pitch": 2,
                    "energy": 0.9,
                    "language": "zh-CN",
                    "gender": "female",
                    "style": "gentle"
                },
                "male": {
                    "name": "男声语音包",
                    "description": "磁性男声",
                    "speaker_id": 2,
                    "emotion": "deep",
                    "speed": 0.9,
                    "pitch": -2,
                    "energy": 1.1,
                    "language": "zh-CN",
                    "gender": "male",
                    "style": "deep"
                },
                "child": {
                    "name": "儿童语音包",
                    "description": "活泼可爱的儿童声音",
                    "speaker_id": 3,
                    "emotion": "happy",
                    "speed": 1.2,
                    "pitch": 4,
                    "energy": 1.2,
                    "language": "zh-CN",
                    "gender": "unknown",
                    "style": "cute"
                },
                "elder": {
                    "name": "老年语音包",
                    "description": "慈祥的老年声音",
                    "speaker_id": 4,
                    "emotion": "calm",
                    "speed": 0.8,
                    "pitch": -1,
                    "energy": 0.8,
                    "language": "zh-CN",
                    "gender": "unknown",
                    "style": "wise"
                },
                "robot": {
                    "name": "机器人语音包",
                    "description": "科技感的机器人声音",
                    "speaker_id": 5,
                    "emotion": "neutral",
                    "speed": 0.9,
                    "pitch": 0,
                    "energy": 1.0,
                    "language": "zh-CN",
                    "gender": "unknown",
                    "style": "robotic"
                },
                "angry": {
                    "name": "愤怒语音包",
                    "description": "愤怒情绪的声音",
                    "speaker_id": 6,
                    "emotion": "angry",
                    "speed": 1.1,
                    "pitch": 1,
                    "energy": 1.3,
                    "language": "zh-CN",
                    "gender": "unknown",
                    "style": "angry"
                },
                "sad": {
                    "name": "悲伤语音包",
                    "description": "悲伤情绪的声音",
                    "speaker_id": 7,
                    "emotion": "sad",
                    "speed": 0.8,
                    "pitch": -1,
                    "energy": 0.7,
                    "language": "zh-CN",
                    "gender": "unknown",
                    "style": "sad"
                }
            }
            
            # 合并配置
            self.voice_packs = {**base_voice_packs, **voice_packs_config}
            
            # 为每个引擎创建独立的语音包列表
            self._create_engine_voice_packs()
            
            logger.info(f"总共加载了 {len(self.voice_packs)} 个基础语音包")
            
        except Exception as e:
            logger.error(f"加载语音包配置失败: {e}")
            self.voice_packs = {}
    
    def _create_engine_voice_packs(self):
        """为每个引擎创建独立的语音包列表"""
        try:
            # 定义引擎列表
            engines = ["edge_tts", "gtts", "pyttsx3", "cosyvoice"]
            
            # 为每个引擎创建语音包
            for engine_name in engines:
                engine_packs = {}
                
                for pack_name, pack_config in self.voice_packs.items():
                    # 创建引擎特定的语音包名称
                    engine_pack_name = f"{engine_name}_{pack_name}"
                    
                    # 复制基础配置
                    engine_pack_config = pack_config.copy()
                    
                    # 添加引擎特定信息
                    engine_pack_config["engine"] = engine_name
                    engine_pack_config["base_pack"] = pack_name
                    engine_pack_config["display_name"] = f"{engine_name.upper()}-{pack_config.get('name', pack_name)}"
                    
                    # 根据引擎添加特定配置
                    if engine_name == "edge_tts":
                        engine_pack_config["voice_id"] = self._get_edge_tts_voice_id(pack_name)
                        engine_pack_config["description"] = f"Edge-TTS {pack_config.get('description', '')}"
                    elif engine_name == "gtts":
                        engine_pack_config["language_config"] = self._get_gtts_language_config(pack_name)
                        engine_pack_config["description"] = f"gTTS {pack_config.get('description', '')}"
                    elif engine_name == "pyttsx3":
                        engine_pack_config["voice_id"] = self._get_pyttsx3_voice_id(pack_name)
                        engine_pack_config["description"] = f"pyttsx3 {pack_config.get('description', '')}"
                    elif engine_name == "cosyvoice":
                        engine_pack_config["description"] = f"CosyVoice {pack_config.get('description', '')}"
                    
                    engine_packs[engine_pack_name] = engine_pack_config
                
                self.engine_voice_packs[engine_name] = engine_packs
                logger.info(f"为引擎 {engine_name} 创建了 {len(engine_packs)} 个语音包")
                
        except Exception as e:
            logger.error(f"创建引擎语音包失败: {e}")
    
    def _get_edge_tts_voice_id(self, pack_name: str) -> str:
        """获取Edge-TTS语音ID"""
        voice_mapping = {
            "default": "zh-CN-XiaoxiaoNeural",
            "female": "zh-CN-XiaoxiaoNeural",
            "male": "zh-CN-YunjianNeural",
            "child": "zh-CN-XiaoxiaoNeural",
            "elder": "zh-CN-YunjianNeural",
            "robot": "zh-CN-YunjianNeural",
            "angry": "zh-CN-XiaoxiaoNeural",
            "sad": "zh-CN-XiaoxiaoNeural"
        }
        return voice_mapping.get(pack_name, "zh-CN-XiaoxiaoNeural")
    
    def _get_gtts_language_config(self, pack_name: str) -> dict:
        """获取gTTS语言配置"""
        language_configs = {
            "default": {"lang": "zh-cn", "tld": "com"},
            "female": {"lang": "zh-cn", "tld": "com"},
            "male": {"lang": "zh-tw", "tld": "com"},
            "child": {"lang": "zh-cn", "tld": "com"},
            "elder": {"lang": "zh-cn", "tld": "com"},
            "robot": {"lang": "en", "tld": "com"},
            "angry": {"lang": "zh-cn", "tld": "com"},
            "sad": {"lang": "zh-cn", "tld": "com"}
        }
        return language_configs.get(pack_name, language_configs["default"])
    
    def _get_pyttsx3_voice_id(self, pack_name: str) -> str:
        """获取pyttsx3语音ID"""
        voice_mapping = {
            "default": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ZH-CN_HUIHUI_11.0",
            "female": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ZH-CN_HUIHUI_11.0",
            "male": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0",
            "child": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ZH-CN_HUIHUI_11.0",
            "elder": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0",
            "robot": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0",
            "angry": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ZH-CN_HUIHUI_11.0",
            "sad": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ZH-CN_HUIHUI_11.0"
        }
        return voice_mapping.get(pack_name, voice_mapping["default"])
    
    def get_all_voice_packs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有基础语音包"""
        return self.voice_packs.copy()
    
    def get_engine_voice_packs(self, engine_name: str) -> Dict[str, Dict[str, Any]]:
        """获取指定引擎的所有语音包"""
        return self.engine_voice_packs.get(engine_name, {}).copy()
    
    def get_all_engine_voice_packs(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """获取所有引擎的语音包"""
        return self.engine_voice_packs.copy()
    
    def get_voice_pack(self, voice_pack_name: str) -> Optional[Dict[str, Any]]:
        """获取指定基础语音包"""
        return self.voice_packs.get(voice_pack_name)
    
    def get_engine_voice_pack(self, engine_name: str, voice_pack_name: str) -> Optional[Dict[str, Any]]:
        """获取指定引擎的指定语音包"""
        engine_packs = self.engine_voice_packs.get(engine_name, {})
        return engine_packs.get(voice_pack_name)
    
    def get_available_voice_packs(self) -> List[str]:
        """获取可用的基础语音包列表"""
        return list(self.voice_packs.keys())
    
    def get_available_engine_voice_packs(self, engine_name: str) -> List[str]:
        """获取指定引擎可用的语音包列表"""
        engine_packs = self.engine_voice_packs.get(engine_name, {})
        return list(engine_packs.keys())
    
    def is_voice_pack_available(self, voice_pack_name: str) -> bool:
        """检查基础语音包是否可用"""
        return voice_pack_name in self.voice_packs
    
    def is_engine_voice_pack_available(self, engine_name: str, voice_pack_name: str) -> bool:
        """检查引擎语音包是否可用"""
        engine_packs = self.engine_voice_packs.get(engine_name, {})
        return voice_pack_name in engine_packs
    
    def get_voice_packs_by_engine(self, engine_name: str) -> List[str]:
        """获取指定引擎支持的语音包（兼容性方法）"""
        return self.get_available_engine_voice_packs(engine_name)
    
    def get_voice_pack_info(self, voice_pack_name: str, engine_name: str = None) -> Optional[Dict[str, Any]]:
        """获取语音包信息，包括引擎特定信息"""
        if engine_name:
            # 获取引擎特定的语音包
            return self.get_engine_voice_pack(engine_name, voice_pack_name)
        else:
            # 获取基础语音包
            return self.get_voice_pack(voice_pack_name)
    
    def get_engine_voice_pack_mapping(self, engine_name: str) -> Dict[str, str]:
        """获取引擎语音包到基础语音包的映射"""
        mapping = {}
        engine_packs = self.engine_voice_packs.get(engine_name, {})
        for engine_pack_name, pack_config in engine_packs.items():
            base_pack = pack_config.get("base_pack", "")
            if base_pack:
                mapping[base_pack] = engine_pack_name
        return mapping


# 全局实例
voice_pack_manager = VoicePackManager() 