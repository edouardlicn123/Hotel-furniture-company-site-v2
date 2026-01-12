#!/bin/bash

# 设置终端编码为 UTF-8，确保中文显示正常
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

clear

echo
echo "=================================================="
echo "     酒店家具厂官网 - 一键启动脚本（优化版）"
echo "     支持自动生成 SECRET_KEY + 智能跳过重复安装"
echo "=================================================="
echo

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[信息] 项目根目录: $PROJECT_ROOT"
cd "$PROJECT_ROOT" || { echo "错误: 无法进入项目目录！"; exit 1; }

# 虚拟环境目录
VENV_DIR="venv"

# 使用官方 PyPI 源（国际源）
PIP_INDEX="https://pypi.org/simple"

# 环境文件
ENV_FILE=".env"

echo
echo "[信息] 检查 Python3 是否已安装..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "错误: 未在 PATH 中找到 python3！请先安装 Python 3.9 或更高版本。"
    read -p "按 Enter 键退出..."
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1)
echo "[信息] 已找到 $PYTHON_VERSION"

# ===============================================
# 步骤1：检查并处理 .env 文件 + SECRET_KEY
# ===============================================
echo
echo "[步骤 1/6] 检查并准备 SECRET_KEY（.env 文件）..."

if [ ! -f "$ENV_FILE" ]; then
    echo "[信息] 未找到 .env 文件，正在创建..."
    touch "$ENV_FILE"
fi

if ! grep -q "FLASK_SECRET_KEY" "$ENV_FILE"; then
    echo "[信息] 未检测到 FLASK_SECRET_KEY，正在生成安全的随机密钥..."
    # 生成 64 字节的 URL-safe 随机密钥（足够安全）
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    
    # 写入 .env 文件（追加模式，避免覆盖其他配置）
    echo "FLASK_SECRET_KEY=$SECRET_KEY" >> "$ENV_FILE"
    echo "[成功] 已自动生成并写入 SECRET_KEY 到 $ENV_FILE"
    echo "      （该密钥仅生成一次，后续启动将直接使用）"
else
    echo "[信息] 已检测到现有的 FLASK_SECRET_KEY，跳过生成。"
fi

# ===============================================
# 步骤2：虚拟环境
# ===============================================
echo
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[步骤 2/6] 未检测到虚拟环境，正在创建（目录：$VENV_DIR）..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "错误: 创建虚拟环境失败！请检查 Python3 和 venv 模块。"
        exit 1
    fi
    echo "[成功] 虚拟环境创建完成。"
else
    echo "[步骤 2/6] 已检测到现有虚拟环境，跳过创建。"
fi

# 激活虚拟环境
echo "[信息] 正在激活虚拟环境..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo "错误: 激活虚拟环境失败！"
    exit 1
fi
echo "[信息] 虚拟环境已激活（Python: $(python --version)）"

# ===============================================
# 步骤3：依赖安装（仅在必要时执行）
# ===============================================
echo
echo "[步骤 3/6] 检查并安装项目依赖..."

# 检查是否已安装核心依赖（以 flask 为代表）
if python -c "import flask" 2>/dev/null; then
    echo "[信息] 已检测到 Flask 等核心依赖已安装，跳过 pip install。"
else
    echo "[信息] 检测到依赖缺失或不完整，正在升级 pip 并安装..."
    
    pip install --upgrade pip -i "$PIP_INDEX" --quiet
    if [ -f "requirements.txt" ]; then
        echo "[信息] 正在安装 requirements.txt 中的依赖（详细输出）..."
        pip install -r requirements.txt -i "$PIP_INDEX"
        if [ $? -ne 0 ]; then
            echo "警告: 部分依赖安装失败，请手动检查 requirements.txt"
        else
            echo "[成功] 所有依赖安装完成。"
        fi
    else
        echo "警告: 未找到 requirements.txt！建议手动创建并添加依赖。"
    fi
fi

# ===============================================
# 步骤4：数据库初始化
# ===============================================
DB_PATH="instance/site.db"
echo
if [ ! -f "$DB_PATH" ]; then
    echo "[步骤 4/6] 未检测到数据库，正在初始化..."
    if [ -f "init_schema.py" ]; then
        python init_schema.py
        if [ $? -eq 0 ] && [ -f "$DB_PATH" ]; then
            echo "[成功] 数据库初始化完成。"
        else
            echo "错误: 数据库初始化失败！请检查 init_schema.py"
            deactivate
            exit 1
        fi
    else
        echo "错误: 未找到 init_schema.py，无法初始化数据库。"
        deactivate
        exit 1
    fi
else
    echo "[步骤 4/6] 已检测到现有数据库，跳过初始化。"
fi

# ===============================================
# 步骤5：启动 Flask
# ===============================================
echo
echo "[步骤 5/6] 启动 Flask 项目..."
echo "访问地址：http://127.0.0.1:5000"
echo "按 Ctrl+C 可停止服务器。"
echo

# 尝试自动打开浏览器（不同系统兼容）
if command -v xdg-open >/dev/null 2>&1; then
    echo "[信息] Linux 系统，使用 xdg-open 打开浏览器..."
    nohup xdg-open http://127.0.0.1:5000 >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
    echo "[信息] macOS 系统，使用 open 打开浏览器..."
    open http://127.0.0.1:5000
elif command -v start >/dev/null 2>&1; then
    echo "[信息] Windows / Git Bash 系统，使用 start 打开浏览器..."
    start "" http://127.0.0.1:5000
else
    echo "[信息] 未找到浏览器打开命令，请手动访问 http://127.0.0.1:5000"
fi

echo "[信息] 启动 Flask 服务..."
python app.py

# 捕获退出状态
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "错误: Flask 运行异常，退出代码：$EXIT_CODE"
else
    echo "[信息] Flask 项目已正常停止。"
fi

# 停用虚拟环境
deactivate 2>/dev/null || true

echo
echo "=================================================="
echo "项目已停止。"
read -p "按 Enter 键退出..."
