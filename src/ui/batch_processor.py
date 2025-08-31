"""
批量处理界面
支持批量文本转语音功能
"""

import os
import csv
from typing import List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTextEdit, QComboBox, QSlider, QLabel, QPushButton, QGroupBox,
    QFileDialog, QProgressBar, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from src.core.tts_engine import tts_engine
from src.audio.audio_processor import audio_processor
from src.utils.logger import get_logger


class BatchSynthesisThread(QThread):
    """批量合成线程"""
    progress_updated = pyqtSignal(int, int)  # current, total
    item_completed = pyqtSignal(int, str, bool)  # index, filename, success
    batch_completed = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, tasks: List[Dict], output_dir: str):
        super().__init__()
        self.tasks = tasks
        self.output_dir = output_dir
    
    def run(self):
        try:
            total = len(self.tasks)
            
            for i, task in enumerate(self.tasks):
                try:
                    # 执行语音合成
                    audio = tts_engine.synthesize(
                        text=task['text'],
                        voice_pack=task['voice_pack'],
                        speed=task['speed'],
                        pitch=task['pitch'],
                        energy=task['energy']
                    )
                    
                    if audio is not None:
                        # 生成文件名
                        filename = f"batch_{i+1:03d}_{task['voice_pack']}.wav"
                        filepath = os.path.join(self.output_dir, filename)
                        
                        # 保存音频
                        audio_processor.save_audio(audio, filepath)
                        
                        self.item_completed.emit(i, filename, True)
                    else:
                        self.item_completed.emit(i, f"batch_{i+1:03d}", False)
                    
                    # 更新进度
                    self.progress_updated.emit(i + 1, total)
                    
                except Exception as e:
                    self.item_completed.emit(i, f"batch_{i+1:03d}", False)
                    self.progress_updated.emit(i + 1, total)
            
            self.batch_completed.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"批量处理过程中发生错误: {str(e)}")


