@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo 正在启动电商热卖排行分析系统...

:: 激活conda环境
echo 正在激活conda环境: seller
call conda activate seller
if %ERRORLEVEL% neq 0 (
    echo 错误: conda环境'seller'激活失败
    pause
    exit /b 1
)

:: 检查依赖是否已安装
@REM echo 正在检查依赖项...
@REM pip list | findstr pyyaml >nul
@REM if %ERRORLEVEL% neq 0 (
@REM     echo 正在安装必要依赖...
@REM     pip install -r requirements.txt
@REM     if %ERRORLEVEL% neq 0 (
@REM         echo 错误: 依赖安装失败
@REM         pause
@REM         exit /b 1
@REM     )
@REM )

:: 启动修复版UI
echo 正在启动系统...
python fix_app.py

:: 脚本结束
echo 系统已关闭
pause