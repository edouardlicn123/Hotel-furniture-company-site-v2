#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
code2ai.py - 项目核心源码汇总工具（2026-01-13 更新版）

功能：扫描项目目录，收集核心源码文件（排除图片、上传、数据库、缓存等），
      生成带时间戳的审查文件，供 AI 审查使用。

当前状态（2026-01-13）：
- 购物车功能完整上线（询价邮件发送、验证码图片、发送频率限制、toast 通知）
- 联系页表单已实现（独立 /contact/send 路由，使用 smtplib 发送）
- 验证码从文字改为图片
- 前端全站 toast 通知替换 alert
- 购物车与联系表单防刷机制完善（30分钟冷却等）
- 后台管理强化完成（网站模式切换、企业介绍、联系方式全动态管理，包括电话、电邮、WhatsApp、WeChat、传真、地址）
- 前端全站同步显示（关于我们、联系页面、页脚）
- 新增后台独立 SMTP 配置管理页面（/admin/smtp）及专用主题 admin.css
- 邮件发送统一抽取到 app/utils/mail.py（smtplib + base64 AUTH），购物车、联系页、SMTP测试均已切换使用
- 关于我们页面、页脚、SEO 等模板修复完成（正确使用 settings.xxx 变量）
- 项目整体邮件发送、SEO占位符替换、模式切换（official/catalog）已稳定
"""

import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Set, List

# ==================== 配置常量 ====================

# 应包含的文件扩展名
INCLUDE_EXTENSIONS: Set[str] = {
    '.py', '.html', '.css', '.js', '.json',
    '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.env.example', '.sh', '.bat', '.sql', '.md'
}

# 严格排除的目录（运行时、生成物、IDE等）
EXCLUDE_DIRS: Set[str] = {
    '__pycache__', '.git', '.svn', '.hg',
    '.idea', '.vscode', 'node_modules',
    '.venv', 'venv', 'env', 'virtualenv',
    'dist', 'build', 'target', '.next',
    '.gradle', '.cache', '.pytest_cache',
    '.mypy_cache', 'coverage', 'code2ai',
    '.github', 'instance', 'migrations/versions',
}

# 严格排除的文件名
EXCLUDE_FILES: Set[str] = {
    '.gitignore', '.DS_Store', 'Thumbs.db',
    'db.sqlite3', 'site.db', 'database.db'
}

# 扩展排除：数据库、图片字体、备份文件
DB_EXTENSIONS: Set[str] = {'.sqlite', '.sqlite3', '.db', '.mdb'}
IMAGE_FONT_EXTENSIONS: Set[str] = {
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
    '.webp', '.bmp', '.tiff', '.avif',
    '.woff', '.woff2', '.ttf', '.otf', '.eot'
}

# 特殊包含规则（2026-01-13 更新：增加 utils/mail.py、更多模板覆盖）
SPECIAL_INCLUDE_RULES = [
    # 主题 CSS（包含 admin.css）
    lambda p: p.suffix.lower() == '.css' and 'themes' in p.parts,
    # admin 后台所有模板（含 SMTP 页面）
    lambda p: p.suffix.lower() == '.html' and 'admin' in p.parts,
    # partials 模板（含 admin_style.html、footer.html 等）
    lambda p: p.suffix.lower() == '.html' and 'partials' in p.parts,
    # series 前端模板
    lambda p: p.suffix.lower() == '.html' and p.parts[-2] == 'series' and 'templates' in p.parts,
    # 购物车页面模板
    lambda p: p.name == 'cart.html' and 'templates' in p.parts,
    # 联系页模板
    lambda p: p.name == 'contact.html' and 'templates' in p.parts,
    # 关于我们页面
    lambda p: p.name == 'about.html' and 'main' in p.parts,
    # 购物车 JS
    lambda p: p.name == 'cart.js' and p.parent.name == 'js' and 'static' in p.parts,
    # SMTP 路由文件
    lambda p: p.name == 'smtp.py' and 'admin' in p.parts,
    # 购物车路由文件
    lambda p: p.name == 'cart.py' and 'routes' in p.parts,
    # 联系页路由文件
    lambda p: p.name == 'contact.py' and 'routes' in p.parts,
    # 统一邮件工具（新增）
    lambda p: p.name == 'mail.py' and 'utils' in p.parts,
    # Dockerfile（无扩展名）
    lambda p: p.name.lower() == 'dockerfile',
]


# ==================== 核心判断函数 ====================

def is_excluded(path: Path) -> bool:
    """判断路径是否应被完全排除"""
    if path.name in EXCLUDE_DIRS or path.name in EXCLUDE_FILES:
        return True

    if path.suffix.lower() in DB_EXTENSIONS:
        return True

    if path.suffix.lower() in IMAGE_FONT_EXTENSIONS:
        return True

    if path.name.endswith('~') or path.name.startswith('.#'):
        return True

    if 'code2ai' in path.parts:
        return True

    if 'static/uploads' in str(path):
        return True

    # 排除 instance 目录下的所有文件（数据库已重建，不需监控）
    if 'instance' in path.parts:
        return True

    return False


def is_included(path: Path) -> bool:
    """判断文件是否为核心源码，应被包含"""
    # 基础扩展名匹配
    if path.suffix.lower() in INCLUDE_EXTENSIONS:
        return True

    # 特殊包含规则（已覆盖所有关键新增文件）
    for rule in SPECIAL_INCLUDE_RULES:
        if rule(path):
            return True

    return False


def collect_core_files(root_dir: Path) -> List[Path]:
    """收集所有核心源码文件"""
    core_files: List[Path] = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        current_path = Path(dirpath)

        # 就地修改 dirnames，跳过排除目录（提升性能）
        dirnames[:] = [d for d in dirnames if not is_excluded(current_path / d)]

        for filename in filenames:
            file_path = current_path / filename

            if is_excluded(file_path):
                continue

            if is_included(file_path):
                core_files.append(file_path)

    return sorted(core_files)


# ==================== 输出路径生成 ====================

def generate_output_path(root: Path, user_output: str) -> Path:
    """生成输出文件路径（默认 code2ai/ 目录下带时间戳）"""
    output = Path(user_output).expanduser().resolve()

    if output.is_dir() or output.suffix == "" or str(output).endswith("code2ai"):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"project_review_{timestamp}.txt"
        target_dir = root / "code2ai"
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / filename

    output.parent.mkdir(parents=True, exist_ok=True)
    return output


# ==================== 主函数 ====================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="将项目核心源码整合为单个 txt 文件，供 AI 审查使用（优化结构版）"
    )
    parser.add_argument(
        "project_dir", nargs="?", default=".", help="项目根目录路径（默认当前目录）"
    )
    parser.add_argument(
        "-o", "--output", default="code2ai/", help="输出路径（目录则自动生成带时间戳文件名）"
    )
    parser.add_argument(
        "--max-size", type=int, default=1_000_000, help="单个文件最大字节数（默认 1MB）"
    )

    args = parser.parse_args()
    root = Path(args.project_dir).resolve()

    if not root.is_dir():
        print(f"错误：路径 {root} 不存在或不是目录")
        return

    output_path = generate_output_path(root, args.output)
    files = collect_core_files(root)

    print(f"正在扫描项目：{root}")
    print(f"找到 {len(files)} 个核心源码文件")
    print(f"输出文件：{output_path}\n")

    skipped = 0
    with open(output_path, "w", encoding="utf-8") as f:
        header = f"""# 项目核心源码汇总（供 AI 审查）
