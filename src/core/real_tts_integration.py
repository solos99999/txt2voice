"""
真实TTS模型集成
使用更容易集成的TTS模型来生成真实的语音
"""

import os
import torch
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RealTTSIntegration:
    """真实TTS模型集成类"""
    
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sample_rate = 22050
        logger.info(f"真实TTS集成初始化，设备: {self.device}")
    
    def load_model(self) -> bool:
        """加载真实的TTS模型"""
        try:
            logger.info("正在尝试加载真实的TTS模型...")
            
            # 尝试使用gTTS（Google Text-to-Speech）- 支持多种语言和方言
            try:
                from gtts import gTTS
                logger.info("✓ 找到gTTS，可以使用Google TTS服务")
                self.model = "gtts"
                return True
            except ImportError:
                logger.info("gTTS未安装，尝试其他方案")
            
            # 尝试使用pyttsx3（离线TTS）
            try:
                import pyttsx3
                logger.info("✓ 找到pyttsx3，可以使用离线TTS")
                self.model = "pyttsx3"
                return True
            except ImportError:
                logger.info("pyttsx3未安装，尝试其他方案")
            
            # 尝试使用edge-tts（微软Edge浏览器的TTS服务）
            try:
                import edge_tts
                logger.info("✓ 找到edge-tts，可以使用微软TTS服务")
                self.model = "edge_tts"
                return True
            except ImportError:
                logger.info("edge-tts未安装，尝试其他方案")
            
            logger.warning("未找到可用的TTS模型，将使用模拟音频")
            return False
            
        except Exception as e:
            logger.error(f"加载真实TTS模型失败: {e}")
            return False
    
    def synthesize(self, text: str, voice_pack: str = "default", 
                   speed: float = 1.0, pitch: int = 0, energy: float = 1.0) -> Optional[np.ndarray]:
        """使用真实的TTS进行语音合成"""
        try:
            if self.model is None:
                logger.error("真实TTS模型未加载")
                return None
            
            logger.info(f"真实TTS合成文本: {text[:50]}...")
            
            # 对于男声语音包，优先使用pyttsx3的英文男声
            if voice_pack == "male" and self.model == "gtts":
                try:
                    import pyttsx3
                    logger.info("男声语音包：尝试使用pyttsx3英文男声")
                    return self._synthesize_pyttsx3_male(text, speed, pitch, energy)
                except Exception as e:
                    logger.warning(f"pyttsx3男声失败，回退到gTTS: {e}")
            
            if self.model == "edge_tts":
                return self._synthesize_edge_tts(text, voice_pack, speed, pitch, energy)
            elif self.model == "gtts":
                return self._synthesize_gtts(text, voice_pack, speed, pitch, energy)
            elif self.model == "pyttsx3":
                return self._synthesize_pyttsx3(text, voice_pack, speed, pitch, energy)
            else:
                logger.error("未知的TTS模型类型")
                return None
                
        except Exception as e:
            logger.error(f"真实TTS合成失败: {e}")
            return None
    
    def _synthesize_edge_tts(self, text: str, voice_pack: str, speed: float, pitch: int, energy: float) -> Optional[np.ndarray]:
        """使用edge-tts合成"""
        try:
            import edge_tts
            import asyncio
            
            # 选择语音
            voice_map = {
                "default": "zh-CN-XiaoxiaoNeural",
                "female": "zh-CN-XiaoyiNeural", 
                "male": "zh-CN-YunxiNeural",
                "child": "zh-CN-XiaohanNeural",
                "elder": "zh-CN-YunyangNeural"
            }
            
            voice = voice_map.get(voice_pack, "zh-CN-XiaoxiaoNeural")
            
            # 设置参数
            rate = f"{int((speed - 1) * 100):+d}%"
            volume = f"{int((energy - 1) * 100):+d}%"
            
            async def generate_speech():
                try:
                    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
                    audio_data = b""
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            audio_data += chunk["data"]
                    return audio_data
                except Exception as e:
                    logger.error(f"edge-tts异步合成失败: {e}")
                    return None
            
            # 运行异步函数
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_data = loop.run_until_complete(generate_speech())
                loop.close()
                
                if audio_data is None:
                    logger.error("edge-tts未返回音频数据")
                    return None
                
                # 转换为numpy数组
                import io
                import soundfile as sf
                
                audio, sr = sf.read(io.BytesIO(audio_data))
                
                # 重采样到目标采样率
                if sr != self.sample_rate:
                    import librosa
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
                
                logger.info("edge-tts语音合成完成")
                return audio.astype(np.float32)
                
            except Exception as e:
                logger.error(f"edge-tts事件循环失败: {e}")
                return None
            
        except Exception as e:
            logger.error(f"edge-tts合成失败: {e}")
            # 如果是网络错误，尝试使用备用方案
            if "403" in str(e) or "network" in str(e).lower():
                logger.info("检测到网络问题，尝试使用备用TTS方案")
                return self._synthesize_fallback(text, voice_pack, speed, pitch, energy)
            return None
    
    def _synthesize_pyttsx3(self, text: str, voice_pack: str, speed: float, pitch: int, energy: float) -> Optional[np.ndarray]:
        """使用pyttsx3合成"""
        try:
            import pyttsx3
            import tempfile
            import soundfile as sf
            
            # 初始化引擎
            engine = pyttsx3.init()
            
            # 设置参数
            engine.setProperty('rate', int(200 * speed))  # 语速
            engine.setProperty('volume', energy)  # 音量
            
            # 根据voice_pack选择语音
            voices = engine.getProperty('voices')
            if voices:
                selected_voice = self._select_pyttsx3_voice(voices, voice_pack)
                if selected_voice:
                    engine.setProperty('voice', selected_voice.id)
                    logger.info(f"pyttsx3使用语音: {selected_voice.name} (ID: {selected_voice.id})")
                else:
                    # 如果没有找到合适的语音，使用第一个
                    engine.setProperty('voice', voices[0].id)
                    logger.warning(f"pyttsx3未找到合适的语音，使用默认: {voices[0].name}")
            
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
            
            logger.info("pyttsx3语音合成完成")
            return audio.astype(np.float32)
            
        except Exception as e:
            logger.error(f"pyttsx3合成失败: {e}")
            return None
    
    def _synthesize_gtts(self, text: str, voice_pack: str, speed: float, pitch: int, energy: float) -> Optional[np.ndarray]:
        """使用gTTS合成"""
        try:
            from gtts import gTTS
            import io
            import soundfile as sf
            
            # 根据voice_pack选择语言和方言
            language_config = self._get_gtts_language_config(voice_pack)
            
            # 创建临时文件
            temp_file = "temp_gtts.mp3"
            
            # 生成语音
            tts = gTTS(text=text, lang=language_config["lang"], 
                      tld=language_config["tld"], 
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
            
            logger.info(f"gTTS语音合成完成 (语言: {language_config['lang']}, 方言: {language_config['tld']})")
            return audio.astype(np.float32)
            
        except Exception as e:
            logger.error(f"gTTS合成失败: {e}")
            return None
    
    def _get_gtts_language_config(self, voice_pack: str) -> dict:
        """获取gTTS语言配置"""
        # gTTS支持的语言和方言配置
        language_configs = {
            "default": {"lang": "zh-cn", "tld": "com"},
            "female": {"lang": "zh-cn", "tld": "com"},  # 中文女声
            "male": {"lang": "en", "tld": "com"},       # 英文男声
            "child": {"lang": "zh-cn", "tld": "com"},   # 中文
            "elder": {"lang": "zh-cn", "tld": "com"},   # 中文
            "robot": {"lang": "en", "tld": "com"},      # 英文（机器人感）
            "angry": {"lang": "zh-cn", "tld": "com"},   # 中文
            "sad": {"lang": "zh-cn", "tld": "com"}      # 中文
        }
        
        return language_configs.get(voice_pack, language_configs["default"])
    
    def _select_pyttsx3_voice(self, voices, voice_pack: str):
        """根据voice_pack选择pyttsx3语音"""
        try:
            # 语音包到语音特征的映射
            voice_mapping = {
                "default": {"gender": "any", "language": "chinese"},
                "female": {"gender": "female", "language": "chinese"},
                "male": {"gender": "male", "language": "chinese"},
                "child": {"gender": "any", "language": "chinese", "style": "child"},
                "elder": {"gender": "any", "language": "chinese", "style": "elder"},
                "robot": {"gender": "any", "language": "english", "style": "robot"},
                "angry": {"gender": "any", "language": "chinese", "style": "angry"},
                "sad": {"gender": "any", "language": "chinese", "style": "sad"}
            }
            
            target_features = voice_mapping.get(voice_pack, {"gender": "any", "language": "chinese"})
            
            # 首先尝试找到目标语言的语音
            target_voices = []
            for voice in voices:
                voice_name = voice.name.lower()
                voice_id = voice.id.lower()
                
                # 检查语言
                if target_features["language"] == "chinese":
                    if ('chinese' in voice_name or 'zh' in voice_id or 
                        'mandarin' in voice_name or 'cantonese' in voice_name):
                        target_voices.append(voice)
                elif target_features["language"] == "english":
                    if ('english' in voice_name or 'en' in voice_id or 
                        'us' in voice_name or 'uk' in voice_name):
                        target_voices.append(voice)
            
            if not target_voices:
                # 如果没有找到目标语言的语音，使用所有可用语音
                target_voices = voices
            
            # 根据性别选择
            if target_features["gender"] == "female":
                for voice in target_voices:
                    voice_name = voice.name.lower()
                    if any(keyword in voice_name for keyword in ['female', 'woman', 'girl', 'lady', 'huihui']):
                        return voice
            elif target_features["gender"] == "male":
                for voice in target_voices:
                    voice_name = voice.name.lower()
                    if any(keyword in voice_name for keyword in ['male', 'man', 'boy', 'guy', 'zira']):
                        return voice
            
            # 如果没有找到特定性别的语音，返回第一个目标语言语音
            return target_voices[0] if target_voices else voices[0]
            
        except Exception as e:
            logger.error(f"选择pyttsx3语音失败: {e}")
            return voices[0] if voices else None
    
    def _synthesize_pyttsx3_male(self, text: str, speed: float, pitch: int, energy: float) -> Optional[np.ndarray]:
        """使用pyttsx3合成男声（强制使用英文男声）"""
        try:
            import pyttsx3
            import tempfile
            import soundfile as sf
            
            # 初始化引擎
            engine = pyttsx3.init()
            
            # 设置参数
            engine.setProperty('rate', int(200 * speed))  # 语速
            engine.setProperty('volume', energy)  # 音量
            
            # 强制使用英文男声
            voices = engine.getProperty('voices')
            if voices:
                # 查找英文男声
                male_voice = None
                for voice in voices:
                    voice_name = voice.name.lower()
                    if ('english' in voice_name or 'en' in voice_name) and ('zira' in voice_name or 'male' in voice_name):
                        male_voice = voice
                        break
                
                if male_voice:
                    engine.setProperty('voice', male_voice.id)
                    logger.info(f"pyttsx3使用英文男声: {male_voice.name}")
                else:
                    # 如果没有找到英文男声，使用第一个英文语音
                    for voice in voices:
                        voice_name = voice.name.lower()
                        if 'english' in voice_name or 'en' in voice_name:
                            engine.setProperty('voice', voice.id)
                            logger.info(f"pyttsx3使用英文语音: {voice.name}")
                            break
                    else:
                        # 如果连英文语音都没有，使用第一个
                        engine.setProperty('voice', voices[0].id)
                        logger.warning(f"pyttsx3未找到英文语音，使用默认: {voices[0].name}")
            
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
            
            logger.info("pyttsx3英文男声语音合成完成")
            return audio
            
        except Exception as e:
            logger.error(f"pyttsx3男声合成失败: {e}")
            return None
    
    def _synthesize_fallback(self, text: str, voice_pack: str, speed: float, pitch: int, energy: float) -> Optional[np.ndarray]:
        """备用合成方案"""
        try:
            logger.info("使用备用TTS方案")
            
            # 尝试使用gTTS
            try:
                return self._synthesize_gtts(text, voice_pack, speed, pitch, energy)
            except Exception as e:
                logger.warning(f"gTTS备用方案失败: {e}")
            
            # 如果gTTS也失败，使用简化的音频生成
            logger.info("使用简化音频生成作为最终备用方案")
            return self._generate_simple_audio(text, speed, pitch, energy)
            
        except Exception as e:
            logger.error(f"备用合成方案失败: {e}")
            return None
    
    def _generate_simple_audio(self, text: str, speed: float, pitch: int, energy: float) -> np.ndarray:
        """生成简化的音频（最终备用方案）"""
        # 基于文本长度生成音频
        text_length = len(text)
        audio_length = int(self.sample_rate * text_length * 0.15)
        
        # 创建基于文本特征的音频
        t = np.linspace(0, audio_length / self.sample_rate, audio_length)
        
        # 基础频率
        base_freq = 220
        audio = np.zeros(audio_length)
        
        # 添加基频和谐波
        audio += 0.3 * np.sin(2 * np.pi * base_freq * t)
        for i in range(2, 6):
            audio += 0.1 * np.sin(2 * np.pi * base_freq * i * t)
        
        # 添加噪声
        noise = np.random.normal(0, 0.05, audio_length)
        audio += noise
        
        # 应用参数调整
        if speed != 1.0:
            from scipy import interpolate
            original_length = len(audio)
            new_length = int(original_length / speed)
            x_old = np.linspace(0, 1, original_length)
            x_new = np.linspace(0, 1, new_length)
            f = interpolate.interp1d(x_old, audio, kind='linear')
            audio = f(x_new)
        
        if energy != 1.0:
            audio = audio * energy
        
        # 归一化
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        return audio.astype(np.float32)
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": f"真实TTS ({self.model})" if self.model else "未加载",
            "version": "1.0",
            "device": self.device,
            "model_type": self.model,
            "loaded": self.model is not None,
            "sample_rate": self.sample_rate
        }


# 全局实例
real_tts_integration = RealTTSIntegration() 