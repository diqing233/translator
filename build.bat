@echo off
chcp 65001 >nul
echo 正在打包翻译软件为 .exe ...
pip install pyinstaller -q
pyinstaller --onefile --windowed --name "快速翻译" translator.py
echo.
echo 打包完成！exe 文件在 dist 目录中。
pause
