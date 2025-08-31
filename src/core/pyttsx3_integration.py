"""
pyttsx3引擎集成
使用离线TTS引擎
"""

import os
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Pyttsx3Integration:
    """pyttsx3引擎集成类"""
    
    def __init__(self):
        self.model = None
        self.sample_rate = 22050
        self.available_voices = []
        logger.info("pyttsx3集成初始化")
    
    def load_model(self) -> bool:
        """加载pyttsx3模型"""
        try:
            logger.info("正在加载pyttsx3模型...")
            
            try:
                import pyttsx3
                logger.info("✓ pyttsx3可用")
                self.model = "pyttsx3"
                
                # 获取可用语音列表
                self._load_available_voices()
                return True
                
            except ImportError:
                logger.error("pyttsx3未安装")
                return False
                
        except Exception as e:
            logger.error(f"加载pyttsx3模型失败: {e}")
            return False
    
    def _load_available_voices(self):
        """加载可用的语音列表"""
        try:
            import pyttsx3
            
            # 初始化引擎
            engine = pyttsx3.init()
            
            # 获取所有语音
            voices = engine.getProperty('voices')
            
            # 分析语音特征
            voice_info = []
            for voice in voices:
                voice_name = voice.name.lower()
                voice_id = voice.id.lower()
                
                # 分析特征
                features = []
                if 'chinese' in voice_name or 'zh' in voice_id:
                    features.append("中文")
                if 'english' in voice_name or 'en' in voice_id:
                    features.append("英文")
                if 'female' in voice_name or 'woman' in voice_name or 'huihui' in voice_name:
                    features.append("女声")
                elif 'male' in voice_name or 'man' in voice_name or 'zira' in voice_name:
                    features.append("男声")
                
                voice_info.append({
                    'name': voice.name,
                    'id': voice.id,
                    'features': features
                })
            
            self.available_voices = voice_info
            logger.info(f"找到 {len(voice_info)} 个语音")
            
            # 显示语音列表
            for voice in voice_info:
                logger.info(f"  - {voice['name']}: {', '.join(voice['features'])}")
                
        except Exception as e:
            logger.error(f"加载语音列表失败: {e}")
            self.available_voices = []
    
    def get_voice_pack_mapping(self) -> Dict[str, str]:
        """获取语音包到pyttsx3语音的映射"""
        if not self.available_voices:
            return {}
        
        voice_mapping = {}
        
        # 查找中文女声
        chinese_female = None
        for voice in self.available_voices:
            if "中文" in voice['features'] and "女声" in voice['features']:
                chinese_female = voice['id']
                break
        
        # 查找英文男声
        english_male = None
        for voice in self.available_voices:
            if "英文" in voice['features'] and "男声" in voice['features']:
                english_male = voice['id']
                break
        
        # 查找中文男声
        chinese_male = None
        for voice in self.available_voices:
            if "中文" in voice['features'] and "男声" in voice['features']:
                chinese_male = voice['id']
                break
        
        # 映射语音包
        if chinese_female:
            voice_mapping['default'] = chinese_female
            voice_mapping['female'] = chinese_female
            voice_mapping['child'] = chinese_female
            voice_mapping['angry'] = chinese_female
            voice_mapping['sad'] = chinese_female
        
        if english_male:
            voice_mapping['male'] = english_male
            voice_mapping['robot'] = english_male
        elif chinese_male:
            voice_mapping['male'] = chinese_male
            voice_mapping['robot'] = chinese_male
        
        if chinese_male:
            voice_mapping['elder'] = chinese_male
        
        return voice_mapping
    
    def synthesize(self, text: str, voice_pack: str = "default", 
                   speed: float = 1.0, pitch: int = 0, energy: float = 1.0) -> Optional[np.ndarray]:
        """使用pyttsx3进行语音合成"""
        try:
            if self.model is None:
                logger.error("pyttsx3模型未加载")
                return None
            
            import pyttsx3
            import tempfile
            import soundfile as sf
            
            # 初始化引擎
            engine = pyttsx3.init()
            
            # 设置参数
            engine.setProperty('rate', int(200 * speed))  # 语速
            engine.setProperty('volume', energy)  # 音量
            
            # 根据voice_pack选择语音
            voice_mapping = self.get_voice_pack_mapping()
            
            # 处理引擎特定的语音包名称
            if voice_pack.startswith("pyttsx3_"):
                base_voice_pack = voice_pack[8:]  # 移除"pyttsx3_"前缀
            else:
                base_voice_pack = voice_pack
            
            voice_id = voice_mapping.get(base_voice_pack, voice_mapping.get('default'))
            
            if voice_id:
                engine.setProperty('voice', voice_id)
                logger.info(f"pyttsx3使用语音: {voice_pack} -> {voice_id}")
            else:
                logger.warning(f"pyttsx3未找到语音包 {voice_pack} 的映射")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 生成语音
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
            # 读取音频
            audio, sr = sf.read(temp_path)
            
            # 重采样
            if sr != self.sample_rate:
                import librosa
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
            
            # 删除临时文件
            os.remove(temp_path)
            
            # 检查音频是否为空
            if len(audio) == 0:
                logger.error("pyttsx3生成的音频为空")
                return None
            
            # 确保音频是浮点数格式
            audio = audio.astype(np.float32)
            
            # 归一化音频
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.8
            
            logger.info("pyttsx3语音合成完成")
            return audio
            
        except Exception as e:
            logger.error(f"pyttsx3合成失败: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": "pyttsx3 (离线TTS)",
            "version": "1.0",
            "model_type": self.model,
            "loaded": self.model is not None,
            "sample_rate": self.sample_rate,
            "available_voices": len(self.available_voices)
        }


# 全局实例
pyttsx3_integration = Pyttsx3Integration() 