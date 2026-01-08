@echo off
chcp 65001 >nul
cls

echo.
echo ==================================================
echo     XX生产商官网 - 一键启动脚本（国内优化版）
echo     已内置清华镜像源，下载依赖更快
echo ==================================================
echo.

:: 设置项目根目录（当前目录）
set PROJECT_ROOT=%~dp0
cd /d %PROJECT_ROOT%

:: 虚拟环境目录
set VENV_DIR=venv

:: 国内镜像源（清华源，速度快稳定）
set PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
set PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

:: 检查虚拟环境是否存在
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [1/5] 未检测到虚拟环境，正在创建...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo ERROR: 创建虚拟环境失败！请确认已安装 Python 并添加到 PATH。
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功。
) else (
    echo [1/5] 检测到现有虚拟环境。
)

:: 激活虚拟环境
echo.
echo [2/5] 正在激活虚拟环境...
call %VENV_DIR%\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: 激活虚拟环境失败！
    pause
    exit /b 1
)

:: 升级 pip 并安装依赖（使用国内镜像源）
echo.
echo [3/5] 正在升级 pip 并安装项目依赖（使用清华镜像源）...
pip install --upgrade pip -i %PIP_INDEX% --trusted-host %PIP_TRUSTED_HOST% -q

if exist requirements.txt (
    pip install -r requirements.txt -i %PIP_INDEX% --trusted-host %PIP_TRUSTED_HOST% -q
    if errorlevel 1 (
        echo WARNING: 部分依赖安装失败，但将继续尝试运行。
    ) else (
        echo 所有依赖已满足或已安装。
    )
) else (
    echo WARNING: 未找到 requirements.txt 文件！
)

:: 检查数据库是否存在
set DB_PATH=instance\site.db
if not exist "%DB_PATH%" (
    echo.
    echo [4/5] 未检测到数据库文件，正在初始化...
    if exist init_schema.py (
        python init_schema.py
        if errorlevel 1 (
            echo ERROR: 执行 init_schema.py 失败！请检查脚本。
            pause
            exit /b 1
        )
        echo 数据库初始化完成（%DB_PATH%）。
    ) else (
        echo ERROR: 未找到 init_schema.py 脚本！无法创建数据库。
        pause
        exit /b 1
    )
) else (
    echo [4/5] 检测到现有数据库（%DB_PATH%），跳过初始化。
)

:: 运行项目并自动打开浏览器
echo.
echo [5/5] 正在启动 Flask 项目...
echo 访问地址：http://127.0.0.1:5000
echo 按 Ctrl+C 可停止服务器。
echo.
echo 正在启动服务器并自动打开浏览器...
start "" http://127.0.0.1:5000

python app.py

:: 如果程序异常退出
if errorlevel 1 (
    echo.
    echo ERROR: 项目运行出错！
)

echo.
echo ==================================================
echo 项目已停止。
pause