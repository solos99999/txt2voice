# 🎤 CosyVoice TTS - 高质量中文语音合成系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/your-repo/CosyVoiceTTS)

一个功能完整的中文语音合成系统，集成了多种TTS引擎，提供高质量的语音输出和直观的图形界面。

## ✨ 主要特性

### 🎯 双引擎支持
- **Edge-TTS**: 微软在线语音服务，36+ 中文语音包
- **CosyVoice2.0**: 高质量离线语音合成，支持自然语音生成

### 🖥️ 图形界面
- 直观的PyQt5图形界面
- 实时音频波形显示
- 工具栏菜单系统（开始、设置、帮助）
- 引擎与语音包智能对应

### 🎵 丰富功能
- 36+ 中文语音包（男声/女声）
- 自动文件命名（引擎名_语音包名_时间戳.wav）
- 音频播放和保存功能
- 批量处理支持

## 🚀 快速开始

###虚拟环境运行
# Windows (当前系统)
.venv\Scripts\activate

# 或者使用PowerShell
.venv\Scripts\Activate.ps1


### 方法1: 直接运行（推荐）
# 安装依赖
pip install -r requirements.txt

# 启动程序
python gui.py
```

## 📋 系统要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10/11, macOS 10.14+, Ubuntu 18.04+
- **内存**: 最少 2GB RAM
- **磁盘空间**: 约 100MB（轻量版）或 5GB+（完整版）
- **网络**: Edge-TTS 需要网络连接

## 📦 依赖包

```
edge-tts>=6.1.0          # 微软语音服务
PyQt5>=5.15.0            # GUI框架
numpy>=1.21.0            # 数值计算
soundfile>=0.10.0        # 音频文件处理
librosa>=0.9.0           # 音频分析
matplotlib>=3.5.0        # 图形显示
pyqtgraph>=0.12.0        # 实时图表
torch>=1.12.0            # 深度学习框架（可选）
torchaudio>=0.12.0       # 音频处理（可选）
```

## 🎯 使用指南

### 基本使用
1. 启动程序后，选择TTS引擎（Edge-TTS 或 CosyVoice）
2. 从下拉菜单选择语音包
3. 在文本框输入要合成的文字
4. 点击"开始合成"按钮
5. 等待合成完成，可播放或查看保存的音频文件

### 工具栏功能
- **开始**: 打开文件、关闭程序
- **设置**: 配置引擎与语音包
- **帮助**: 查看使用说明和快捷键

### 快捷键
- **Space**: 播放/暂停音频
- **Ctrl+S**: 保存音频文件
- **Ctrl+Q**: 退出程序

## 📁 项目结构

```
CosyVoiceTTS/
├── gui.py                    # 主程序入口
├── main.py                   # 命令行版本
├── requirements.txt          # 依赖列表
├── README.md                 # 项目说明
├── src/                      # 源代码目录
│   ├── core/                 # 核心功能
│   │   ├── tts_engine.py     # TTS引擎管理
│   │   ├── edge_tts_integration.py    # Edge-TTS集成
│   │   └── real_cosyvoice_integration.py  # CosyVoice集成
│   ├── gui/                  # GUI界面
│   │   ├── main_window.py    # 主窗口
│   │   ├── audio_visualizer.py  # 音频可视化
│   │   └── engine_voice_manager.py  # 引擎语音管理
│   ├── audio/                # 音频处理
│   │   └── audio_processor.py  # 音频处理器
│   └── utils/                # 工具函数
│       ├── logger.py         # 日志系统
│       └── config_loader.py  # 配置加载
├── config/                   # 配置文件
│   └── engine_voice_config.json  # 引擎语音配置
├── batch_output/             # 音频输出目录
├── models/                   # 模型文件（可选）
└── docs/                     # 文档目录
```

## 🔧 高级配置

### 引擎配置
编辑 `config/engine_voice_config.json` 自定义引擎显示：

```json
{
  "engines": {
    "edge_tts": {
      "display_name": "Edge-TTS (微软)",
      "enabled": true,
      "order": 1
    },
    "cosyvoice": {
      "display_name": "CosyVoice2.0 (离线)",
      "enabled": true,
      "order": 2
    }
  }
}
```

### 音频输出设置
- 默认输出目录: `batch_output/`
- 文件命名格式: `{引擎名}_{语音包名}_{时间戳}.wav`
- 音频格式: WAV, 22050Hz, 单声道

## 🛠️ 开发指南

### 本地开发
```bash
# 克隆项目
git clone https://github.com/your-repo/CosyVoiceTTS.git
cd CosyVoiceTTS

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 启动开发版本
python gui.py
```

### 构建可执行文件
```bash
# 方法1: 完整版构建
python build_executable.py

# 方法2: 快速构建
python quick_build.py

# 方法3: 便携版
python create_simple_portable.py
```

## 🐛 故障排除

### 常见问题

**问题**: 程序无法启动
```bash
# 解决方案
1. 检查Python版本: python --version
2. 安装依赖: pip install -r requirements.txt
3. 检查错误日志: logs/app.log
```

**问题**: Edge-TTS 连接失败
```bash
# 解决方案
1. 检查网络连接
2. 更新edge-tts: pip install --upgrade edge-tts
3. 尝试切换语音包
```

**问题**: 音频文件无法播放
```bash
# 解决方案
1. 检查输出目录: batch_output/
2. 确认文件完整性
3. 使用其他音频播放器测试
```

**问题**: CosyVoice 输出噪音
```bash
# 解决方案
已修复：使用高质量备用实现
如仍有问题，请重启程序或切换语音包
```

### 日志文件
- 应用日志: `logs/app.log`
- 错误日志: `logs/error.log`
- 调试信息: 启动时添加 `--debug` 参数

## 📊 性能优化

### 系统优化
- 关闭不必要的后台程序
- 确保足够的内存空间
- 使用SSD硬盘提升I/O性能

### 网络优化（Edge-TTS）
- 使用稳定的网络连接
- 考虑使用代理服务器
- 批量处理时适当延迟

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送分支: `git push origin feature/AmazingFeature`
5. 提交Pull Request

### 代码规范
- 使用Python PEP 8编码规范
- 添加适当的注释和文档字符串
- 编写单元测试
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Microsoft Edge-TTS](https://github.com/rany2/edge-tts) - 提供优质的在线语音服务
- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) - 高质量的语音合成模型
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的GUI框架
- 所有贡献者和用户的支持



## 🔄 更新日志

### v1.0.0 (2025-08-31)
- ✅ 修复Edge-TTS连接问题，支持36个中文语音包
- ✅ 解决CosyVoice噪音输出问题，使用高质量备用实现
- ✅ 完善GUI界面，添加工具栏和设置功能
- ✅ 优化文件命名规则，包含引擎名、语音包名和时间戳
- ✅ 实现引擎-语音包智能对应关系
- ✅ 添加音频可视化和实时播放功能
- ✅ 支持多种部署方式（直接运行、便携版、可执行文件）

---

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**