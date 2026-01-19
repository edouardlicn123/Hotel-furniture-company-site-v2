#!/bin/bash

# 设置终端编码为 UTF-8，确保中文显示正常
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

clear

# 颜色定义（可选，增强可读性）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================================${NC}"
echo -e "     酒店家具厂官网 - 一键启动脚本 "
echo -e "     支持自动 SECRET_KEY + 依赖增量安装 + debug 开关"
echo -e "${GREEN}==================================================${NC}"
echo

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[信息] 项目根目录: $PROJECT_ROOT"
cd "$PROJECT_ROOT" || { echo -e "${RED}错误: 无法进入项目目录！${NC}"; exit 1; }

# 虚拟环境目录
VENV_DIR="venv"

# 使用国内镜像加速（可根据需要注释掉）
PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
# PIP_INDEX="https://pypi.org/simple"  # 国际源备用

# 环境文件
ENV_FILE=".env"

# debug 模式开关（强烈建议开发时改为 True）
FLASK_DEBUG="True"  # 改成 True 後第一次連接失敗的機率會大幅降低

echo
echo "[信息] 检查 Python3 是否已安装..."
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}错误: 未在 PATH 中找到 python3！请先安装 Python 3.9 或更高版本。${NC}"
    read -p "按 Enter 键退出..."
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1)
echo "[信息] 已找到 $PYTHON_VERSION"

# ===============================================
# 步骤1：检查并处理 .env 文件 + SECRET_KEY
# ===============================================
echo
echo "[步骤 1/7] 检查并准备 SECRET_KEY（.env 文件）..."

if [ ! -f "$ENV_FILE" ]; then
    echo "[信息] 未找到 .env 文件，正在创建..."
    touch "$ENV_FILE"
fi

if ! grep -q "FLASK_SECRET_KEY" "$ENV_FILE"; then
    echo "[信息] 未检测到 FLASK_SECRET_KEY，正在生成安全的随机密钥..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    echo "FLASK_SECRET_KEY=$SECRET_KEY" >> "$ENV_FILE"
    echo -e "[${GREEN}成功${NC}] 已自动生成并写入 SECRET_KEY"
else
    echo "[信息] 已检测到现有的 FLASK_SECRET_KEY，跳过生成。"
fi

# ===============================================
# 步骤2：虚拟环境
# ===============================================
echo
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[步骤 2/7] 未检测到虚拟环境，正在创建..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: 创建虚拟环境失败！请检查 Python3 和 venv 模块。${NC}"
        exit 1
    fi
    echo -e "[${GREEN}成功${NC}] 虚拟环境创建完成。"
else
    echo "[步骤 2/7] 已检测到现有虚拟环境，跳过创建。"
fi

# 激活虚拟环境
echo "[信息] 正在激活虚拟环境..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo -e "${RED}错误: 激活虚拟环境失败！${NC}"
    exit 1
fi
echo "[信息] 虚拟环境已激活（$(python --version)）"

# ===============================================
# 步骤3：依赖安装（增量 + 校验）
# ===============================================
echo
echo "[步骤 3/7] 检查并安装项目依赖..."

if python -c "import flask" 2>/dev/null; then
    echo "[信息] Flask 已安装，检查 requirements.txt 是否变化..."
    
    if [ -f "requirements.txt" ]; then
        CURRENT_MD5=$(md5sum requirements.txt 2>/dev/null | cut -d' ' -f1)
        LAST_MD5=$(cat .requirements.md5 2>/dev/null || echo "")
        
        if [ "$CURRENT_MD5" = "$LAST_MD5" ]; then
            echo "[信息] requirements.txt 无变化，跳过安装。"
        else
            echo "[信息] requirements.txt 有更新，正在安装..."
            pip install --upgrade pip -i "$PIP_INDEX" --quiet
            pip install -r requirements.txt -i "$PIP_INDEX"
            if [ $? -eq 0 ]; then
                md5sum requirements.txt > .requirements.md5
                echo -e "[${GREEN}成功${NC}] 依赖安装完成。"
            else
                echo -e "${YELLOW}警告: 部分依赖安装失败，请手动检查。${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}警告: 未找到 requirements.txt，建议手动创建。${NC}"
    fi
