#!/usr/bin/env python3
"""
CosyVoice2.0 本地文本转语音系统
主程序入口
"""

import os
import sys
import click
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import setup_logger, get_logger
from src.utils.config_loader import config_loader
from src.core.tts_engine import tts_engine
from src.audio.audio_processor import audio_processor


# 设置日志
logger = setup_logger()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """CosyVoice2.0 本地文本转语音系统"""
    pass


@cli.command()
@click.option('--text', '-t', required=True, help='要转换的文本内容')
@click.option('--output', '-o', default='output.wav', help='输出音频文件路径')
@click.option('--voice-pack', '-v', default='default', help='语音包名称')
@click.option('--speed', '-s', default=1.0, type=float, help='语速 (0.5-2.0)')
@click.option('--pitch', '-p', default=0, type=int, help='音调偏移 (-12-12)')
@click.option('--energy', '-e', default=1.0, type=float, help='音量因子 (0.1-2.0)')
@click.option('--play', is_flag=True, help='合成后自动播放')
def synthesize(text, output, voice_pack, speed, pitch, energy, play):
    """文本转语音合成"""
    try:
        logger.info("开始文本转语音合成")
        
        # 检查模型是否已加载
        if not tts_engine.is_model_loaded():
            logger.info("正在加载模型...")
            if not tts_engine.load_model():
                logger.error("模型加载失败")
                return
        
        # 检查语音包是否存在
        available_packs = tts_engine.get_available_voice_packs()
        if voice_pack not in available_packs:
            logger.warning(f"语音包 '{voice_pack}' 不存在，使用默认语音包")
            voice_pack = 'default'
        
        # 执行语音合成
        audio = tts_engine.synthesize(
            text=text,
            voice_pack=voice_pack,
            speed=speed,
            pitch=pitch,
            energy=energy
        )
        
        if audio is None:
            logger.error("语音合成失败")
            return
        
        # 保存音频文件
        audio_processor.save_audio(audio, output)
        
        # 获取音频信息
        audio_info = audio_processor.get_audio_info(audio, tts_engine.sample_rate)
        logger.info(f"音频信息: 时长 {audio_info['duration']:.2f}秒, "
                   f"采样率 {audio_info['sample_rate']}Hz")
        
        # 自动播放
        if play:
            logger.info("开始播放音频...")
            audio_processor.play_audio(audio, tts_engine.sample_rate)
        
        logger.info(f"语音合成完成，文件已保存: {output}")
        
    except Exception as e:
        logger.error(f"语音合成过程中发生错误: {e}")


@cli.command()
def list_voice_packs():
    """列出可用的语音包"""
    try:
        available_packs = tts_engine.get_available_voice_packs()
        
        if not available_packs:
            logger.warning("没有可用的语音包")
            return
        
        logger.info("可用的语音包:")
        for pack_name in available_packs:
            pack_info = tts_engine.get_voice_pack_info(pack_name)
            if pack_info:
                logger.info(f"  - {pack_name}: {pack_info.get('name', 'Unknown')} "
                           f"({pack_info.get('description', 'No description')})")
            else:
                logger.info(f"  - {pack_name}")
                
    except Exception as e:
        logger.error(f"获取语音包列表失败: {e}")


@cli.command()
@click.option('--config-path', '-c', default='config/config.yaml', help='配置文件路径')
def show_config(config_path):
    """显示当前配置"""
    try:
        logger.info("当前配置:")
        
        # 模型配置
        model_config = config_loader.get('model', {})
        logger.info("模型配置:")
        for key, value in model_config.items():
            logger.info(f"  {key}: {value}")
        
        # 音频配置
        audio_config = config_loader.get('audio', {})
        logger.info("音频配置:")
        for key, value in audio_config.items():
            logger.info(f"  {key}: {value}")
        
        # 输出配置
        output_config = config_loader.get('output', {})
        logger.info("输出配置:")
        for key, value in output_config.items():
            logger.info(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"显示配置失败: {e}")


@cli.command()
def test():
    """测试TTS系统"""
    try:
        logger.info("开始TTS系统测试")
        
        # 测试模型加载
        logger.info("1. 测试模型加载...")
        if tts_engine.load_model():
            logger.info("✓ 模型加载成功")
        else:
            logger.error("✗ 模型加载失败")
            return
        
        # 测试语音合成
        logger.info("2. 测试语音合成...")
        test_text = "你好，这是CosyVoice2.0文本转语音系统的测试。"
        audio = tts_engine.synthesize(test_text)
        
        if audio is not None:
            logger.info("✓ 语音合成成功")
            
            # 保存测试音频
            test_output = "test_output.wav"
            audio_processor.save_audio(audio, test_output)
            logger.info(f"✓ 测试音频已保存: {test_output}")
            
            # 显示音频信息
            audio_info = audio_processor.get_audio_info(audio, tts_engine.sample_rate)
            logger.info(f"✓ 音频信息: 时长 {audio_info['duration']:.2f}秒")
        else:
            logger.error("✗ 语音合成失败")
        
        # 测试语音包
        logger.info("3. 测试语音包...")
        available_packs = tts_engine.get_available_voice_packs()
        logger.info(f"✓ 可用语音包数量: {len(available_packs)}")
        
        # 测试新语音包
        logger.info("4. 测试新语音包...")
        new_packs = ["child", "elder", "robot", "angry", "sad"]
        for pack in new_packs:
            if pack in available_packs:
                logger.info(f"✓ 语音包 {pack} 可用")
            else:
                logger.warning(f"⚠ 语音包 {pack} 不可用")
        
        logger.info("TTS系统测试完成")
        
    except Exception as e:
        logger.error(f"TTS系统测试失败: {e}")


@cli.command()
def batch():
    """批量处理测试"""
    try:
        from src.core.batch_processor import batch_processor
        
        logger.info("开始批量处理测试")
        
        # 准备测试文本
        test_texts = [
            "第一个测试文本。",
            "第二个测试文本。",
            "第三个测试文本。"
        ]
        
        # 执行批量处理
        result = batch_processor.process_text_list(
            texts=test_texts,
            voice_pack="default"
        )
        
        if result["success"]:
            logger.info(f"✓ 批量处理成功: {result['success_count']}/{result['total_texts']}")
        else:
            logger.error(f"✗ 批量处理失败: {result['message']}")
        
    except Exception as e:
        logger.error(f"批量处理测试失败: {e}")


if __name__ == "__main__":
    cli() 