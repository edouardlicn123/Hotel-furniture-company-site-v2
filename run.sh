#!/bin/bash

# 设置终端编码为 UTF-8，确保中文显示正常
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

clear

echo
echo "=================================================="
echo "     酒店家具厂官网 - 一键启动脚本（国内优化版）"
echo "     已内置清华镜像源，下载依赖更快"
echo "=================================================="
echo

# 设置项目根目录为当前脚本所在目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT" || { echo "ERROR: 无法进入项目目录！"; exit 1; }

# 虚拟环境目录
VENV_DIR="venv"

# 国内清华镜像源
PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
PIP_TRUSTED_HOST="pypi.tuna.tsinghua.edu.cn"

# 检查并创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/5] 未检测到虚拟环境，正在创建..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "ERROR: 创建虚拟环境失败！请确认已安装 Python3 并正确配置 PATH。"
        read -p "按 Enter 键退出..."
        exit 1
    fi
    echo "虚拟环境创建成功。"
else
    echo "[1/5] 检测到现有虚拟环境。"
fi

# 激活虚拟环境
echo
echo "[2/5] 正在激活虚拟环境..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo "ERROR: 激活虚拟环境失败！"
    read -p "按 Enter 键退出..."
    exit 1
fi

# 升级 pip 并安装依赖
echo
echo "[3/5] 正在升级 pip 并安装项目依赖（使用清华镜像源）..."
pip install --upgrade pip -i "$PIP_INDEX" --trusted-host "$PIP_TRUSTED_HOST" -q

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -i "$PIP_INDEX" --trusted-host "$PIP_TRUSTED_HOST" -q
    if [ $? -ne 0 ]; then
        echo "WARNING: 部分依赖安装失败，但将继续尝试运行。"
    else
        echo "所有依赖已满足或已安装。"
    fi
else
    echo "WARNING: 未找到 requirements.txt 文件！"
fi

# 检查数据库是否存在
DB_PATH="instance/site.db"
if [ ! -f "$DB_PATH" ]; then
    echo
    echo "[4/5] 未检测到数据库文件，正在初始化..."
    if [ -f "init_schema.py" ]; then
        python init_schema.py
        if [ $? -ne 0 ]; then
            echo "ERROR: 执行 init_schema.py 失败！请检查脚本。"
            read -p "按 Enter 键退出..."
            exit 1
        fi
        echo "数据库初始化完成（$DB_PATH）。"
    else
        echo "ERROR: 未找到 init_schema.py 脚本！无法创建数据库。"
        read -p "按 Enter 键退出..."
        exit 1
    fi
else
    echo "[4/5] 检测到现有数据库（$DB_PATH），跳过初始化。"
fi

# 启动 Flask 项目并尝试打开浏览器
echo
echo "[5/5] 正在启动 Flask 项目..."
echo "访问地址：http://127.0.0.1:5000"
echo "按 Ctrl+C 可停止服务器。"
echo
echo "正在启动服务器并尝试自动打开浏览器..."

# 尝试打开浏览器（支持 macOS、Linux、WSL）
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://127.0.0.1:5000
elif command -v open >/dev/null 2>&1; then
    open http://127.0.0.1:5000
elif command -v start >/dev/null 2>&1; then
    start http://127.0.0.1:5000
fi

# 启动 Flask
python app.py

# 捕获退出状态
if [ $? -ne 0 ]; then
    echo
    echo "ERROR: 项目运行出错！"
fi

echo
echo "=================================================="
echo "项目已停止。"
read -p "按 Enter 键退出..."
