"""
音频可视化组件
"""

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class AudioVisualizer(QWidget):
    """音频可视化组件"""
    
    def __init__(self):
        super().__init__()
        self.audio_data = None
        self.sample_rate = 22050
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 音频信息标签
        self.info_label = QLabel("暂无音频数据")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 初始化子图
        self.waveform_ax = self.figure.add_subplot(3, 1, 1)
        self.spectrum_ax = self.figure.add_subplot(3, 1, 2)
        self.spectrogram_ax = self.figure.add_subplot(3, 1, 3)
        
        self.figure.tight_layout()
        
        # 设置初始显示
        self.clear_plots()
    
    def set_audio(self, audio_data, sample_rate=22050):
        """设置音频数据"""
        try:
            self.audio_data = audio_data
            self.sample_rate = sample_rate
            
            # 更新信息标签
            duration = len(audio_data) / sample_rate
            self.info_label.setText(
                f"音频长度: {duration:.2f}秒 | "
                f"采样率: {sample_rate}Hz | "
                f"数据点: {len(audio_data)}"
            )
            
            # 更新可视化
            self.update_visualization()
            
        except Exception as e:
            print(f"设置音频数据失败: {e}")
    
    def update_visualization(self):
        """更新可视化显示"""
        if self.audio_data is None:
            return
        
        try:
            # 清除之前的图形
            self.clear_plots()
            
            # 时间轴
            time_axis = np.linspace(0, len(self.audio_data) / self.sample_rate, len(self.audio_data))
            
            # 1. 波形图
            self.waveform_ax.plot(time_axis, self.audio_data, 'b-', linewidth=0.5)
            self.waveform_ax.set_title('音频波形')
            self.waveform_ax.set_xlabel('时间 (秒)')
            self.waveform_ax.set_ylabel('幅度')
            self.waveform_ax.grid(True, alpha=0.3)
            
            # 2. 频谱图
            # 计算FFT
            fft_data = np.fft.fft(self.audio_data)
            fft_freq = np.fft.fftfreq(len(self.audio_data), 1/self.sample_rate)
            
            # 只取正频率部分
            positive_freq_idx = fft_freq >= 0
            fft_magnitude = np.abs(fft_data[positive_freq_idx])
            fft_freq_positive = fft_freq[positive_freq_idx]
            
            # 转换为dB
            fft_db = 20 * np.log10(fft_magnitude + 1e-10)
            
            self.spectrum_ax.plot(fft_freq_positive[:len(fft_freq_positive)//2], 
                                fft_db[:len(fft_db)//2], 'r-', linewidth=1)
            self.spectrum_ax.set_title('频谱')
            self.spectrum_ax.set_xlabel('频率 (Hz)')
            self.spectrum_ax.set_ylabel('幅度 (dB)')
            self.spectrum_ax.grid(True, alpha=0.3)
            self.spectrum_ax.set_xlim(0, self.sample_rate // 4)  # 显示到奈奎斯特频率的一半
            
            # 3. 频谱图 (时频分析)
            # 计算短时傅里叶变换
            window_size = min(1024, len(self.audio_data) // 4)
            hop_size = window_size // 4
            
            if len(self.audio_data) > window_size:
                # 简化的频谱图计算
                n_frames = (len(self.audio_data) - window_size) // hop_size + 1
                n_freqs = window_size // 2 + 1
                
                spectrogram = np.zeros((n_freqs, n_frames))
                
                for i in range(n_frames):
                    start = i * hop_size
                    end = start + window_size
                    window_data = self.audio_data[start:end]
                    
                    # 应用汉宁窗
                    windowed_data = window_data * np.hanning(len(window_data))
                    
                    # 计算FFT
                    fft_frame = np.fft.fft(windowed_data)
                    magnitude = np.abs(fft_frame[:n_freqs])
                    spectrogram[:, i] = magnitude
                
                # 转换为dB并显示
                spectrogram_db = 20 * np.log10(spectrogram + 1e-10)
                
                # 时间和频率轴
                time_frames = np.linspace(0, len(self.audio_data) / self.sample_rate, n_frames)
                freq_bins = np.linspace(0, self.sample_rate / 2, n_freqs)
                
                im = self.spectrogram_ax.imshow(
                    spectrogram_db, 
                    aspect='auto', 
                    origin='lower',
                    extent=[time_frames[0], time_frames[-1], freq_bins[0], freq_bins[-1]],
                    cmap='viridis'
                )
                
                self.spectrogram_ax.set_title('频谱图')
                self.spectrogram_ax.set_xlabel('时间 (秒)')
                self.spectrogram_ax.set_ylabel('频率 (Hz)')
                
                # 添加颜色条
                try:
                    cbar = self.figure.colorbar(im, ax=self.spectrogram_ax)
                    cbar.set_label('幅度 (dB)')
                except:
                    pass  # 如果添加颜色条失败，忽略
            
            # 更新画布
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"更新可视化失败: {e}")
    
    def clear_plots(self):
        """清除所有图形"""
        try:
            self.waveform_ax.clear()
            self.spectrum_ax.clear()
            self.spectrogram_ax.clear()
            
            if self.audio_data is None:
                # 显示空状态
                self.waveform_ax.text(0.5, 0.5, '暂无音频数据', 
                                    transform=self.waveform_ax.transAxes,
                                    ha='center', va='center', fontsize=12)
                self.spectrum_ax.text(0.5, 0.5, '暂无音频数据', 
                                    transform=self.spectrum_ax.transAxes,
                                    ha='center', va='center', fontsize=12)
                self.spectrogram_ax.text(0.5, 0.5, '暂无音频数据', 
                                       transform=self.spectrogram_ax.transAxes,
                                       ha='center', va='center', fontsize=12)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"清除图形失败: {e}")