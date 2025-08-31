import os
import logging
import numpy as np
import soundfile as sf
from datetime import datetime
import re
from typing import Optional

logger = logging.getLogger(__name__)

class AudioProcessor:
    """音频处理器类"""
    
    def __init__(self, output_dir: str = "batch_output"):
        """
        初始化音频处理器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.player = None
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"创建输出目录: {output_dir}")
    
    def generate_unique_filename(self, engine_name: str, voice_pack: str, base_name: str = "audio") -> str:
        """
        生成唯一的文件名，包含引擎名、语音包名和时间戳
        
        Args:
            engine_name: 引擎名称
            voice_pack: 语音包名称
            base_name: 基础文件名
            
        Returns:
            str: 唯一的文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 清理语音包名称，移除特殊字符
        clean_voice_pack = re.sub(r'[^\w\-_]', '', voice_pack)
        
        # 构建文件名
        filename = f"{engine_name}_{clean_voice_pack}_{timestamp}.wav"
        
        # 确保文件名唯一
        counter = 1
        original_filename = filename
        while os.path.exists(os.path.join(self.output_dir, filename)):
            name_part = original_filename.replace('.wav', '')
            filename = f"{name_part}_{counter}.wav"
            counter += 1
        
        return filename
    
    def save_audio(self, audio_data: np.ndarray, sample_rate: int, 
                   engine_name: str, voice_pack: str, 
                   filename: Optional[str] = None) -> str:
        """
        保存音频数据到文件
        
        Args:
            audio_data: 音频数据数组
            sample_rate: 采样率
            engine_name: 引擎名称
            voice_pack: 语音包名称
            filename: 可选的文件名，如果不提供则自动生成
            
        Returns:
            str: 保存的文件路径
        """
        try:
            if filename is None:
                filename = self.generate_unique_filename(engine_name, voice_pack)
            
            filepath = os.path.join(self.output_dir, filename)
            
            # 确保音频数据格式正确
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # 归一化音频数据
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # 保存音频文件
            sf.write(filepath, audio_data, sample_rate)
            
            # 获取文件大小
            file_size = os.path.getsize(filepath)
            logger.info(f"音频文件已保存: {filepath} ({file_size} bytes)")
            
            return filepath
            
        except Exception as e:
            logger.error(f"保存音频文件失败: {e}")
            raise
    
    def load_audio(self, filepath: str) -> tuple:
        """
        加载音频文件
        
        Args:
            filepath: 音频文件路径
            
        Returns:
            tuple: (音频数据, 采样率)
        """
        try:
            audio_data, sample_rate = sf.read(filepath)
            logger.info(f"音频文件已加载: {filepath}")
            return audio_data, sample_rate
        except Exception as e:
            logger.error(f"加载音频文件失败: {e}")
            raise
    
    def play_audio(self, filepath: str):
        """
        播放音频文件
        
        Args:
            filepath: 音频文件路径
        """
        try:
            # 这里可以集成音频播放库，如pygame或playsound
            logger.info(f"播放音频: {filepath}")
            # 实际播放逻辑需要根据具体需求实现
        except Exception as e:
            logger.error(f"播放音频失败: {e}")
    
    def stop_audio(self):
        """停止音频播放"""
        try:
            if hasattr(self, 'player') and self.player:
                self.player.stop()
                self.player = None
                logger.info("音频播放已停止")
        except Exception as e:
            logger.error(f"停止音频播放失败: {e}")
    
    def get_audio_info(self, filepath: str) -> dict:
        """
        获取音频文件信息
        
        Args:
            filepath: 音频文件路径
            
        Returns:
            dict: 音频文件信息
        """
        try:
            audio_data, sample_rate = sf.read(filepath)
            file_size = os.path.getsize(filepath)
            duration = len(audio_data) / sample_rate
            
            info = {
                'filepath': filepath,
                'file_size': file_size,
                'sample_rate': sample_rate,
                'channels': 1 if audio_data.ndim == 1 else audio_data.shape[1],
                'duration': duration,
                'samples': len(audio_data)
            }
            
            return info
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            return {}
    
    def validate_audio(self, audio_data: np.ndarray, sample_rate: int) -> bool:
        """
        验证音频数据是否有效
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            
        Returns:
            bool: 是否有效
        """
        try:
            # 检查基本参数
            if audio_data is None or len(audio_data) == 0:
                return False
            
            if sample_rate <= 0:
                return False
            
            # 检查数据类型
            if not isinstance(audio_data, np.ndarray):
                return False
            
            # 检查数值范围
            if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                return False
            
            return True
        except Exception as e:
            logger.error(f"验证音频数据失败: {e}")
            return False

# 创建全局实例
audio_processor = AudioProcessor()