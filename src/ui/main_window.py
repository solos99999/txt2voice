"""
主窗口模块
提供完整的图形用户界面
"""

import sys
import os
from pathlib import Path
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTextEdit, QComboBox, QSlider, QLabel, QPushButton, QGroupBox,
    QFileDialog, QProgressBar, QMessageBox, QSplitter, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.tts_engine import tts_engine
from src.audio.audio_processor import audio_processor
from src.utils.logger import get_logger
from .audio_visualizer import AudioVisualizer


class SynthesisThread(QThread):
    """语音合成线程"""
    progress_updated = pyqtSignal(int)
    synthesis_completed = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, text: str, voice_pack: str, speed: float, pitch: int, energy: float):
        super().__init__()
        self.text = text
        self.voice_pack = voice_pack
        self.speed = speed
        self.pitch = pitch
        self.energy = energy
    
    def run(self):
        try:
            # 模拟进度更新
            for i in range(101):
                self.progress_updated.emit(i)
                self.msleep(50)
            
            # 执行语音合成
            audio = tts_engine.synthesize(
                text=self.text,
                voice_pack=self.voice_pack,
                speed=self.speed,
                pitch=self.pitch,
                energy=self.energy
            )
            
            if audio is not None:
                self.synthesis_completed.emit(audio)
            else:
                self.error_occurred.emit("语音合成失败")
                
        except Exception as e:
            self.error_occurred.emit(f"合成过程中发生错误: {str(e)}")


