@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title 酒店家具厂官网 - 一键启动脚本（Windows版 2026-01-16）

cls

echo.
echo [32m==================================================[0m
echo      酒店家具厂官网 - 一键启动脚本（Windows版）
echo      支持自动 SECRET_KEY + 依赖增量安装 + debug开关
echo [32m==================================================[0m
echo.

:: ===============================================
::  项目路径
:: ===============================================
cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"
echo [信息] 项目根目录: %PROJECT_ROOT%

:: ===============================================
::  一些常用路径定义
:: ===============================================
set "VENV_DIR=venv"
set "ENV_FILE=.env"
set "DB_PATH=instance\site.db"

:: 使用国内镜像（可自行修改或注释）
set "PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple"
:: set "PIP_INDEX=https://pypi.org/simple"

:: debug 模式（建议生产环境关闭）
set "FLASK_DEBUG=False"
:: set "FLASK_DEBUG=True"   ← 如需调试请打开这行

echo.
echo [信息] 检查 Python 是否存在...

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo.
    echo [31m错误: 在 PATH 中找不到 python 命令！[0m
    echo        请先安装 Python 3.9 或更高版本，并勾选「Add Python to PATH」
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set "PY_VER=%%i"
echo [信息] 找到 Python %PY_VER%

:: ===============================================
:: 步骤1：处理 .env 与 SECRET_KEY
:: ===============================================
echo.
echo [步骤 1/6] 检查并准备 SECRET_KEY (.env 文件)...

if not exist "%ENV_FILE%" (
    echo [信息] 未找到 .env 文件，正在创建...
    type nul > "%ENV_FILE%"
)

findstr /C:"FLASK_SECRET_KEY" "%ENV_FILE%" >nul
if %ERRORLEVEL% neq 0 (
    echo [信息] 未检测到 FLASK_SECRET_KEY，正在生成...
    
    :: Windows 下生成比较随机的密钥（64位base64url）
    for /f %%i in ('python -c "import secrets; print(secrets.token_urlsafe(64))"') do set "SECRET=%%i"
    
    echo FLASK_SECRET_KEY=!SECRET!>> "%ENV_FILE%"
    echo [32m[成功] 已自动生成并写入 SECRET_KEY[0m
) else (
    echo [信息] 已检测到现有的 FLASK_SECRET_KEY，跳过生成。
)

:: ===============================================
:: 步骤2：虚拟环境
:: ===============================================
echo.
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [步骤 2/6] 未检测到虚拟环境，正在创建...
    python -m venv "%VENV_DIR%"
    if !ERRORLEVEL! neq 0 (
        echo [31m错误: 创建虚拟环境失败！请检查 python 与 venv 模块[0m
        pause
        exit /b 1
    )
    echo [32m[成功] 虚拟环境创建完成[0m
) else (
    echo [步骤 2/6] 已检测到现有虚拟环境，跳过创建。
)

:: 激活虚拟环境（Windows特色写法）
echo [信息] 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"
if !ERRORLEVEL! neq 0 (
    echo [31m错误: 激活虚拟环境失败！[0m
    pause
    exit /b 1
)

echo [信息] 虚拟环境已激活 ( !python --version! )

:: ===============================================
:: 步骤3：依赖安装（尽量增量）
:: ===============================================
echo.
echo [步骤 3/6] 检查并安装项目依赖...

:: 最粗暴但最可靠的方式：每次都尝试安装（现代电脑其实很快）
:: 如果你非常在意速度，可保留下面注释的 md5 方案（但 windows md5 较麻烦）

echo [信息] 正在安装/更新依赖...
python -m pip install --upgrade pip -i %PIP_INDEX% >nul 2>nul

if exist requirements.txt (
    echo         正在安装 requirements.txt 中的依赖...
    pip install -r requirements.txt -i %PIP_INDEX%
    if !ERRORLEVEL! equ 0 (
        echo [32m[成功] 依赖安装/更新完成[0m
    ) else (
        echo [33m[警告] 部分依赖安装失败，请稍后手动检查[0m
    )
) else (
    echo [33m[警告] 未找到 requirements.txt 文件！[0m
)

:: ===============================================
:: 步骤4：数据库文件检查与备份
:: ===============================================
echo.
if not exist "%DB_PATH%" (
    echo [步骤 4/6] 未检测到数据库，正在尝试初始化...
    if exist init_schema.py (
        python init_schema.py
        if exist "%DB_PATH%" (
            echo [32m[成功] 数据库初始化完成[0m
        ) else (
            echo [31m[错误] 数据库文件仍未生成！请检查 init_schema.py[0m
            goto :deactivate
        )
    ) else (
        echo [31m[错误] 未找到 init_schema.py 文件！[0m
        goto :deactivate
    )
) else (
    echo [步骤 4/6] 检测到已有数据库，正在创建备份...
    set "BACKUP_NAME=instance\site.db.bak.%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
    set "BACKUP_NAME=!BACKUP_NAME: =0!"
    copy "%DB_PATH%" "!BACKUP_NAME!" >nul
    echo [信息] 已备份至 !BACKUP_NAME!
)

:: ===============================================
:: 步骤5：启动！
:: ===============================================
echo.
echo [步骤 5/6] 准备启动 Flask 项目...
echo.
echo     访问地址：[32mhttp://127.0.0.1:5000[0m
echo     Debug 模式：[33m%FLASK_DEBUG%[0m   (生产环境建议关闭)
echo.
echo     按 Ctrl+C 可停止服务器
echo.

:: 尝试打开浏览器（Windows 通常都能成功）
start "" http://127.0.0.1:5000 2>nul

echo [32m启动中...[0m
echo.

set FLASK_DEBUG=%FLASK_DEBUG%
python app.py

:deactivate
echo.
echo [信息] 正在退出虚拟环境...
deactivate 2>nul

echo.
echo [32m==================================================[0m
echo               项目已停止
echo [32m==================================================[0m
echo.
pause
endlocal
