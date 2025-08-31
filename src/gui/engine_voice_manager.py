"""
引擎和语音包管理器
实现引擎与语音包的对应关系
"""

import json
import os
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EngineVoiceManager:
    """引擎和语音包管理器"""
    
    def __init__(self):
        self.engine_voice_mapping = {}
        self.config = self._load_config()
        self._initialize_mappings()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "engine_voice_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
        
        # 返回默认配置
        return {
            "engine_display_names": {},
            "engine_order": ["edge_tts", "cosyvoice", "gtts", "pyttsx3"],
            "voice_pack_categories": {},
            "ui_settings": {
                "show_engine_info": True,
                "show_voice_pack_info": True,
                "group_voices_by_category": False,
                "max_voices_per_engine": 50
            }
        }
    
    def _initialize_mappings(self):
        """初始化引擎与语音包的映射关系"""
        self.engine_voice_mapping = {
            "edge_tts": self._get_edge_tts_voices,
            "cosyvoice": self._get_cosyvoice_voices,
            "gtts": self._get_gtts_voices,
            "pyttsx3": self._get_pyttsx3_voices
        }
    
    def get_voices_for_engine(self, engine_name):
        """获取指定引擎的语音包列表"""
        try:
            if engine_name in self.engine_voice_mapping:
                return self.engine_voice_mapping[engine_name]()
            else:
                return self._get_basic_voices()
        except Exception as e:
            logger.error(f"获取引擎 {engine_name} 的语音包失败: {e}")
            return self._get_basic_voices()
    
    def _get_edge_tts_voices(self):
        """获取Edge-TTS语音包"""
        try:
            from src.core.edge_tts_integration import edge_tts_integration
            if hasattr(edge_tts_integration, 'available_voices'):
                voices = edge_tts_integration.available_voices
                voice_list = []
                
                if isinstance(voices, list):
                    # voices是列表格式，包含字典
                    for voice_info in voices:
                        if isinstance(voice_info, dict):
                            voice_id = voice_info.get('name', 'Unknown')
                            friendly_name = voice_info.get('friendly_name', voice_id)
                            gender = voice_info.get('gender', 'Unknown')
                            display_name = f"{friendly_name} ({gender})"
                            voice_list.append((display_name, voice_id))
                elif isinstance(voices, dict):
                    # voices是字典格式
                    for voice_id, voice_info in voices.items():
                        display_name = f"{voice_info.get('name', voice_id)} ({voice_info.get('gender', 'Unknown')})"
                        voice_list.append((display_name, voice_id))
                
                return voice_list if voice_list else self._get_basic_voices()
            else:
                return self._get_basic_voices()
        except Exception as e:
            logger.error(f"加载Edge-TTS语音包失败: {e}")
            return self._get_basic_voices()
    
    def _get_cosyvoice_voices(self):
        """获取CosyVoice语音包"""
        try:
            from src.core.real_cosyvoice_integration import real_cosyvoice_integration
            if hasattr(real_cosyvoice_integration, 'available_voices'):
                voices = real_cosyvoice_integration.available_voices
                voice_list = []
                
                if voices:
                    for voice_id, voice_info in voices.items():
                        display_name = f"{voice_info.get('name', voice_id)} ({voice_info.get('gender', 'Unknown')})"
                        voice_list.append((display_name, voice_id))
                    return voice_list
            
            # CosyVoice默认语音包
            cosyvoice_voices = [
                ("默认语音", "default"),
                ("温暖女声", "female_warm"),
                ("深沉男声", "male_deep"),
                ("可爱童声", "child_cute"),
                ("专业播音", "professional"),
                ("情感朗读", "emotional")
            ]
            return cosyvoice_voices
            
        except Exception as e:
            logger.error(f"加载CosyVoice语音包失败: {e}")
            return [("默认语音", "default"), ("温暖女声", "female_warm"), ("深沉男声", "male_deep")]
    
    def _get_gtts_voices(self):
        """获取gTTS语音包"""
        try:
            # gTTS支持的语言和方言
            gtts_voices = [
                ("中文 (普通话)", "zh-cn"),
                ("中文 (台湾)", "zh-tw"),
                ("English (US)", "en-us"),
                ("English (UK)", "en-uk"),
                ("English (Australia)", "en-au"),
                ("日本語", "ja"),
                ("한국어", "ko"),
                ("Français", "fr"),
                ("Deutsch", "de"),
                ("Español", "es"),
                ("Italiano", "it"),
                ("Português", "pt"),
                ("Русский", "ru")
            ]
            return gtts_voices
        except Exception as e:
            logger.error(f"加载gTTS语音包失败: {e}")
            return [("中文 (普通话)", "zh-cn"), ("English (US)", "en-us")]
    
    def _get_pyttsx3_voices(self):
        """获取pyttsx3语音包"""
        try:
            from src.core.pyttsx3_integration import pyttsx3_integration
            if hasattr(pyttsx3_integration, 'available_voices'):
                voices = pyttsx3_integration.available_voices
                voice_list = []
                
                if voices:
                    for voice_info in voices:
                        voice_id = voice_info.get('id', 'Unknown')
                        name = voice_info.get('name', voice_id)
                        gender = voice_info.get('gender', 'Unknown')
                        display_name = f"{name} ({gender})"
                        voice_list.append((display_name, voice_id))
                    return voice_list
            
            # pyttsx3默认语音包
            pyttsx3_voices = [
                ("系统默认", "default"),
                ("Microsoft Zira (Female)", "zira"),
                ("Microsoft David (Male)", "david"),
                ("Microsoft Mark (Male)", "mark")
            ]
            return pyttsx3_voices
            
        except Exception as e:
            logger.error(f"加载pyttsx3语音包失败: {e}")
            return [("系统默认", "default")]
    
    def _get_basic_voices(self):
        """获取基础语音包"""
        return [
            ("默认语音", "default"),
            ("女声", "female"),
            ("男声", "male"),
            ("童声", "child")
        ]
    
    def get_available_engines(self):
        """获取可用的引擎列表（按配置顺序）"""
        try:
            from src.core.tts_engine import tts_engine
            available_engines = tts_engine.get_available_engines()
            
            # 按配置顺序排序
            engine_order = self.config.get("engine_order", [])
            ordered_engines = []
            
            # 先添加配置中指定顺序的引擎
            for engine in engine_order:
                if engine in available_engines:
                    ordered_engines.append(engine)
            
            # 再添加其他可用引擎
            for engine in available_engines:
                if engine not in ordered_engines:
                    ordered_engines.append(engine)
            
            return ordered_engines
        except Exception as e:
            logger.error(f"获取可用引擎失败: {e}")
            return ["edge_tts", "cosyvoice", "gtts", "pyttsx3"]
    
    def get_engine_display_name(self, engine_name):
        """获取引擎显示名称"""
        display_names = self.config.get("engine_display_names", {})
        return display_names.get(engine_name, engine_name)
    
    def should_group_voices_by_category(self):
        """是否按类别分组显示语音包"""
        return self.config.get("ui_settings", {}).get("group_voices_by_category", False)
    
    def get_max_voices_per_engine(self):
        """获取每个引擎最大显示语音数量"""
        return self.config.get("ui_settings", {}).get("max_voices_per_engine", 50)
    
    def get_engine_info(self, engine_name):
        """获取引擎信息"""
        engine_info_mapping = {
            "edge_tts": {
                "name": "Edge-TTS",
                "description": "微软Edge浏览器TTS服务",
                "features": ["高质量", "多语言", "在线服务"],
                "voice_count": "36+ 中文语音"
            },
            "cosyvoice": {
                "name": "CosyVoice2.0",
                "description": "阿里巴巴开源TTS模型",
                "features": ["高质量", "本地推理", "情感表达"],
                "voice_count": "6+ 语音风格"
            },
            "gtts": {
                "name": "Google TTS",
                "description": "Google文本转语音服务",
                "features": ["多语言", "在线服务", "免费"],
                "voice_count": "13+ 语言"
            },
            "pyttsx3": {
                "name": "pyttsx3",
                "description": "本地系统TTS引擎",
                "features": ["离线", "跨平台", "系统集成"],
                "voice_count": "系统语音"
            }
        }
        
        return engine_info_mapping.get(engine_name, {
            "name": engine_name,
            "description": "未知引擎",
            "features": [],
            "voice_count": "未知"
        })


# 创建全局实例
engine_voice_manager = EngineVoiceManager()