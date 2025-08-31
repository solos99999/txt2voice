"""
Edge-TTS引擎集成
使用微软Edge浏览器的TTS服务
"""

import os
import asyncio
import edge_tts
import numpy as np
from typing import Optional, Dict, Any, List
from pathlib import Path
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EdgeTTSIntegration:
    """Edge-TTS引擎集成类"""
    
    def __init__(self):
        self.model = None
        self.sample_rate = 22050
        self.available_voices = []
        logger.info("Edge-TTS集成初始化")
    
    def load_model(self) -> bool:
        """加载Edge-TTS模型"""
        try:
            logger.info("正在加载Edge-TTS模型...")
            
            # 检查edge-tts是否可用
            try:
                import edge_tts
                logger.info("✓ Edge-TTS可用")
                self.model = "edge_tts"
                
                # 获取可用语音列表
                self._load_available_voices()
                return True
                
            except ImportError:
                logger.error("Edge-TTS未安装")
                return False
                
        except Exception as e:
            logger.error(f"加载Edge-TTS模型失败: {e}")
            return False
    
    def _load_available_voices(self):
        """加载可用的语音列表"""
        try:
            async def get_voices():
                voices = await edge_tts.list_voices()
                return voices
            
            # 运行异步函数获取语音列表
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            voices = loop.run_until_complete(get_voices())
            loop.close()
            
            # 过滤中文语音
            chinese_voices = []
            for voice in voices:
                # 检查语音对象的结构
                if isinstance(voice, dict):
                    # 处理字典格式
                    short_name = voice.get('ShortName', voice.get('Name', ''))
                    friendly_name = voice.get('FriendlyName', voice.get('DisplayName', ''))
                    gender = voice.get('Gender', 'Unknown')
                    locale = voice.get('Locale', voice.get('Language', ''))
                else:
                    # 处理对象格式
                    short_name = getattr(voice, 'short_name', getattr(voice, 'name', ''))
                    friendly_name = getattr(voice, 'friendly_name', getattr(voice, 'display_name', ''))
                    gender = getattr(voice, 'gender', 'Unknown')
                    locale = getattr(voice, 'locale', getattr(voice, 'language', ''))
                
                if 'zh-CN' in short_name or 'zh-CN' in locale:
                    chinese_voices.append({
                        'name': short_name,
                        'friendly_name': friendly_name,
                        'gender': gender,
                        'locale': locale
                    })
            
            self.available_voices = chinese_voices
            logger.info(f"找到 {len(chinese_voices)} 个中文语音")
            
            # 显示语音列表
            for voice in chinese_voices:
                logger.info(f"  - {voice['name']}: {voice['friendly_name']} ({voice['gender']})")
                
        except Exception as e:
            logger.error(f"加载语音列表失败: {e}")
            self.available_voices = []
    
    def get_voice_pack_mapping(self) -> Dict[str, str]:
        """获取语音包到Edge-TTS语音的映射"""
        if not self.available_voices:
            return {}
        
        # 根据性别和特征映射语音包
        voice_mapping = {}
        
        # 查找女声
        female_voices = [v for v in self.available_voices if v['gender'] == 'Female']
        if female_voices:
            voice_mapping['female'] = female_voices[0]['name']
            voice_mapping['default'] = female_voices[0]['name']
        
        # 查找男声
        male_voices = [v for v in self.available_voices if v['gender'] == 'Male']
        if male_voices:
            voice_mapping['male'] = male_voices[0]['name']
        
        # 为其他语音包分配语音
        if female_voices:
            voice_mapping['child'] = female_voices[0]['name']  # 儿童用女声
            voice_mapping['angry'] = female_voices[0]['name']  # 愤怒用女声
            voice_mapping['sad'] = female_voices[0]['name']    # 悲伤用女声
        
        if male_voices:
            voice_mapping['elder'] = male_voices[0]['name']    # 老年用男声
            voice_mapping['robot'] = male_voices[0]['name']    # 机器人用男声
        
        return voice_mapping
    
    def synthesize(self, text: str, voice_pack: str = "default", 
                   speed: float = 1.0, pitch: int = 0, energy: float = 1.0) -> Optional[np.ndarray]:
        """使用Edge-TTS进行语音合成"""
        try:
            if self.model is None:
                logger.error("Edge-TTS模型未加载")
                return None
            
            # 获取语音包映射
            voice_mapping = self.get_voice_pack_mapping()
            
            # 处理引擎特定的语音包名称
            if voice_pack.startswith("edge_tts_"):
                base_voice_pack = voice_pack[9:]  # 移除"edge_tts_"前缀
            else:
                base_voice_pack = voice_pack
            
            # 如果传入的是完整的Edge-TTS语音ID，直接使用
            if base_voice_pack.startswith("zh-CN-") and base_voice_pack.endswith("Neural"):
                voice = base_voice_pack
            else:
                voice = voice_mapping.get(base_voice_pack, voice_mapping.get('default', 'zh-CN-XiaoxiaoNeural'))
            
            logger.info(f"Edge-TTS合成文本: {text[:50]}... (语音: {voice})")
            
            # 设置参数
            rate = f"{int((speed - 1) * 100):+d}%"
            volume = f"{int((energy - 1) * 100):+d}%"
            
            async def generate_speech():
                try:
                    # 创建临时文件
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    # 使用save方法而不是流式处理
                    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
                    await communicate.save(temp_path)
                    
                    # 检查文件是否生成成功
                    if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                        logger.error("Edge-TTS生成的音频文件为空或不存在")
                        return None
                    
                    # 读取音频文件
                    import soundfile as sf
                    audio, sr = sf.read(temp_path)
                    
                    # 清理临时文件
                    os.unlink(temp_path)
                    
                    # 重采样到目标采样率
                    if sr != self.sample_rate:
                        import librosa
                        audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
                    
                    logger.info("Edge-TTS语音合成完成")
                    return audio.astype(np.float32)
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Edge-TTS异步合成失败: {error_msg}")
                    
                    # 检查是否是网络相关错误
                    if "403" in error_msg or "Invalid response status" in error_msg:
                        logger.warning("Edge-TTS网络访问受限，可能是地区限制或服务变更")
                    elif "timeout" in error_msg.lower():
                        logger.warning("Edge-TTS请求超时")
                    elif "connection" in error_msg.lower():
                        logger.warning("Edge-TTS连接失败")
                    
                    return None
            
            # 运行异步函数，带重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    audio = loop.run_until_complete(generate_speech())
                    loop.close()
                    
                    if audio is not None and len(audio) > 0:
                        return audio
                    else:
                        logger.warning(f"Edge-TTS第{attempt + 1}次尝试未返回音频数据")
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(1)  # 等待1秒后重试
                            continue
                        else:
                            logger.error("Edge-TTS所有重试都失败了")
                            return None
                    
                except Exception as e:
                    logger.error(f"Edge-TTS第{attempt + 1}次尝试失败: {e}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2)  # 等待2秒后重试
                        continue
                    else:
                        logger.error("Edge-TTS所有重试都失败了")
                        return None
            
            return None
            
        except Exception as e:
            logger.error(f"Edge-TTS合成失败: {e}")
            return None
    

    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": "Edge-TTS (微软TTS服务)",
            "version": "1.0",
            "model_type": self.model,
            "loaded": self.model is not None,
            "sample_rate": self.sample_rate,
            "available_voices": len(self.available_voices)
        }

    def test_network_connection(self) -> bool:
        """测试Edge-TTS网络连接"""
        try:
            import asyncio
            import edge_tts
            
            async def test_connection():
                try:
                    # 尝试获取语音列表来测试连接
                    voices = await edge_tts.list_voices()
                    return len(voices) > 0
                except Exception as e:
                    logger.error(f"Edge-TTS网络连接测试失败: {e}")
                    return False
            
            # 运行测试
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_connection())
            loop.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Edge-TTS网络连接测试异常: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态信息"""
        status = {
            "available": self.model is not None,
            "network_connected": False,
            "voice_count": len(self.available_voices),
            "error_message": None
        }
        
        if self.model is not None:
            status["network_connected"] = self.test_network_connection()
        
        return status


# 全局实例
edge_tts_integration = EdgeTTSIntegration() 