class BatchProcessor(QWidget):
    """批量处理器界面"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.batch_thread = None
        self.tasks = []
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 输入区域
        input_group = QGroupBox("批量输入")
        input_layout = QVBoxLayout()
        
        # 文本输入
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("请输入要批量转换的文本，每行一个...")
        self.text_edit.setMaximumHeight(100)
        input_layout.addWidget(self.text_edit)
        
        # 从文件导入
        file_layout = QHBoxLayout()
        self.import_button = QPushButton("从文件导入")
        self.import_button.clicked.connect(self.import_from_file)
        file_layout.addWidget(self.import_button)
        
        self.export_template_button = QPushButton("导出模板")
        self.export_template_button.clicked.connect(self.export_template)
        file_layout.addWidget(self.export_template_button)
        
        file_layout.addStretch()
        input_layout.addLayout(file_layout)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 参数设置
        param_group = QGroupBox("参数设置")
        param_layout = QGridLayout()
        
        param_layout.addWidget(QLabel("语音包:"), 0, 0)
        self.voice_pack_combo = QComboBox()
        param_layout.addWidget(self.voice_pack_combo, 0, 1)
        
        param_layout.addWidget(QLabel("语速:"), 1, 0)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        param_layout.addWidget(self.speed_slider, 1, 1)
        
        self.speed_label = QLabel("1.0x")
        param_layout.addWidget(self.speed_label, 1, 2)
        
        param_layout.addWidget(QLabel("音调:"), 2, 0)
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setRange(-12, 12)
        self.pitch_slider.setValue(0)
        param_layout.addWidget(self.pitch_slider, 2, 1)
        
        self.pitch_label = QLabel("0")
        param_layout.addWidget(self.pitch_label, 2, 2)
        
        param_layout.addWidget(QLabel("音量:"), 3, 0)
        self.energy_slider = QSlider(Qt.Horizontal)
        self.energy_slider.setRange(10, 200)
        self.energy_slider.setValue(100)
        param_layout.addWidget(self.energy_slider, 3, 1)
        
        self.energy_label = QLabel("1.0x")
        param_layout.addWidget(self.energy_label, 3, 2)
        
        param_group.setLayout(param_layout)
        layout.addWidget(param_group)
        
        # 任务列表
        task_group = QGroupBox("任务列表")
        task_layout = QVBoxLayout()
        
        # 任务表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(["序号", "文本", "语音包", "状态"])
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        task_layout.addWidget(self.task_table)
        
        # 任务控制按钮
        task_button_layout = QHBoxLayout()
        
        self.add_task_button = QPushButton("添加任务")
        self.add_task_button.clicked.connect(self.add_task)
        task_button_layout.addWidget(self.add_task_button)
        
        self.clear_tasks_button = QPushButton("清空任务")
        self.clear_tasks_button.clicked.connect(self.clear_tasks)
        task_button_layout.addWidget(self.clear_tasks_button)
        
        task_button_layout.addStretch()
        task_layout.addLayout(task_button_layout)
        
        task_group.setLayout(task_layout)
        layout.addWidget(task_group)
        
        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QHBoxLayout()
        
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_dir_edit = QLineEdit("batch_output")
        output_layout.addWidget(self.output_dir_edit)
        
        self.browse_button = QPushButton("浏览")
        self.browse_button.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.browse_button)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.start_batch_button = QPushButton("开始批量处理")
        self.start_batch_button.clicked.connect(self.start_batch_processing)
        control_layout.addWidget(self.start_batch_button)
        
        self.stop_batch_button = QPushButton("停止")
        self.stop_batch_button.clicked.connect(self.stop_batch_processing)
        self.stop_batch_button.setEnabled(False)
        control_layout.addWidget(self.stop_batch_button)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 连接信号
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        self.pitch_slider.valueChanged.connect(self.update_pitch_label)
        self.energy_slider.valueChanged.connect(self.update_energy_label)
        
        self.setLayout(layout)
    
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
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
    
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
    
    def import_from_file(self):
        """从文件导入"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文本文件", "", "文本文件 (*.txt);;CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.import_from_csv(file_path)
                else:
                    self.import_from_txt(file_path)
                    
                QMessageBox.information(self, "导入成功", f"已从文件导入 {len(self.tasks)} 个任务")
                
            except Exception as e:
                QMessageBox.warning(self, "导入错误", f"导入文件时发生错误: {str(e)}")
    
    def import_from_txt(self, file_path: str):
        """从文本文件导入"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.tasks = []
        for line in lines:
            line = line.strip()
            if line:
                self.tasks.append({
                    'text': line,
                    'voice_pack': self.voice_pack_combo.currentData(),
                    'speed': self.speed_slider.value() / 100.0,
                    'pitch': self.pitch_slider.value(),
                    'energy': self.energy_slider.value() / 100.0
                })
        
        self.update_task_table()
    
    def import_from_csv(self, file_path: str):
        """从CSV文件导入"""
        self.tasks = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                task = {
                    'text': row.get('text', ''),
                    'voice_pack': row.get('voice_pack', self.voice_pack_combo.currentData()),
                    'speed': float(row.get('speed', 1.0)),
                    'pitch': int(row.get('pitch', 0)),
                    'energy': float(row.get('energy', 1.0))
                }
                if task['text']:
                    self.tasks.append(task)
        
        self.update_task_table()
    
    def export_template(self):
        """导出CSV模板"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存CSV模板", "batch_template.csv", "CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['text', 'voice_pack', 'speed', 'pitch', 'energy'])
                    writer.writerow(['示例文本', 'default', '1.0', '0', '1.0'])
                
                QMessageBox.information(self, "导出成功", f"CSV模板已保存到: {file_path}")
                
            except Exception as e:
                QMessageBox.warning(self, "导出错误", f"导出模板时发生错误: {str(e)}")
    
    def add_task(self):
        """添加任务"""
        text = self.text_edit.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "输入错误", "请输入要转换的文本")
            return
        
        # 分割多行文本
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                task = {
                    'text': line,
                    'voice_pack': self.voice_pack_combo.currentData(),
                    'speed': self.speed_slider.value() / 100.0,
                    'pitch': self.pitch_slider.value(),
                    'energy': self.energy_slider.value() / 100.0
                }
                self.tasks.append(task)
        
        self.update_task_table()
        self.text_edit.clear()
    
    def clear_tasks(self):
        """清空任务"""
        self.tasks.clear()
        self.update_task_table()
    
    def update_task_table(self):
        """更新任务表格"""
        self.task_table.setRowCount(len(self.tasks))
        
        for i, task in enumerate(self.tasks):
            # 序号
            self.task_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            
            # 文本（截断显示）
            text = task['text']
            if len(text) > 50:
                text = text[:47] + "..."
            self.task_table.setItem(i, 1, QTableWidgetItem(text))
            
            # 语音包
            self.task_table.setItem(i, 2, QTableWidgetItem(task['voice_pack']))
            
            # 状态
            self.task_table.setItem(i, 3, QTableWidgetItem("等待中"))
    
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def start_batch_processing(self):
        """开始批量处理"""
        if not self.tasks:
            QMessageBox.warning(self, "任务错误", "请先添加任务")
            return
        
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "输出错误", "请设置输出目录")
            return
        
        # 创建输出目录
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "目录错误", f"创建输出目录失败: {str(e)}")
            return
        
        # 禁用按钮
        self.start_batch_button.setEnabled(False)
        self.stop_batch_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.tasks))
        self.progress_bar.setValue(0)
        
        # 创建批量处理线程
        self.batch_thread = BatchSynthesisThread(self.tasks, output_dir)
        self.batch_thread.progress_updated.connect(self.update_progress)
        self.batch_thread.item_completed.connect(self.update_task_status)
        self.batch_thread.batch_completed.connect(self.batch_completed)
        self.batch_thread.error_occurred.connect(self.batch_error)
        self.batch_thread.start()
    
    def stop_batch_processing(self):
        """停止批量处理"""
        if self.batch_thread and self.batch_thread.isRunning():
            self.batch_thread.terminate()
            self.batch_thread.wait()
        
        self.start_batch_button.setEnabled(True)
        self.stop_batch_button.setEnabled(False)
        self.progress_bar.setVisible(False)
    
    def update_progress(self, current: int, total: int):
        """更新进度"""
        self.progress_bar.setValue(current)
    
    def update_task_status(self, index: int, filename: str, success: bool):
        """更新任务状态"""
        if success:
            self.task_table.setItem(index, 3, QTableWidgetItem(f"完成: {filename}"))
        else:
            self.task_table.setItem(index, 3, QTableWidgetItem("失败"))
    
    def batch_completed(self):
        """批量处理完成"""
        self.start_batch_button.setEnabled(True)
        self.stop_batch_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        QMessageBox.information(self, "批量处理完成", "所有任务已处理完成！")
    
    def batch_error(self, error_msg: str):
        """批量处理错误"""
        self.start_batch_button.setEnabled(True)
        self.stop_batch_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "批量处理错误", error_msg) 