#!/bin/bash

# 设置终端编码为 UTF-8，确保中文显示正常
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

clear

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

echo -e "${GREEN}==================================================${NC}"
echo -e "     酒店家具厂官网 - 一键启动脚本（最终稳定版）"
echo -e "     直接前台启动 · 只打印一次启动信息 · 兼容 Flask 3.x"
echo -e "${GREEN}==================================================${NC}"
echo

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[信息] 项目根目录: $PROJECT_ROOT"
cd "$PROJECT_ROOT" || { echo -e "${RED}错误: 无法进入项目目录！${NC}"; exit 1; }

# 虚拟环境目录
VENV_DIR="venv"

# 国内 pip 镜像（可注释掉使用国际源）
PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
# PIP_INDEX="https://pypi.org/simple"

# 环境文件
ENV_FILE=".env"

# Debug 模式（开发时建议保持 True）
FLASK_DEBUG="True"

echo
echo "[信息] 检查 Python3 是否已安装..."
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}错误: 未在 PATH 中找到 python3！请先安装 Python 3.9 或更高版本。${NC}"
    read -p "按 Enter 键退出..."
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1)
echo "[信息] 已找到 $PYTHON_VERSION"

# ───────────────────────────────────────────────
# 步骤1：处理 .env 和 SECRET_KEY
# ───────────────────────────────────────────────
echo
echo "[步骤 1/6] 检查并准备 SECRET_KEY（.env 文件）..."

[ ! -f "$ENV_FILE" ] && touch "$ENV_FILE"

if ! grep -q "FLASK_SECRET_KEY" "$ENV_FILE"; then
    echo "[信息] 未检测到 FLASK_SECRET_KEY，正在生成..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    echo "FLASK_SECRET_KEY=$SECRET_KEY" >> "$ENV_FILE"
    echo -e "[${GREEN}成功${NC}] 已生成并写入 SECRET_KEY"
else
    echo "[信息] 已检测到现有 SECRET_KEY，跳过生成"
fi

# ───────────────────────────────────────────────
# 步骤2：虚拟环境
# ───────────────────────────────────────────────
echo
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[步骤 2/6] 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
    [ $? -ne 0 ] && { echo -e "${RED}错误: 创建虚拟环境失败！${NC}"; exit 1; }
    echo -e "[${GREEN}成功${NC}] 虚拟环境创建完成"
else
    echo "[步骤 2/6] 检测到现有虚拟环境，跳过创建"
fi

echo "[信息] 激活虚拟环境..."
source "$VENV_DIR/bin/activate"
[ $? -ne 0 ] && { echo -e "${RED}错误: 激活虚拟环境失败！${NC}"; exit 1; }
echo "[信息] 虚拟环境已激活（$(python --version)）"

# ───────────────────────────────────────────────
# 步骤3：依赖安装（增量 + MD5 校验）
# ───────────────────────────────────────────────
echo
echo "[步骤 3/6] 检查并安装依赖..."

if python -c "import flask" 2>/dev/null; then
    if [ -f "requirements.txt" ]; then
        CURRENT_MD5=$(md5sum requirements.txt 2>/dev/null | cut -d' ' -f1)
        LAST_MD5=$(cat .requirements.md5 2>/dev/null || echo "")
        
        if [ "$CURRENT_MD5" = "$LAST_MD5" ]; then
            echo "[信息] requirements.txt 无变化，跳过安装"
        else
            echo "[信息] requirements.txt 有更新，正在安装..."
            pip install --upgrade pip -i "$PIP_INDEX" --quiet
            pip install -r requirements.txt -i "$PIP_INDEX"
            [ $? -eq 0 ] && md5sum requirements.txt > .requirements.md5
            echo -e "[${GREEN}成功${NC}] 依赖安装完成"
        fi
    else
        echo -e "${YELLOW}警告: 未找到 requirements.txt，建议手动创建${NC}"
    fi
else
    echo "[信息] 核心依赖缺失，进行完整安装..."
    pip install --upgrade pip -i "$PIP_INDEX" --quiet
    [ -f "requirements.txt" ] && pip install -r requirements.txt -i "$PIP_INDEX"
fi

# ───────────────────────────────────────────────
# 步骤4：数据库检查与初始化
# ───────────────────────────────────────────────
DB_PATH="instance/site.db"
BACKUP_PATH="instance/site.db.bak.$(date +%Y%m%d_%H%M%S)"
echo
if [ ! -f "$DB_PATH" ]; then
    echo "[步骤 4/6] 未找到数据库，正在初始化..."
    if [ -f "init_schema.py" ]; then
        python init_schema.py
        if [ $? -eq 0 ] && [ -f "$DB_PATH" ]; then
            echo -e "[${GREEN}成功${NC}] 数据库初始化完成"
        else
            echo -e "${RED}错误: 数据库初始化失败！请检查 init_schema.py${NC}"
            deactivate
            exit 1
        fi
    else
        echo -e "${RED}错误: 未找到 init_schema.py！${NC}"
        deactivate
        exit 1
    fi
else
    echo "[步骤 4/6] 检测到现有数据库，正在备份..."
    cp "$DB_PATH" "$BACKUP_PATH"
    echo "[信息] 旧数据库已备份至 $BACKUP_PATH"
    echo "[信息] 使用现有数据库，跳过初始化"
fi

# ───────────────────────────────────────────────
# 步骤5：启动 Flask（直接前台运行，只打印一次启动信息）
# ───────────────────────────────────────────────
echo
echo -e "[步骤 5/6] 启动 Flask 项目..."
echo -e "访问地址：${GREEN}http://127.0.0.1:5000${NC}"
echo -e "Debug 模式：${YELLOW}$FLASK_DEBUG${NC}"
echo "按 Ctrl+C 可安全停止服务器"
echo

# 设置环境变量，flask run 会自动读取
export FLASK_DEBUG="$FLASK_DEBUG"

# 直接在前台启动（不使用 & 和 wait）
# 这样启动信息只会出现一次，且终端控制权直接交给 Flask
python -m flask run \
    --host=0.0.0.0 \
    --port=5000 \
    --no-reload \
    --debug

# 下面的代码只有在用户 Ctrl+C 后才会执行
echo
echo -e "[${GREEN}信息${NC}] 项目已正常停止（用户手动终止）"

# ───────────────────────────────────────────────
# 清理
# ───────────────────────────────────────────────
deactivate 2>/dev/null || true

echo
echo -e "${GREEN}==================================================${NC}"
echo "脚本执行结束。"
read -p "按 Enter 键退出..."