class AudioPlayer(QWidget):
    """音频播放器组件"""
    
    def __init__(self):
        super().__init__()
        self.current_audio = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 音频信息显示
        self.info_label = QLabel("未加载音频")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("QLabel { padding: 10px; background-color: #f0f0f0; border-radius: 5px; }")
        layout.addWidget(self.info_label)
        
        # 播放控制按钮
        button_layout = QHBoxLayout()
        
        self.play_button = QPushButton("播放")
        self.play_button.clicked.connect(self.play_audio)
        self.play_button.setEnabled(False)
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_audio)
        self.save_button.setEnabled(False)
        
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def set_audio(self, audio, sample_rate: int):
        self.current_audio = audio
        
        if audio is not None:
            audio_info = audio_processor.get_audio_info(audio, sample_rate)
            info_text = f"时长: {audio_info['duration']:.2f}秒\n采样率: {audio_info['sample_rate']}Hz"
            self.info_label.setText(info_text)
            self.play_button.setEnabled(True)
            self.save_button.setEnabled(True)
        else:
            self.info_label.setText("音频加载失败")
            self.play_button.setEnabled(False)
            self.save_button.setEnabled(False)
    
    def play_audio(self):
        if self.current_audio is not None:
            try:
                audio_processor.play_audio(self.current_audio, tts_engine.sample_rate)
            except Exception as e:
                QMessageBox.warning(self, "播放错误", f"播放音频时发生错误: {str(e)}")
    
    def save_audio(self):
        if self.current_audio is not None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存音频文件", "", "WAV文件 (*.wav);;MP3文件 (*.mp3);;所有文件 (*)"
            )
            
            if file_path:
                try:
                    audio_processor.save_audio(self.current_audio, file_path)
                    QMessageBox.information(self, "保存成功", f"音频文件已保存到: {file_path}")
                except Exception as e:
                    QMessageBox.warning(self, "保存错误", f"保存音频文件时发生错误: {str(e)}")


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.synthesis_thread = None
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("CosyVoice2.0 文本转语音系统")
        self.setGeometry(100, 100, 900, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout()
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - 输入和控制
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板 - 输出和播放
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([600, 300])
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 文本输入区域
        text_group = QGroupBox("文本输入")
        text_layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("请输入要转换的文本...")
        self.text_edit.setMaximumHeight(150)
        text_layout.addWidget(self.text_edit)
        
        # 文本统计
        self.text_stats_label = QLabel("字符数: 0")
        text_layout.addWidget(self.text_stats_label)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)
        
        # 语音包选择
        voice_group = QGroupBox("语音包设置")
        voice_layout = QGridLayout()
        
        voice_layout.addWidget(QLabel("语音包:"), 0, 0)
        self.voice_pack_combo = QComboBox()
        voice_layout.addWidget(self.voice_pack_combo, 0, 1)
        
        voice_layout.addWidget(QLabel("语速:"), 1, 0)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        voice_layout.addWidget(self.speed_slider, 1, 1)
        
        self.speed_label = QLabel("1.0x")
        voice_layout.addWidget(self.speed_label, 1, 2)
        
        voice_layout.addWidget(QLabel("音调:"), 2, 0)
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setRange(-12, 12)
        self.pitch_slider.setValue(0)
        voice_layout.addWidget(self.pitch_slider, 2, 1)
        
        self.pitch_label = QLabel("0")
        voice_layout.addWidget(self.pitch_label, 2, 2)
        
        voice_layout.addWidget(QLabel("音量:"), 3, 0)
        self.energy_slider = QSlider(Qt.Horizontal)
        self.energy_slider.setRange(10, 200)
        self.energy_slider.setValue(100)
        voice_layout.addWidget(self.energy_slider, 3, 1)
        
        self.energy_label = QLabel("1.0x")
        voice_layout.addWidget(self.energy_label, 3, 2)
        
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)
        
        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QHBoxLayout()
        
        self.synthesize_button = QPushButton("开始合成")
        self.synthesize_button.clicked.connect(self.start_synthesis)
        control_layout.addWidget(self.synthesize_button)
        
        self.clear_button = QPushButton("清空文本")
        self.clear_button.clicked.connect(self.clear_text)
        control_layout.addWidget(self.clear_button)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 连接信号
        self.text_edit.textChanged.connect(self.update_text_stats)
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        self.pitch_slider.valueChanged.connect(self.update_pitch_label)
        self.energy_slider.valueChanged.connect(self.update_energy_label)
        
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 播放器标签页
        self.audio_player = AudioPlayer()
        tab_widget.addTab(self.audio_player, "音频播放")
        
        # 可视化标签页
        self.audio_visualizer = AudioVisualizer()
        tab_widget.addTab(self.audio_visualizer, "音频可视化")
        
        layout.addWidget(tab_widget)
        panel.setLayout(layout)
        return panel
    
    def load_config(self):
        """加载配置"""
        try:
            # 加载语音包
            available_packs = tts_engine.get_available_voice_packs()
            self.voice_pack_combo.clear()
            
            for pack_name in available_packs:
                pack_info = tts_engine.get_voice_pack_info(pack_name)
                if pack_info:
                    display_name = f"{pack_name} - {pack_info.get('name', 'Unknown')}"
                else:
                    display_name = pack_name
                
                self.voice_pack_combo.addItem(display_name, pack_name)
            
            self.logger.info("配置加载完成")
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            QMessageBox.warning(self, "配置错误", f"加载配置时发生错误: {str(e)}")
    
    def update_text_stats(self):
        """更新文本统计"""
        text = self.text_edit.toPlainText()
        char_count = len(text)
        self.text_stats_label.setText(f"字符数: {char_count}")
    
    def update_speed_label(self):
        """更新语速标签"""
        value = self.speed_slider.value() / 100.0
        self.speed_label.setText(f"{value:.1f}x")
    
    def update_pitch_label(self):
        """更新音调标签"""
        value = self.pitch_slider.value()
        self.pitch_label.setText(str(value))
    
    def update_energy_label(self):
        """更新音量标签"""
        value = self.energy_slider.value() / 100.0
        self.energy_label.setText(f"{value:.1f}x")
    
    def start_synthesis(self):
        """开始语音合成"""
        text = self.text_edit.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "输入错误", "请输入要转换的文本")
            return
        
        # 获取参数
        voice_pack = self.voice_pack_combo.currentData()
        speed = self.speed_slider.value() / 100.0
        pitch = self.pitch_slider.value()
        energy = self.energy_slider.value() / 100.0
        
        # 禁用按钮
        self.synthesize_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 创建合成线程
        self.synthesis_thread = SynthesisThread(text, voice_pack, speed, pitch, energy)
        self.synthesis_thread.progress_updated.connect(self.progress_bar.setValue)
        self.synthesis_thread.synthesis_completed.connect(self.synthesis_completed)
        self.synthesis_thread.error_occurred.connect(self.synthesis_error)
        self.synthesis_thread.start()
    
    def synthesis_completed(self, audio):
        """合成完成"""
        self.synthesize_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # 设置音频到播放器
        self.audio_player.set_audio(audio, tts_engine.sample_rate)
        
        # 设置音频到可视化器
        self.audio_visualizer.set_audio(audio, tts_engine.sample_rate)
        
        QMessageBox.information(self, "合成完成", "语音合成已完成！")
    
    def synthesis_error(self, error_msg):
        """合成错误"""
        self.synthesize_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "合成错误", error_msg)
    
    def clear_text(self):
        """清空文本"""
        self.text_edit.clear()
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.synthesis_thread and self.synthesis_thread.isRunning():
            self.synthesis_thread.terminate()
            self.synthesis_thread.wait()
        event.accept() 