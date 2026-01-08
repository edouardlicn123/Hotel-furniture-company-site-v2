#!/bin/bash

# 设置终端编码为 UTF-8，确保中文显示正常
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

clear

echo
echo "=================================================="
echo "     酒店家具厂官网 - 一键启动脚本（国际源版）"
echo "     使用官方 PyPI 源（国际源）"
echo "=================================================="
echo

# 设置项目根目录为当前脚本所在目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[信息] 项目根目录: $PROJECT_ROOT"
cd "$PROJECT_ROOT" || { echo "错误: 无法进入项目目录！"; exit 1; }

# 虚拟环境目录
VENV_DIR="venv"

# 使用官方 PyPI 源（国际源）
PIP_INDEX="https://pypi.org/simple"

echo
echo "[信息] 检查 Python3 是否已安装..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "错误: 未在 PATH 中找到 python3！请先安装 Python 3 并确保其可访问。"
    read -p "按 Enter 键退出..."
    exit 1
fi
echo "[信息] 已找到 python3 版本: $(python3 --version)"

# 检查并创建虚拟环境
echo
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/5] 未检测到虚拟环境，正在创建虚拟环境（目录：$VENV_DIR）..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "错误: 创建虚拟环境失败！请检查 Python3 和 venv 模块是否正确安装。"
        read -p "按 Enter 键退出..."
        exit 1
    fi
    echo "[成功] 虚拟环境创建完成。"
else
    echo "[1/5] 已检测到现有虚拟环境（目录：$VENV_DIR）。"
fi

# 激活虚拟环境
echo
echo "[2/5] 正在激活虚拟环境..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo "错误: 激活虚拟环境失败！"
    read -p "按 Enter 键退出..."
    exit 1
fi
echo "[信息] 虚拟环境已激活。当前 Python 路径: $(which python)"
echo "[信息] 当前 pip 路径: $(which pip)"

# 升级 pip 并安装依赖（使用官方源）
echo
echo "[3/5] 正在升级 pip 并安装项目依赖（使用官方 PyPI 源：$PIP_INDEX）..."
pip install --upgrade pip -i "$PIP_INDEX" --verbose
if [ $? -ne 0 ]; then
    echo "警告: pip 升级失败，将继续使用现有版本..."
else
    echo "[信息] pip 已成功升级到 $(pip --version | awk '{print $2}')"
fi

if [ -f "requirements.txt" ]; then
    echo "[信息] 发现 requirements.txt，正在安装依赖包（详细输出）..."
    pip install -r requirements.txt -i "$PIP_INDEX" --verbose
    if [ $? -ne 0 ]; then
        echo "警告: 部分依赖安装失败，程序可能无法正常运行。"
        echo "请根据上方错误信息手动修复或安装缺失的包。"
    else
        echo "[成功] 所有依赖已安装完成。"
    fi
else
    echo "警告: 未找到 requirements.txt 文件！将不安装任何依赖。"
    echo "[信息] 如果项目需要依赖，请确保 requirements.txt 存在。"
fi

# 检查数据库是否存在
DB_PATH="instance/site.db"
echo
if [ ! -f "$DB_PATH" ]; then
    echo "[4/5] 未检测到数据库文件（$DB_PATH），正在初始化数据库..."
    if [ -f "init_schema.py" ]; then
        echo "[信息] 正在执行 init_schema.py 创建数据库..."
        python init_schema.py
        if [ $? -ne 0 ]; then
            echo "错误: 执行 init_schema.py 失败！请检查脚本内容。"
            read -p "按 Enter 键退出..."
            deactivate
            exit 1
        fi
        if [ -f "$DB_PATH" ]; then
            echo "[成功] 数据库初始化完成（路径：$DB_PATH）。"
        else
            echo "警告: 初始化后仍未发现数据库文件，请检查 init_schema.py 的输出。"
        fi
    else
        echo "错误: 未找到 init_schema.py 脚本！无法初始化数据库。"
        read -p "按 Enter 键退出..."
        deactivate
        exit 1
    fi
else
    echo "[4/5] 已检测到现有数据库（$DB_PATH），跳过初始化。"
fi

# 启动 Flask 项目
echo
echo "[5/5] 正在启动 Flask 项目..."
echo "访问地址：http://127.0.0.1:5000"
echo "按 Ctrl+C 可停止服务器。"
echo
echo "[信息] 正在尝试在浏览器新标签页中自动打开网站..."

# 尝试在不同系统上以新标签页方式打开浏览器
if command -v xdg-open >/dev/null 2>&1; then
    # Linux：后台打开，避免阻塞脚本
    echo "[信息] 系统为 Linux，使用 xdg-open 打开新标签页"
    nohup xdg-open http://127.0.0.1:5000 >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
    # macOS：open 命令默认在新标签页打开（如果浏览器已运行）
    echo "[信息] 系统为 macOS，使用 open 命令打开新标签页"
    open http://127.0.0.1:5000
elif command -v start >/dev/null 2>&1; then
    # Windows / Git Bash / WSL
    echo "[信息] 系统为 Windows，使用 start 命令打开新标签页"
    start "" http://127.0.0.1:5000
else
    echo "[信息] 未检测到支持的浏览器打开命令，请手动在浏览器中打开 http://127.0.0.1:5000"
fi

echo
echo "[信息] 正在启动 Flask 服务（执行 python app.py）..."
python app.py

# 捕获退出状态
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo
    echo "错误: Flask 项目运行出错，退出代码：$EXIT_CODE"
else
    echo
    echo "[信息] Flask 项目已正常停止。"
fi

# 停用虚拟环境
deactivate 2>/dev/null || echo "[信息] 虚拟环境已停用或未激活。"

echo
echo "=================================================="
echo "项目已停止。"
read -p "按 Enter 键退出..."
