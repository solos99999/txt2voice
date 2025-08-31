@echo off
echo 正在安装CosyVoice TTS依赖...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo 安装完成！
pause