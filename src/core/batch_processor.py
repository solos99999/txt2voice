"""
批量处理器
支持批量文本转语音功能
"""

import os
import csv
from typing import List, Dict, Any
from ..utils.logger import get_logger
from .tts_engine import tts_engine
from ..audio.audio_processor import audio_processor


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.output_dir = "batch_output"
    
    def process_text_list(self, texts: List[str], voice_pack: str = "default",
                         speed: float = 1.0, pitch: int = 0, energy: float = 1.0) -> Dict[str, Any]:
        """处理文本列表"""
        if not texts:
            return {"success": False, "message": "没有文本需要处理"}
        
        # 确保模型已加载
        if not tts_engine.is_model_loaded():
            if not tts_engine.load_model():
                return {"success": False, "message": "模型加载失败"}
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        results = []
        success_count = 0
        
        for i, text in enumerate(texts):
            try:
                self.logger.info(f"处理第 {i+1}/{len(texts)} 个文本")
                
                # 执行语音合成
                audio = tts_engine.synthesize(
                    text=text,
                    voice_pack=voice_pack,
                    speed=speed,
                    pitch=pitch,
                    energy=energy
                )
                
                if audio is not None:
                    # 保存音频文件
                    output_filename = f"batch_{i+1:03d}.wav"
                    output_path = os.path.join(self.output_dir, output_filename)
                    audio_processor.save_audio(audio, output_path)
                    
                    results.append({
                        "index": i + 1,
                        "text": text,
                        "status": "success",
                        "output_file": output_path
                    })
                    success_count += 1
                else:
                    results.append({
                        "index": i + 1,
                        "text": text,
                        "status": "failed",
                        "error": "语音合成失败"
                    })
                    
            except Exception as e:
                self.logger.error(f"处理文本失败: {e}")
                results.append({
                    "index": i + 1,
                    "text": text,
                    "status": "failed",
                    "error": str(e)
                })
        
        report = {
            "success": True,
            "total_texts": len(texts),
            "success_count": success_count,
            "failed_count": len(texts) - success_count,
            "results": results
        }
        
        self.logger.info(f"批量处理完成: {success_count}/{len(texts)} 成功")
        return report
    
    def export_template_csv(self, file_path: str):
        """导出CSV模板"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['text', 'voice_pack', 'speed', 'pitch', 'energy'])
                writer.writerow(['示例文本', 'default', '1.0', '0', '1.0'])
            
            self.logger.info(f"CSV模板已导出到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"导出CSV模板失败: {e}")
            raise


# 全局批量处理器实例
batch_processor = BatchProcessor() 