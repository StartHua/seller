@echo off
chcp 65001 > nul
echo 正在修复依赖问题...

call conda activate seller

:: 降级Werkzeug到兼容版本
pip uninstall -y werkzeug
pip install werkzeug==2.3.7

echo 依赖修复完成!
pause 