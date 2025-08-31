#!/bin/bash
echo "正在安装CosyVoice TTS依赖..."
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
echo "安装完成！"