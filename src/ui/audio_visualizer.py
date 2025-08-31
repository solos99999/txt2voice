"""
音频可视化组件
提供音频波形和频谱显示功能
"""

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg


class AudioVisualizer(QWidget):
    """音频可视化组件"""
    
    def __init__(self):
        super().__init__()
        self.audio_data = None
        self.sample_rate = 22050
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("显示模式:"))
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["波形", "频谱", "频谱图"])
        self.display_mode_combo.currentTextChanged.connect(self.update_display)
        control_layout.addWidget(self.display_mode_combo)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 创建绘图窗口
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('left', '幅度')
        self.plot_widget.setLabel('bottom', '时间 (秒)')
        
        layout.addWidget(self.plot_widget)
        
        self.setLayout(layout)
    
    def set_audio(self, audio_data: np.ndarray, sample_rate: int):
        """设置音频数据"""
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.update_display()
    
    def update_display(self):
        """更新显示"""
        if self.audio_data is None:
            return
        
        mode = self.display_mode_combo.currentText()
        
        if mode == "波形":
            self.show_waveform()
        elif mode == "频谱":
            self.show_spectrum()
        elif mode == "频谱图":
            self.show_spectrogram()
    
    def show_waveform(self):
        """显示波形"""
        self.plot_widget.clear()
        
        # 创建时间轴
        time_axis = np.arange(len(self.audio_data)) / self.sample_rate
        
        # 绘制波形
        self.plot_widget.plot(time_axis, self.audio_data, pen=pg.mkPen('b', width=1))
        self.plot_widget.setLabel('bottom', '时间 (秒)')
        self.plot_widget.setLabel('left', '幅度')
        self.plot_widget.setTitle('音频波形')
    
    def show_spectrum(self):
        """显示频谱"""
        self.plot_widget.clear()
        
        # 计算FFT
        fft_data = np.fft.fft(self.audio_data)
        magnitude = np.abs(fft_data)
        
        # 只显示正频率部分
        half_length = len(magnitude) // 2
        magnitude = magnitude[:half_length]
        
        # 创建频率轴
        freq_axis = np.linspace(0, self.sample_rate / 2, half_length)
        
        # 绘制频谱
        self.plot_widget.plot(freq_axis, magnitude, pen=pg.mkPen('r', width=1))
        self.plot_widget.setLabel('bottom', '频率 (Hz)')
        self.plot_widget.setLabel('left', '幅度')
        self.plot_widget.setTitle('音频频谱')
    
    def show_spectrogram(self):
        """显示频谱图"""
        self.plot_widget.clear()
        
        # 计算频谱图
        # 使用较小的窗口大小以提高性能
        window_size = min(1024, len(self.audio_data) // 10)
        hop_size = window_size // 4
        
        # 计算STFT
        stft_data = []
        for i in range(0, len(self.audio_data) - window_size, hop_size):
            window = self.audio_data[i:i + window_size]
            fft = np.fft.fft(window)
            magnitude = np.abs(fft[:window_size // 2])
            stft_data.append(magnitude)
        
        if stft_data:
            stft_array = np.array(stft_data).T
            
            # 创建时间和频率轴
            time_axis = np.arange(len(stft_data)) * hop_size / self.sample_rate
            freq_axis = np.linspace(0, self.sample_rate / 2, window_size // 2)
            
            # 创建图像项
            img = pg.ImageItem()
            self.plot_widget.addItem(img)
            
            # 设置图像数据
            img.setImage(stft_array)
            
            # 设置坐标轴
            img.setTransform(pg.Transform3D().scale(
                time_axis[-1] / stft_array.shape[1],
                freq_axis[-1] / stft_array.shape[0]
            ))
            
            self.plot_widget.setLabel('bottom', '时间 (秒)')
            self.plot_widget.setLabel('left', '频率 (Hz)')
            self.plot_widget.setTitle('音频频谱图')
    
    def clear(self):
        """清空显示"""
        self.plot_widget.clear()
        self.audio_data = None 