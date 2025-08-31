"""
主窗口界面
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QPushButton, QLabel, QComboBox, 
                             QSlider, QSpinBox, QDoubleSpinBox, QProgressBar,
                             QGroupBox, QGridLayout, QSplitter, QFrame,
                             QMessageBox, QFileDialog, QListWidget, QTabWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.tts_engine import tts_engine
from src.audio.audio_processor import audio_processor
from src.utils.logger import get_logger
from .audio_visualizer import AudioVisualizer
from .voice_pack_widget import VoicePackWidget
from .engine_voice_manager import engine_voice_manager
from .engine_voice_manager import engine_voice_manager
from .engine_voice_manager import engine_voice_manager

logger = get_logger(__name__)


class SynthesisThread(QThread):
    """语音合成线程"""
    progress_updated = pyqtSignal(int)
    synthesis_completed = pyqtSignal(np.ndarray)
    synthesis_failed = pyqtSignal(str)
    
    def __init__(self, text, voice_pack, speed, pitch, energy):
        super().__init__()
        self.text = text
        self.voice_pack = voice_pack
        self.speed = speed
        self.pitch = pitch
        self.energy = energy
    
    def run(self):
        try:
            # 更新进度
            self.progress_updated.emit(10)
            
            # 进行语音合成
            audio = tts_engine.synthesize(
                self.text, 
                voice_pack=self.voice_pack,
                speed=self.speed,
                pitch=self.pitch,
                energy=self.energy
            )
            
            if audio is not None:
                self.progress_updated.emit(100)
                self.synthesis_completed.emit(audio)
            else:
                self.synthesis_failed.emit("语音合成失败")
                
        except Exception as e:
            logger.error(f"语音合成线程异常: {e}")
            self.synthesis_failed.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.current_audio = None
        self.synthesis_thread = None
        self.init_ui()
        self.init_tts_engine()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("CosyVoice TTS - 文本转语音系统")
        self.setGeometry(50, 50, 800, 500)  # 进一步缩小以适应屏幕
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧显示面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例 (适应更小的界面)
        splitter.setSizes([300, 600])
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
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
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QSlider::groove:horizontal {
                border: 1px solid #cccccc;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #4CAF50;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)
    
    def create_left_panel(self):
        """创建左侧控制面板"""
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)
        
        # 引擎选择组
        engine_group = QGroupBox("TTS引擎选择")
        engine_layout = QVBoxLayout(engine_group)
        
        # 引擎选择下拉框
        self.engine_combo = QComboBox()
        self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
        engine_layout.addWidget(QLabel("选择引擎:"))
        engine_layout.addWidget(self.engine_combo)
        
        # 引擎信息显示
        self.engine_info_label = QLabel("引擎信息")
        self.engine_info_label.setWordWrap(True)
        engine_layout.addWidget(self.engine_info_label)
        
        layout.addWidget(engine_group)
        
        # 语音包选择组
        voice_pack_group = QGroupBox("语音包选择")
        voice_pack_layout = QVBoxLayout(voice_pack_group)
        
        # 语音包选择下拉框
        self.voice_pack_combo = QComboBox()
        voice_pack_layout.addWidget(QLabel("选择语音包:"))
        voice_pack_layout.addWidget(self.voice_pack_combo)
        
        # 语音包信息显示
        self.voice_pack_info_label = QLabel("语音包信息")
        self.voice_pack_info_label.setWordWrap(True)
        voice_pack_layout.addWidget(self.voice_pack_info_label)
        
        layout.addWidget(voice_pack_group)
        
        # 文本输入组
        text_group = QGroupBox("文本输入")
        text_layout = QVBoxLayout(text_group)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("请输入要转换的文本...")
        self.text_edit.setMaximumHeight(150)
        text_layout.addWidget(self.text_edit)
        
        layout.addWidget(text_group)
        
        # 参数调节组
        params_group = QGroupBox("语音参数")
        params_layout = QGridLayout(params_group)
        
        # 语速调节
        params_layout.addWidget(QLabel("语速:"), 0, 0)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        params_layout.addWidget(self.speed_slider, 0, 1)
        
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setRange(0.5, 2.0)
        self.speed_spinbox.setValue(1.0)
        self.speed_spinbox.setSingleStep(0.1)
        self.speed_spinbox.valueChanged.connect(self.on_speed_spinbox_changed)
        params_layout.addWidget(self.speed_spinbox, 0, 2)
        
        # 音调调节
        params_layout.addWidget(QLabel("音调:"), 1, 0)
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setRange(-12, 12)
        self.pitch_slider.setValue(0)
        self.pitch_slider.valueChanged.connect(self.on_pitch_changed)
        params_layout.addWidget(self.pitch_slider, 1, 1)
        
        self.pitch_spinbox = QSpinBox()
        self.pitch_spinbox.setRange(-12, 12)
        self.pitch_spinbox.setValue(0)
        self.pitch_spinbox.valueChanged.connect(self.on_pitch_spinbox_changed)
        params_layout.addWidget(self.pitch_spinbox, 1, 2)
        
        # 音量调节
        params_layout.addWidget(QLabel("音量:"), 2, 0)
        self.energy_slider = QSlider(Qt.Horizontal)
        self.energy_slider.setRange(50, 150)
        self.energy_slider.setValue(100)
        self.energy_slider.valueChanged.connect(self.on_energy_changed)
        params_layout.addWidget(self.energy_slider, 2, 1)
        
        self.energy_spinbox = QDoubleSpinBox()
        self.energy_spinbox.setRange(0.5, 1.5)
        self.energy_spinbox.setValue(1.0)
        self.energy_spinbox.setSingleStep(0.1)
        self.energy_spinbox.valueChanged.connect(self.on_energy_spinbox_changed)
        params_layout.addWidget(self.energy_spinbox, 2, 2)
        
        layout.addWidget(params_group)
        
        # 控制按钮组
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout(control_group)
        
        # 合成按钮
        self.synthesize_btn = QPushButton("开始合成")
        self.synthesize_btn.clicked.connect(self.start_synthesis)
        control_layout.addWidget(self.synthesize_btn)
        
        # 播放按钮
        self.play_btn = QPushButton("播放音频")
        self.play_btn.clicked.connect(self.play_audio)
        self.play_btn.setEnabled(False)
        control_layout.addWidget(self.play_btn)
        
        # 保存按钮
        self.save_btn = QPushButton("保存音频")
        self.save_btn.clicked.connect(self.save_audio)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        layout.addWidget(control_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return left_widget
    
    def create_right_panel(self):
        """创建右侧显示面板"""
        right_widget = QWidget()
        layout = QVBoxLayout(right_widget)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 音频可视化标签页
        self.audio_visualizer = AudioVisualizer()
        tab_widget.addTab(self.audio_visualizer, "音频可视化")
        
        # 日志标签页
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        tab_widget.addTab(log_widget, "日志")
        
        layout.addWidget(tab_widget)
        
        return right_widget
    
    def init_tts_engine(self):
        """初始化TTS引擎"""
        try:
            # 加载TTS引擎
            if tts_engine.load_model():
                self.log_message("TTS引擎加载成功")
                
                # 动态加载可用引擎
                self.load_available_engines()
                
                # 填充语音包选择下拉框
                self.update_voice_packs()
                
                # 更新引擎信息
                self.update_engine_info()
                
            else:
                self.log_message("TTS引擎加载失败", "error")
                QMessageBox.critical(self, "错误", "TTS引擎加载失败")
                
        except Exception as e:
            logger.error(f"初始化TTS引擎失败: {e}")
            self.log_message(f"初始化TTS引擎失败: {e}", "error")
    
    def load_available_engines(self):
        """动态加载可用的TTS引擎"""
        try:
            # 获取实际可用的引擎列表
            available_engines = tts_engine.get_available_engines()
            self.engine_combo.clear()
            self.engine_combo.addItems(available_engines)
            
            # 设置当前引擎
            current_engine = tts_engine.get_current_engine()
            if current_engine:
                index = self.engine_combo.findText(current_engine)
                if index >= 0:
                    self.engine_combo.setCurrentIndex(index)
                    
        except Exception as e:
            logger.error(f"加载可用引擎失败: {e}")
            # 备用引擎列表
            self.engine_combo.addItems(["edge_tts", "cosyvoice", "gtts", "pyttsx3"])

    def update_voice_packs(self):
        """更新语音包列表 - 根据当前引擎显示对应的语音包"""
        try:
            self.voice_pack_combo.clear()
            
            # 获取当前引擎
            current_engine = self.engine_combo.currentText()
            if not current_engine:
                return
            
            # 根据引擎类型获取对应的语音包
            if current_engine == "edge_tts":
                self._load_edge_tts_voices()
            elif current_engine == "cosyvoice":
                self._load_cosyvoice_voices()
            elif current_engine == "gtts":
                self._load_gtts_voices()
            elif current_engine == "pyttsx3":
                self._load_pyttsx3_voices()
            else:
                # 未知引擎，使用基础语音包
                self._load_basic_voices()
            
            # 设置默认选择
            if self.voice_pack_combo.count() > 0:
                self.voice_pack_combo.setCurrentIndex(0)
            
            self.update_voice_pack_info()
            
        except Exception as e:
            logger.error(f"更新语音包列表失败: {e}")
            self._load_basic_voices()

    def _load_edge_tts_voices(self):
        """加载Edge-TTS语音包"""
        try:
            from src.core.edge_tts_integration import edge_tts_integration
            if hasattr(edge_tts_integration, 'available_voices'):
                voices = edge_tts_integration.available_voices
                if isinstance(voices, list):
                    # voices是列表格式，包含字典
                    for voice_info in voices:
                        if isinstance(voice_info, dict):
                            voice_id = voice_info.get('name', 'Unknown')
                            friendly_name = voice_info.get('friendly_name', voice_id)
                            gender = voice_info.get('gender', 'Unknown')
                            display_name = f"{friendly_name} ({gender})"
                            self.voice_pack_combo.addItem(display_name, voice_id)
                elif isinstance(voices, dict):
                    # voices是字典格式
                    for voice_id, voice_info in voices.items():
                        display_name = f"{voice_info.get('name', voice_id)} ({voice_info.get('gender', 'Unknown')})"
                        self.voice_pack_combo.addItem(display_name, voice_id)
                else:
                    self._load_basic_voices()
            else:
                self._load_basic_voices()
        except Exception as e:
            logger.error(f"加载Edge-TTS语音包失败: {e}")
            self._load_basic_voices()

    def _load_cosyvoice_voices(self):
        """加载CosyVoice语音包"""
        try:
            from src.core.real_cosyvoice_integration import real_cosyvoice_integration
            if hasattr(real_cosyvoice_integration, 'available_voices'):
                voices = real_cosyvoice_integration.available_voices
                if voices:
                    for voice_id, voice_info in voices.items():
                        display_name = f"{voice_info.get('name', voice_id)} ({voice_info.get('gender', 'Unknown')})"
                        self.voice_pack_combo.addItem(display_name, voice_id)
                else:
                    # CosyVoice默认语音包
                    cosyvoice_packs = ["default", "female_warm", "male_deep", "child_cute"]
                    for pack in cosyvoice_packs:
                        self.voice_pack_combo.addItem(pack, pack)
            else:
                cosyvoice_packs = ["default", "female_warm", "male_deep", "child_cute"]
                for pack in cosyvoice_packs:
                    self.voice_pack_combo.addItem(pack, pack)
        except Exception as e:
            logger.error(f"加载CosyVoice语音包失败: {e}")
            cosyvoice_packs = ["default", "female_warm", "male_deep", "child_cute"]
            for pack in cosyvoice_packs:
                self.voice_pack_combo.addItem(pack, pack)

    def _load_gtts_voices(self):
        """加载gTTS语音包"""
        try:
            # gTTS支持的语言和方言
            gtts_voices = [
                ("zh-cn", "中文 (普通话)"),
                ("zh-tw", "中文 (台湾)"),
                ("en-us", "English (US)"),
                ("en-uk", "English (UK)"),
                ("ja", "日本語"),
                ("ko", "한국어")
            ]
            for voice_id, display_name in gtts_voices:
                self.voice_pack_combo.addItem(display_name, voice_id)
        except Exception as e:
            logger.error(f"加载gTTS语音包失败: {e}")
            self._load_basic_voices()

    def _load_pyttsx3_voices(self):
        """加载pyttsx3语音包"""
        try:
            from src.core.pyttsx3_integration import pyttsx3_integration
            if hasattr(pyttsx3_integration, 'available_voices'):
                voices = pyttsx3_integration.available_voices
                if voices:
                    for voice_info in voices:
                        voice_id = voice_info.get('id', 'Unknown')
                        name = voice_info.get('name', voice_id)
                        gender = voice_info.get('gender', 'Unknown')
                        display_name = f"{name} ({gender})"
                        self.voice_pack_combo.addItem(display_name, voice_id)
                else:
                    self._load_basic_voices()
            else:
                self._load_basic_voices()
        except Exception as e:
            logger.error(f"加载pyttsx3语音包失败: {e}")
            self._load_basic_voices()

    def _load_basic_voices(self):
        """加载基础语音包"""
        basic_packs = ["default", "female", "male", "child"]
        for pack in basic_packs:
            self.voice_pack_combo.addItem(pack, pack)
    
    def update_engine_info(self):
        """更新引擎信息显示"""
        try:
            current_engine = self.engine_combo.currentText()
            if current_engine:
                engine_info = tts_engine.get_engine_info(current_engine)
                info_text = f"引擎: {engine_info.get('name', 'Unknown')}\n"
                info_text += f"版本: {engine_info.get('version', 'Unknown')}\n"
                info_text += f"状态: {'已加载' if engine_info.get('loaded', False) else '未加载'}\n"
                info_text += f"采样率: {engine_info.get('sample_rate', 'Unknown')}Hz"
                
                if 'available_voices' in engine_info:
                    info_text += f"\n可用语音: {engine_info['available_voices']}个"
                
                self.engine_info_label.setText(info_text)
                
        except Exception as e:
            logger.error(f"更新引擎信息失败: {e}")
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar('主工具栏')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # 开始按钮
        start_action = toolbar.addAction('🎵 开始')
        start_action.setToolTip('开始语音合成')
        start_action.triggered.connect(self.on_start_synthesis)
        
        toolbar.addSeparator()
        
        # 设置按钮
        settings_action = toolbar.addAction('⚙️ 设置')
        settings_action.setToolTip('打开设置')
        settings_action.triggered.connect(self.show_settings)
        
        toolbar.addSeparator()
        
        # 帮助按钮
        help_action = toolbar.addAction('❓ 帮助')
        help_action.setToolTip('查看帮助')
        help_action.triggered.connect(self.show_help)
    
    def on_start_synthesis(self):
        """工具栏开始合成按钮事件 - 显示菜单选项"""
        from PyQt5.QtWidgets import QMenu, QAction
        
        menu = QMenu(self)
        
        # 打开文件选项
        open_file_action = QAction('📁 打开文件', self)
        open_file_action.triggered.connect(self.open_text_file)
        menu.addAction(open_file_action)
        
        # 开始合成选项
        start_synthesis_action = QAction('🎵 开始合成', self)
        start_synthesis_action.triggered.connect(self.start_synthesis)
        menu.addAction(start_synthesis_action)
        
        menu.addSeparator()
        
        # 关闭选项
        close_action = QAction('❌ 关闭', self)
        close_action.triggered.connect(self.close)
        menu.addAction(close_action)
        
        # 显示菜单
        # 获取工具栏位置来显示菜单
        toolbar = self.sender().parent()
        if toolbar:
            menu.exec_(toolbar.mapToGlobal(toolbar.rect().bottomLeft()))
        else:
            menu.exec_(self.mapToGlobal(self.rect().center()))
    
    def open_text_file(self):
        """打开文本文件"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            '打开文本文件', 
            '', 
            'Text Files (*.txt);;All Files (*)'
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 假设有文本输入框，将内容设置到输入框
                    if hasattr(self, 'text_input'):
                        self.text_input.setPlainText(content)
                    self.log_message(f'已加载文件: {file_path}')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'无法打开文件: {str(e)}')
    
    def show_settings(self):
        """显示引擎与语音包配置对话框"""
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                     QComboBox, QPushButton, QTextEdit, QTabWidget,
                                     QWidget, QListWidget, QSplitter, QGroupBox,
                                     QGridLayout, QMessageBox, QCheckBox)
        import json
        
        dialog = QDialog(self)
        dialog.setWindowTitle('引擎与语音包配置')
        dialog.setGeometry(150, 150, 700, 500)
        
        layout = QVBoxLayout(dialog)
        
        # 界面设置
        layout.addWidget(QLabel('界面设置:'))
        
        # 显示引擎信息
        show_engine_info = QCheckBox('显示引擎信息')
        show_engine_info.setChecked(True)
        layout.addWidget(show_engine_info)
        
        # 显示语音包信息
        show_voice_info = QCheckBox('显示语音包信息')
        show_voice_info.setChecked(True)
        layout.addWidget(show_voice_info)
        
        # 最大语音包数量
        max_voices_layout = QHBoxLayout()
        max_voices_layout.addWidget(QLabel('最大显示语音包数量:'))
        max_voices_spinbox = QSpinBox()
        max_voices_spinbox.setRange(10, 100)
        max_voices_spinbox.setValue(50)
        max_voices_layout.addWidget(max_voices_spinbox)
        layout.addLayout(max_voices_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton('确定')
        cancel_button = QPushButton('取消')
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            self.log_message('设置已保存')
    
    def show_help(self):
        """显示帮助对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle('帮助')
        dialog.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout(dialog)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>CosyVoice TTS 语音合成系统</h2>
        
        <h3>功能介绍:</h3>
        <ul>
            <li><b>多引擎支持:</b> Edge-TTS、CosyVoice、Google TTS、pyttsx3</li>
            <li><b>语音包管理:</b> 每个引擎显示专属语音包</li>
            <li><b>参数调节:</b> 支持语速、音调、音量调节</li>
            <li><b>音频可视化:</b> 实时显示音频波形和频谱</li>
        </ul>
        
        <h3>使用方法:</h3>
        <ol>
            <li>选择TTS引擎</li>
            <li>选择对应的语音包</li>
            <li>输入要转换的文本</li>
            <li>调整语音参数</li>
            <li>点击"开始合成"按钮</li>
            <li>播放或保存生成的音频</li>
        </ol>
        
        <h3>引擎说明:</h3>
        <ul>
            <li><b>Edge-TTS:</b> 微软TTS服务，36+中文语音包</li>
            <li><b>CosyVoice:</b> 阿里巴巴开源TTS模型，高质量合成</li>
            <li><b>Google TTS:</b> Google文本转语音服务</li>
            <li><b>pyttsx3:</b> 本地系统TTS引擎</li>
        </ul>
        
        <h3>快捷键:</h3>
        <ul>
            <li><b>Ctrl+Enter:</b> 开始合成</li>
            <li><b>Space:</b> 播放/暂停</li>
            <li><b>Ctrl+S:</b> 保存音频</li>
        </ul>
        """)
        layout.addWidget(help_text)
        
        close_button = QPushButton('关闭')
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.exec_()
    
    def update_voice_pack_info(self):
        """更新语音包信息显示"""
        try:
            # 获取当前选择的语音包ID
            current_voice_pack = self.voice_pack_combo.currentData()
            if not current_voice_pack:
                current_voice_pack = self.voice_pack_combo.currentText()
            current_engine = self.engine_combo.currentText()
            
            if current_voice_pack and current_engine:
                pack_info = tts_engine.get_voice_pack_info(current_voice_pack, current_engine)
                if pack_info:
                    info_text = f"名称: {pack_info.get('name', 'Unknown')}\n"
                    info_text += f"描述: {pack_info.get('description', 'Unknown')}\n"
                    info_text += f"性别: {pack_info.get('gender', 'unknown')}\n"
                    info_text += f"风格: {pack_info.get('style', 'neutral')}\n"
                    info_text += f"情感: {pack_info.get('emotion', 'neutral')}"
                    
                    self.voice_pack_info_label.setText(info_text)
                    
        except Exception as e:
            logger.error(f"更新语音包信息失败: {e}")
    
    def on_engine_changed(self, engine_name):
        """引擎选择改变事件"""
        try:
            if engine_name:
                tts_engine.set_current_engine(engine_name)
                self.update_voice_packs()
                self.update_engine_info()
                self.log_message(f"切换到引擎: {engine_name}")
                
        except Exception as e:
            logger.error(f"切换引擎失败: {e}")
    
    def on_speed_changed(self, value):
        """语速滑块改变事件"""
        speed = value / 100.0
        self.speed_spinbox.setValue(speed)
    
    def on_speed_spinbox_changed(self, value):
        """语速输入框改变事件"""
        self.speed_slider.setValue(int(value * 100))
    
    def on_pitch_changed(self, value):
        """音调滑块改变事件"""
        self.pitch_spinbox.setValue(value)
    
    def on_pitch_spinbox_changed(self, value):
        """音调输入框改变事件"""
        self.pitch_slider.setValue(value)
    
    def on_energy_changed(self, value):
        """音量滑块改变事件"""
        energy = value / 100.0
        self.energy_spinbox.setValue(energy)
    
    def on_energy_spinbox_changed(self, value):
        """音量输入框改变事件"""
        self.energy_slider.setValue(int(value * 100))
    
    def start_synthesis(self):
        """开始语音合成"""
        try:
            text = self.text_edit.toPlainText().strip()
            if not text:
                QMessageBox.warning(self, "警告", "请输入要转换的文本")
                return
            
            # 获取语音包ID（使用currentData获取实际的语音包ID）
            voice_pack = self.voice_pack_combo.currentData()
            if not voice_pack:
                # 如果没有data，则使用text作为备用
                voice_pack = self.voice_pack_combo.currentText()
            speed = self.speed_spinbox.value()
            pitch = self.pitch_spinbox.value()
            energy = self.energy_spinbox.value()
            
            # 禁用按钮
            self.synthesize_btn.setEnabled(False)
            self.play_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # 创建合成线程
            self.synthesis_thread = SynthesisThread(text, voice_pack, speed, pitch, energy)
            self.synthesis_thread.progress_updated.connect(self.progress_bar.setValue)
            self.synthesis_thread.synthesis_completed.connect(self.on_synthesis_completed)
            self.synthesis_thread.synthesis_failed.connect(self.on_synthesis_failed)
            self.synthesis_thread.start()
            
            self.log_message("开始语音合成...")
            
        except Exception as e:
            logger.error(f"开始合成失败: {e}")
            self.log_message(f"开始合成失败: {e}", "error")
            self.reset_ui()
    
    def on_synthesis_completed(self, audio):
        """合成完成事件"""
        try:
            self.current_audio = audio
            
            # 更新音频可视化
            self.audio_visualizer.set_audio(audio)
            
            # 启用按钮
            self.play_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            
            # 隐藏进度条
            self.progress_bar.setVisible(False)
            
            # 重新启用合成按钮
            self.synthesize_btn.setEnabled(True)
            
            # 自动保存音频文件（使用新的文件命名规则）
            try:
                from ..audio.audio_processor import audio_processor
                engine_name = self.engine_combo.currentText()
                voice_pack = self.voice_pack_combo.currentData() or self.voice_pack_combo.currentText()
                
                # 保存音频文件
                actual_file = audio_processor.save_audio(
                    audio, 
                    22050,
                    engine_name,
                    voice_pack
                )
                
                self.log_message(f"✅ 语音合成完成！文件已保存: {os.path.basename(actual_file)}")
                self.statusBar().showMessage(f"✅ 合成完成！文件: {os.path.basename(actual_file)}")
                
            except Exception as save_error:
                logger.error(f"保存音频文件失败: {save_error}")
                self.log_message("✅ 语音合成完成")
                self.statusBar().showMessage("✅ 合成完成")
            
        except Exception as e:
            logger.error(f"处理合成结果失败: {e}")
            self.log_message(f"处理合成结果失败: {e}", "error")
            self.reset_ui()
    
    def on_synthesis_failed(self, error_msg):
        """合成失败事件"""
        try:
            self.log_message(f"语音合成失败: {error_msg}", "error")
            QMessageBox.critical(self, "错误", f"语音合成失败: {error_msg}")
            self.reset_ui()
            
        except Exception as e:
            logger.error(f"处理合成失败事件异常: {e}")
    
    def play_audio(self):
        """播放音频"""
        try:
            if self.current_audio is not None:
                # 播放音频（使用新的文件命名规则）
                actual_file = audio_processor.play_audio(
                    self.current_audio, 
                    engine_name=self.engine_combo.currentText(),
                    voice_pack=self.voice_pack_combo.currentData() or self.voice_pack_combo.currentText()
                )
                if actual_file:
                    self.log_message(f"开始播放音频，文件已保存: {os.path.basename(actual_file)}")
                else:
                    self.log_message("开始播放音频")
            else:
                QMessageBox.warning(self, "警告", "没有可播放的音频")
                
        except Exception as e:
            logger.error(f"播放音频失败: {e}")
            self.log_message(f"播放音频失败: {e}", "error")
    
    def save_audio(self):
        """保存音频"""
        try:
            if self.current_audio is not None:
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "保存音频文件", "", "WAV文件 (*.wav)"
                )
                
                if file_path:
                    audio_processor.save_audio(self.current_audio, file_path)
                    self.log_message(f"音频已保存: {file_path}")
                    QMessageBox.information(self, "成功", "音频文件保存成功")
            else:
                QMessageBox.warning(self, "警告", "没有可保存的音频")
                
        except Exception as e:
            logger.error(f"保存音频失败: {e}")
            self.log_message(f"保存音频失败: {e}", "error")
    
    def reset_ui(self):
        """重置UI状态"""
        self.synthesize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def log_message(self, message, level="info"):
        """记录日志消息"""
        try:
            timestamp = QTimer().remainingTime()  # 简单的时间戳
            level_text = {"info": "信息", "error": "错误", "warning": "警告"}.get(level, "信息")
            
            log_text = f"[{level_text}] {message}"
            self.log_text.append(log_text)
            
            # 滚动到底部
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            logger.error(f"记录日志消息失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 停止合成线程
            if self.synthesis_thread and self.synthesis_thread.isRunning():
                self.synthesis_thread.terminate()
                self.synthesis_thread.wait()
            
            # 停止音频播放
            audio_processor.stop_audio()
            
            event.accept()
            
        except Exception as e:
            logger.error(f"关闭窗口异常: {e}")
    
    def load_available_engines(self):
        """动态加载可用的TTS引擎"""
        try:
            # 获取实际可用的引擎列表
            available_engines = engine_voice_manager.get_available_engines()
            self.engine_combo.clear()
            self.engine_combo.addItems(available_engines)
            
            # 设置当前引擎
            current_engine = tts_engine.get_current_engine()
            if current_engine:
                index = self.engine_combo.findText(current_engine)
                if index >= 0:
                    self.engine_combo.setCurrentIndex(index)
                    
        except Exception as e:
            logger.error(f"加载可用引擎失败: {e}")
            # 备用引擎列表
            self.engine_combo.addItems(["edge_tts", "cosyvoice", "gtts", "pyttsx3"])

    def update_voice_packs_new(self):
        """更新语音包列表 - 根据当前引擎显示对应的语音包"""
        try:
            self.voice_pack_combo.clear()
            
            # 获取当前引擎
            current_engine = self.engine_combo.currentText()
            if not current_engine:
                return
            
            # 使用引擎语音管理器获取对应的语音包
            voices = engine_voice_manager.get_voices_for_engine(current_engine)
            
            # 添加语音包到下拉菜单
            for display_name, voice_id in voices:
                self.voice_pack_combo.addItem(display_name, voice_id)
            
            # 设置默认选择
            if self.voice_pack_combo.count() > 0:
                self.voice_pack_combo.setCurrentIndex(0)
            
            self.update_voice_pack_info()
            
        except Exception as e:
            logger.error(f"更新语音包列表失败: {e}")
            # 添加基本的语音包作为备用
            basic_voices = [("默认语音", "default"), ("女声", "female"), ("男声", "male")]
            for display_name, voice_id in basic_voices:
                self.voice_pack_combo.addItem(display_name, voice_id)

    def update_engine_info_new(self):
        """更新引擎信息显示"""
        try:
            current_engine = self.engine_combo.currentText()
            if current_engine:
                engine_info = engine_voice_manager.get_engine_info(current_engine)
                name = engine_info.get('name', 'Unknown')
                desc = engine_info.get('description', 'Unknown')
                features = ', '.join(engine_info.get('features', []))
                voice_count = engine_info.get('voice_count', 'Unknown')
                
                info_text = f"引擎: {name}\
"
                info_text += f"描述: {desc}\
"
                info_text += f"特性: {features}\
"
                info_text += f"语音数量: {voice_count}"
                
                self.engine_info_label.setText(info_text)
                
        except Exception as e:
            logger.error(f"更新引擎信息失败: {e}") 