"""
语音包选择组件
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QListWidgetItem, QLabel, QPushButton, QGroupBox,
                             QTextEdit, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class VoicePackWidget(QWidget):
    """语音包选择组件"""
    
    voice_pack_selected = pyqtSignal(str)  # 语音包选择信号
    
    def __init__(self):
        super().__init__()
        self.voice_packs = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QHBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧：语音包列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 语音包列表
        list_group = QGroupBox("可用语音包")
        list_layout = QVBoxLayout(list_group)
        
        self.voice_pack_list = QListWidget()
        self.voice_pack_list.itemClicked.connect(self.on_voice_pack_selected)
        list_layout.addWidget(self.voice_pack_list)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.refresh_voice_packs)
        list_layout.addWidget(self.refresh_btn)
        
        left_layout.addWidget(list_group)
        splitter.addWidget(left_widget)
        
        # 右侧：语音包详情
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 详情显示
        details_group = QGroupBox("语音包详情")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        details_layout.addWidget(self.details_text)
        
        right_layout.addWidget(details_group)
        
        # 预览控制
        preview_group = QGroupBox("预览控制")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_btn = QPushButton("预览语音包")
        self.preview_btn.clicked.connect(self.preview_voice_pack)
        self.preview_btn.setEnabled(False)
        preview_layout.addWidget(self.preview_btn)
        
        right_layout.addWidget(preview_group)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 400])
    
    def set_voice_packs(self, voice_packs):
        """设置语音包数据"""
        try:
            self.voice_packs = voice_packs
            self.refresh_voice_pack_list()
            
        except Exception as e:
            print(f"设置语音包数据失败: {e}")
    
    def refresh_voice_pack_list(self):
        """刷新语音包列表"""
        try:
            self.voice_pack_list.clear()
            
            for pack_name, pack_info in self.voice_packs.items():
                item = QListWidgetItem(pack_name)
                
                # 设置显示文本
                display_name = pack_info.get('display_name', pack_name)
                description = pack_info.get('description', '')
                
                if description:
                    item.setText(f"{display_name}\n{description}")
                else:
                    item.setText(display_name)
                
                # 设置数据
                item.setData(Qt.UserRole, pack_name)
                
                # 设置样式
                if pack_info.get('recommended', False):
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                
                self.voice_pack_list.addItem(item)
            
        except Exception as e:
            print(f"刷新语音包列表失败: {e}")
    
    def on_voice_pack_selected(self, item):
        """语音包选择事件"""
        try:
            pack_name = item.data(Qt.UserRole)
            if pack_name and pack_name in self.voice_packs:
                self.show_voice_pack_details(pack_name)
                self.preview_btn.setEnabled(True)
                self.voice_pack_selected.emit(pack_name)
            
        except Exception as e:
            print(f"处理语音包选择失败: {e}")
    
    def show_voice_pack_details(self, pack_name):
        """显示语音包详情"""
        try:
            if pack_name not in self.voice_packs:
                return
            
            pack_info = self.voice_packs[pack_name]
            
            details_html = f"""
            <h3>{pack_info.get('display_name', pack_name)}</h3>
            <p><b>内部名称:</b> {pack_name}</p>
            <p><b>描述:</b> {pack_info.get('description', '无描述')}</p>
            <p><b>性别:</b> {pack_info.get('gender', '未知')}</p>
            <p><b>语言:</b> {pack_info.get('language', '未知')}</p>
            <p><b>风格:</b> {pack_info.get('style', '标准')}</p>
            <p><b>情感:</b> {pack_info.get('emotion', '中性')}</p>
            """
            
            # 支持的引擎
            supported_engines = pack_info.get('supported_engines', {})
            if supported_engines:
                details_html += "<p><b>支持的引擎:</b></p><ul>"
                for engine, supported in supported_engines.items():
                    status = "✓" if supported else "✗"
                    details_html += f"<li>{status} {engine}</li>"
                details_html += "</ul>"
            
            # 额外信息
            if 'sample_rate' in pack_info:
                details_html += f"<p><b>采样率:</b> {pack_info['sample_rate']}Hz</p>"
            
            if 'quality' in pack_info:
                details_html += f"<p><b>质量:</b> {pack_info['quality']}</p>"
            
            if pack_info.get('recommended', False):
                details_html += "<p><b>🌟 推荐语音包</b></p>"
            
            self.details_text.setHtml(details_html)
            
        except Exception as e:
            print(f"显示语音包详情失败: {e}")
    
    def preview_voice_pack(self):
        """预览语音包"""
        try:
            current_item = self.voice_pack_list.currentItem()
            if current_item:
                pack_name = current_item.data(Qt.UserRole)
                # 这里可以添加预览逻辑
                print(f"预览语音包: {pack_name}")
            
        except Exception as e:
            print(f"预览语音包失败: {e}")
    
    def refresh_voice_packs(self):
        """刷新语音包"""
        try:
            # 这里可以添加重新加载语音包的逻辑
            self.refresh_voice_pack_list()
            
        except Exception as e:
            print(f"刷新语音包失败: {e}")
    
    def get_selected_voice_pack(self):
        """获取当前选择的语音包"""
        try:
            current_item = self.voice_pack_list.currentItem()
            if current_item:
                return current_item.data(Qt.UserRole)
            return None
            
        except Exception as e:
            print(f"获取选择的语音包失败: {e}")
            return None