# 项目路径：{root}
# 生成时间：{datetime.now().isoformat()}
# 包含文件数：{len(files)}
# 已优化排除：图片、上传文件、数据库、缓存、IDE 配置等
# 当前状态（2026-01-13）：
# - 购物车功能完整上线（询价邮件发送、验证码图片、发送频率限制、toast 通知）
# - 联系页表单已实现（独立 /contact/send 路由，使用 smtplib 发送）
# - 验证码从文字改为图片
# - 前端全站 toast 通知替换 alert
# - 购物车与联系表单防刷机制完善（30分钟冷却等）
# - 后台管理强化完成（网站模式切换、企业介绍、联系方式全动态管理，包括电话、电邮、WhatsApp、WeChat、传真、地址）
# - 前端全站同步显示（关于我们、联系页面、页脚）
# - 新增后台独立 SMTP 配置管理页面（/admin/smtp）及专用主题 admin.css
# - 邮件发送统一抽取到 app/utils/mail.py（smtplib + base64 AUTH），购物车、联系页、SMTP测试均已切换使用
# - 关于我们页面、页脚、SEO 等模板修复完成（正确使用 settings.xxx 变量）
# - 项目整体邮件发送、SEO占位符替换、模式切换（official/catalog）已稳定

{"=" * 80}

"""
        f.write(header)

        for file_path in files:
            rel_path = file_path.relative_to(root)
            try:
                size = file_path.stat().st_size
                if size > args.max_size:
                    print(f"跳过超大文件：{rel_path} ({size/1024:.1f} KB)")
                    skipped += 1
                    continue

                content = file_path.read_text(encoding="utf-8", errors="replace")

                f.write(f"### 文件: {rel_path}\n")
                f.write(f"# 大小: {size} 字节\n")
                f.write("```\n")
                f.write(content.rstrip() + "\n")
                f.write("```\n")
                f.write("\n" + "-" * 80 + "\n\n")

            except Exception as e:
                print(f"读取失败：{rel_path} ({e})")
                skipped += 1

    total_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n生成完成！")
    print(f"   输出文件：{output_path}")
    if skipped:
        print(f"   跳过 {skipped} 个文件（超大或异常）")
    print(f"   总大小：{total_mb:.2f} MB")


if __name__ == "__main__":
    main()
