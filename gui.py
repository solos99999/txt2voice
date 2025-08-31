#!/usr/bin/env python3
"""
CosyVoice2.0 TTS系统图形界面启动脚本
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.gui.main_window import MainWindow
from src.utils.logger import setup_logger
from src.core.tts_engine import tts_engine


def main():
    """主函数"""
    # 设置日志
    logger = setup_logger()
    logger.info("启动CosyVoice2.0 TTS图形界面")
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName("CosyVoice2.0 TTS")
    app.setApplicationVersion("1.0.0")
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 预加载模型
    logger.info("正在加载TTS模型...")
    if tts_engine.load_model():
        logger.info("模型加载成功")
    else:
        logger.warning("模型加载失败，将使用模拟模型")
    
    # 运行应用
    logger.info("图形界面启动完成")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 