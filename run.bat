@echo off
setlocal enabledelayedexpansion

:: 清屏
cls

:: 颜色定义
set RED=[31m
set GREEN=[32m
set YELLOW=[33m
set NC=[0m

echo %GREEN%==================================================%NC%
echo      酒店家具官网 - 一键启动脚本（最终稳定版）
echo      直接启动前台 · 只打印一次启动信息 · 兼容 Flask 3.x
echo %GREEN%==================================================%NC%
echo.

:: 项目根目录
set PROJECT_ROOT=%CD%
echo [信息] 项目根目录: %PROJECT_ROOT%

:: 虚拟环境目录
set VENV_DIR=venv

:: 国内 pip 镜像（可注释掉使用官方源）
set PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
:: set PIP_INDEX=https://pypi.org/simple

:: 环境文件
set ENV_FILE=.env

:: Debug 模式（开发时建议保持 True）
set FLASK_DEBUG=True

echo.
echo [信息] 检查 Python3 是否已安装...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo %RED%错误: PATH 中未找到 Python3！请先安装 Python 3.9 或更高版本。%NC%
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version') do set PYTHON_VERSION=%%v
echo [信息] 已找到 %PYTHON_VERSION%

:: ───────────────────────────────────────────────
:: 步骤1：处理 .env 和 SECRET_KEY
:: ───────────────────────────────────────────────
echo.
echo [步骤 1/6] 检查并准备 SECRET_KEY（.env 文件）...

if not exist "%ENV_FILE%" type nul > "%ENV_FILE%"

findstr /C:"FLASK_SECRET_KEY" "%ENV_FILE%" >nul
if %ERRORLEVEL% neq 0 (
    echo [信息] 未检测到 FLASK_SECRET_KEY，正在生成...
    for /f %%i in ('python -c "import secrets; print(secrets.token_urlsafe(64))"') do set SECRET_KEY=%%i
    echo FLASK_SECRET_KEY=%SECRET_KEY%>> "%ENV_FILE%"
    echo %GREEN%[成功]%NC% 已生成并写入 SECRET_KEY
) else (
    echo [信息] 已检测到现有 SECRET_KEY，跳过生成
)

:: ───────────────────────────────────────────────
:: 步骤2：虚拟环境
:: ───────────────────────────────────────────────
echo.
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [步骤 2/6] 创建虚拟环境...
    python -m venv "%VENV_DIR%"
    if %ERRORLEVEL% neq 0 (
        echo %RED%错误: 创建虚拟环境失败！%NC%
        pause
        exit /b 1
    )
    echo %GREEN%[成功]%NC% 虚拟环境创建完成
) else (
    echo [步骤 2/6] 检测到现有虚拟环境，跳过创建
)

echo [信息] 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"
if %ERRORLEVEL% neq 0 (
    echo %RED%错误: 激活虚拟环境失败！%NC%
    pause
    exit /b 1
)
echo [信息] 虚拟环境已激活（%PYTHON_VERSION%）

:: ───────────────────────────────────────────────
:: 步骤3：依赖安装（增量 + MD5 校验）
:: ───────────────────────────────────────────────
echo.
echo [步骤 3/6] 检查并安装依赖...

python -c "import flask" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    if exist "requirements.txt" (
        for /f %%i in ('certutil -hashfile requirements.txt MD5 ^| findstr /v "CertUtil"') do set CURRENT_MD5=%%i
        if exist ".requirements.md5" (
            set /p LAST_MD5=<.requirements.md5
        ) else (
            set LAST_MD5=
        )
        
        if "!CURRENT_MD5!"=="!LAST_MD5!" (
            echo [信息] requirements.txt 无变化，跳过安装
        ) else (
            echo [信息] requirements.txt 有更新，正在安装...
            python -m pip install --upgrade pip -i %PIP_INDEX% --quiet
            python -m pip install -r requirements.txt -i %PIP_INDEX%
            if !ERRORLEVEL! equ 0 (
                certutil -hashfile requirements.txt MD5 | findstr /v "CertUtil" > .requirements.md5
                echo %GREEN%[成功]%NC% 依赖安装完成
            )
        )
    ) else (
        echo %YELLOW%警告: 未找到 requirements.txt，建议手动创建%NC%
    )
) else (
    echo [信息] 核心依赖缺失，进行完整安装...
    python -m pip install --upgrade pip -i %PIP_INDEX% --quiet
    if exist "requirements.txt" python -m pip install -r requirements.txt -i %PIP_INDEX%
)

:: ───────────────────────────────────────────────
:: 步骤4：数据库检查与初始化
:: ───────────────────────────────────────────────
set DB_PATH=instance\site.db
set BACKUP_PATH=instance\site.db.bak.%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
echo.
if not exist "%DB_PATH%" (
    echo [步骤 4/6] 未找到数据库，正在初始化...
    if exist "init_schema.py" (
        python init_schema.py
        if !ERRORLEVEL! equ 0 if exist "%DB_PATH%" (
            echo %GREEN%[成功]%NC% 数据库初始化完成
        ) else (
            echo %RED%错误: 数据库初始化失败！请检查 init_schema.py%NC%
            deactivate
            pause
            exit /b 1
        )
    ) else (
        echo %RED%错误: 未找到 init_schema.py！%NC%
        deactivate
        pause
        exit /b 1
    )
) else (
    echo [步骤 4/6] 检测到现有数据库，正在备份...
    copy "%DB_PATH%" "%BACKUP_PATH%"
    echo [信息] 旧数据库已备份至 %BACKUP_PATH%
    echo [信息] 使用现有数据库，跳过初始化
)

:: ───────────────────────────────────────────────
:: 步骤5：启动 Flask（前台运行，只打印一次启动信息）
:: ───────────────────────────────────────────────
echo.
echo [步骤 5/6] 启动 Flask 项目...
echo 访问地址：%GREEN%http://127.0.0.1:5000%NC%
echo Debug 模式：%YELLOW%%FLASK_DEBUG%%NC%
echo 按 Ctrl+C 可安全停止服务器
echo.

:: 设置环境变量，flask run 会自动读取
set FLASK_DEBUG=%FLASK_DEBUG%

:: 直接在前台启动
python -m flask run ^
    --host=0.0.0.0 ^
    --port=5000 ^
    --no-reload ^
    --debug

:: 以下代码仅在 Ctrl+C 后执行
echo.
echo %GREEN%[信息]%NC% 项目已正常停止（用户手动终止）

:: ───────────────────────────────────────────────
:: 清理
:: ───────────────────────────────────────────────
deactivate 2>nul

echo.
echo %GREEN%==================================================%NC%
echo 脚本执行结束。
pause