else
    echo "[信息] 核心依赖缺失，正在完整安装..."
    pip install --upgrade pip -i "$PIP_INDEX" --quiet
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -i "$PIP_INDEX"
    else
        echo -e "${YELLOW}警告: 未找到 requirements.txt！${NC}"
    fi
fi

# ===============================================
# 步骤4：数据库初始化（带备份）
# ===============================================
DB_PATH="instance/site.db"
BACKUP_PATH="instance/site.db.bak.$(date +%Y%m%d_%H%M%S)"
echo
if [ ! -f "$DB_PATH" ]; then
    echo "[步骤 4/7] 未检测到数据库，正在初始化..."
    if [ -f "init_schema.py" ]; then
        python init_schema.py
        if [ $? -eq 0 ] && [ -f "$DB_PATH" ]; then
            echo -e "[${GREEN}成功${NC}] 数据库初始化完成。"
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
    echo "[步骤 4/7] 已检测到现有数据库，正在备份..."
    cp "$DB_PATH" "$BACKUP_PATH"
    echo "[信息] 旧数据库已备份到 $BACKUP_PATH"
    echo "[信息] 跳过初始化，使用现有数据库。"
fi

# ===============================================
# 步骤5：启动 Flask（關鍵修改在此）
# ===============================================
echo
echo -e "[步骤 5/7] 启动 Flask 项目..."
echo -e "访问地址：${GREEN}http://127.0.0.1:5000${NC}"
echo -e "Debug 模式：${YELLOW}$FLASK_DEBUG${NC}"
echo "按 Ctrl+C 可停止服务器。"
echo

# 先在背景啟動 Flask
echo -e "${YELLOW}正在启动 Flask 服务器（后台运行）...${NC}"
python app.py > flask.log 2>&1 &

# 記錄進程 ID
FLASK_PID=$!

# 等待伺服器真正可以回應（最多等 15 秒）
echo -e "等待服务器就绪（最多 15 秒）..."
for i in {1..30}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000 2>/dev/null)
    if [[ "$HTTP_CODE" =~ ^(200|30[0-9])$ ]]; then
        echo -e "${GREEN}服务器已就绪！（HTTP $HTTP_CODE）${NC}"
        break
    fi
    printf "."
    sleep 0.5
done
echo ""  # 換行

# 檢查 Flask 是否還在運行
if ! ps -p $FLASK_PID > /dev/null; then
    echo -e "${RED}警告：Flask 似乎启动失败，请查看 flask.log 获取错误信息${NC}"
    cat flask.log | tail -n 20
    deactivate
    exit 1
fi

# 伺服器就緒後再開瀏覽器
echo -e "${GREEN}尝试自动打开浏览器...${NC}"
if command -v xdg-open >/dev/null 2>&1; then
    nohup xdg-open http://127.0.0.1:5000 >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
    open http://127.0.0.1:5000 &
elif command -v start >/dev/null 2>&1; then
    start "" http://127.0.0.1:5000 &
else
    echo "[信息] 未找到浏览器自动打开命令，请手动访问 http://127.0.0.1:5000"
fi

# 把 Flask 进程拉回前台，讓使用者可以 Ctrl+C 正常關閉
echo -e "${GREEN}服务器运行中...${NC}（在此窗口按 Ctrl+C 停止）"
wait $FLASK_PID

# 捕获退出状态
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}错误: Flask 运行异常，退出代码：$EXIT_CODE${NC}"
    echo "最后 20 行日志："
    tail -n 20 flask.log
else
    echo -e "[${GREEN}信息${NC}] Flask 项目已正常停止。"
fi

# 停用虚拟环境
deactivate 2>/dev/null || true

echo
echo -e "${GREEN}==================================================${NC}"
echo "项目已停止。"
read -p "按 Enter 键退出..."
