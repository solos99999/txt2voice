"""
gTTS引擎集成
使用Google Text-to-Speech服务
"""

import os
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path
from ..utils.logger import get_logger

logger = get_logger(__name__)


class GTTSIntegration:
    """gTTS引擎集成类"""
    
    def __init__(self):
        self.model = None
        self.sample_rate = 22050
        logger.info("gTTS集成初始化")
    
    def load_model(self) -> bool:
        """加载gTTS模型"""
        try:
            logger.info("正在加载gTTS模型...")
            
            try:
                from gtts import gTTS
                logger.info("✓ gTTS可用")
                self.model = "gtts"
                return True
                
            except ImportError:
                logger.error("gTTS未安装")
                return False
                
        except Exception as e:
            logger.error(f"加载gTTS模型失败: {e}")
            return False
    
    def get_voice_pack_mapping(self) -> Dict[str, dict]:
        """获取语音包到gTTS语言配置的映射"""
        return {
            "default": {"lang": "zh-cn", "tld": "com"},
            "female": {"lang": "zh-cn", "tld": "com"},
            "male": {"lang": "zh-tw", "tld": "com"},
            "child": {"lang": "zh-cn", "tld": "com"},
            "elder": {"lang": "zh-cn", "tld": "com"},
            "robot": {"lang": "en", "tld": "com"},
            "angry": {"lang": "zh-cn", "tld": "com"},
            "sad": {"lang": "zh-cn", "tld": "com"}
        }
    
    def synthesize(self, text: str, voice_pack: str = "default", 
                   speed: float = 1.0, pitch: int = 0, energy: float = 1.0) -> Optional[np.ndarray]:
        """使用gTTS进行语音合成"""
        try:
            if self.model is None:
                logger.error("gTTS模型未加载")
                return None
            
            # 获取语言配置
            language_configs = self.get_voice_pack_mapping()
            config = language_configs.get(voice_pack, language_configs["default"])
            
            logger.info(f"gTTS合成文本: {text[:50]}... (语言: {config['lang']})")
            
            from gtts import gTTS
            import tempfile
            import soundfile as sf
            
            # 创建临时文件
            temp_file = "temp_gtts.mp3"
            
            # 生成语音
            tts = gTTS(text=text, lang=config["lang"], 
                      tld=config["tld"], 
                      slow=(speed < 0.8))
            tts.save(temp_file)
            
            # 读取音频
            audio, sr = sf.read(temp_file)
            
            # 重采样
            if sr != self.sample_rate:
                import librosa
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
            
            # 删除临时文件
            os.remove(temp_file)
            
            logger.info(f"gTTS语音合成完成 (语言: {config['lang']})")
            return audio.astype(np.float32)
            
        except Exception as e:
            logger.error(f"gTTS合成失败: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": "gTTS (Google TTS服务)",
            "version": "1.0",
            "model_type": self.model,
            "loaded": self.model is not None,
            "sample_rate": self.sample_rate
        }


# 全局实例
gtts_integration = GTTSIntegration() 