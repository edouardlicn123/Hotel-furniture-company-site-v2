#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
code2ai.py - 项目核心源码汇总工具（优化结构版）

功能：扫描项目目录，收集核心源码文件（排除图片、上传、数据库、缓存等），
      生成带时间戳的审查文件，供 AI 审查使用。

支持动态配置：优先读取项目根目录下的 code2ai_config.toml（推荐），
               其次使用内置默认规则。
               便于项目内增删监视文件范围，无需修改脚本本体。

当前状态（2026-01-13）：已完成购物车、联系表单、后台 SMTP、模式切换等功能，
                         前端 toast 通知全站替换，验证码图片化，防刷机制完善。
"""

import os
import argparse
import tomllib
from pathlib import Path
from datetime import datetime
from typing import Set, List, Dict, Any

# ==================== 默认内置规则（当没有配置文件时使用） ====================

DEFAULT_CONFIG = {
    "include": {
        "extensions": [
            '.py', '.html', '.css', '.js', '.json',
            '.yaml', '.yml', '.toml', '.ini', '.cfg',
            '.env.example', '.sh', '.bat', '.sql', '.md'
        ]
    },
    "exclude": {
        "dirs": [
            '__pycache__', '.git', '.svn', '.hg',
            '.idea', '.vscode', 'node_modules',
            '.venv', 'venv', 'env', 'virtualenv',
            'dist', 'build', 'target', '.next',
            '.gradle', '.cache', '.pytest_cache',
            '.mypy_cache', 'coverage', 'code2ai',
            '.github', 'instance', 'migrations/versions',
        ],
        "files": [
            '.gitignore', '.DS_Store', 'Thumbs.db',
            'db.sqlite3', 'site.db', 'database.db'
        ],
        "extensions": [
            '.sqlite', '.sqlite3', '.db', '.mdb',
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
            '.webp', '.bmp', '.tiff', '.avif',
            '.woff', '.woff2', '.ttf', '.otf', '.eot'
        ]
    },
    "special_include": [
        # 主题 CSS
        lambda p: p.suffix.lower() == '.css' and 'themes' in p.parts,
        # admin 后台模板
        lambda p: p.suffix.lower() == '.html' and 'admin' in p.parts,
        # admin 相关 partials
        lambda p: p.suffix.lower() == '.html' and 'partials' in p.parts and 'admin' in p.name.lower(),
        # series 模板
        lambda p: p.suffix.lower() == '.html' and p.parts[-2] == 'series' and 'templates' in p.parts,
        # 购物车页面
        lambda p: p.name == 'cart.html' and 'templates' in p.parts,
        # 联系页
        lambda p: p.name == 'contact.html' and 'templates' in p.parts,
        # 购物车 JS
        lambda p: p.name == 'cart.js' and p.parent.name == 'js' and 'static' in p.parts,
        # SMTP 路由
        lambda p: p.name == 'smtp.py' and 'admin' in p.parts,
        # 购物车路由
        lambda p: p.name == 'cart.py' and 'routes' in p.parts,
        # Dockerfile
        lambda p: p.name.lower() == 'dockerfile',
        # 联系页路由
        lambda p: p.name == 'contact.py' and 'routes' in p.parts,
    ],
    "output": {
        "default_dir": "code2ai",
        "max_file_size_kb": 1000
    }
}

# ==================== 配置加载函数 ====================

def load_config(root: Path) -> Dict[str, Any]:
    """优先加载项目根目录下的 code2ai_config.toml，无则使用内置默认配置"""
    config_file = root / "code2ai_config.toml"
    
    if config_file.is_file():
        try:
            with open(config_file, "rb") as f:
                loaded = tomllib.load(f)
            print(f"[INFO] 已加载项目配置文件: {config_file}")
            return loaded
        except Exception as e:
            print(f"[WARNING] 配置文件加载失败: {e}，使用内置默认配置")
    
    print("[INFO] 未找到 code2ai_config.toml，使用内置默认规则")
    return DEFAULT_CONFIG


# ==================== 核心判断函数 ====================

def is_excluded(path: Path, config: Dict[str, Any]) -> bool:
    exclude = config.get("exclude", {})
    
    if path.name in exclude.get("dirs", []) or path.name in exclude.get("files", []):
        return True
    
    if path.suffix.lower() in exclude.get("extensions", []):
        return True
    
    if path.name.endswith('~') or path.name.startswith('.#'):
        return True
    
    if 'code2ai' in path.parts or 'static/uploads' in str(path) or 'instance' in path.parts:
        return True
    
    return False


def is_included(path: Path, config: Dict[str, Any]) -> bool:
    include = config.get("include", {})
    special = config.get("special_include", [])
    
    # 基础扩展名匹配
    if path.suffix.lower() in include.get("extensions", []):
        return True
    
    # 特殊包含规则（lambda 函数列表）
    for rule in special:
        if callable(rule) and rule(path):
            return True
    
    return False


def collect_core_files(root_dir: Path, config: Dict[str, Any]) -> List[Path]:
    """根据配置收集核心源码文件"""
    core_files: List[Path] = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        current_path = Path(dirpath)

        # 跳过排除目录
        dirnames[:] = [d for d in dirnames if not is_excluded(current_path / d, config)]

        for filename in filenames:
            file_path = current_path / filename

            if is_excluded(file_path, config):
                continue

            if is_included(file_path, config):
                core_files.append(file_path)

    return sorted(core_files)


# ==================== 输出路径生成 ====================

def generate_output_path(root: Path, user_output: str, config: Dict[str, Any]) -> Path:
    """生成输出文件路径（优先使用配置中的 default_dir）"""
    output = Path(user_output).expanduser().resolve()
    default_dir = config.get("output", {}).get("default_dir", "code2ai")

    if output.is_dir() or output.suffix == "" or str(output).endswith("code2ai"):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"project_review_{timestamp}.txt"
        target_dir = root / default_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / filename

    output.parent.mkdir(parents=True, exist_ok=True)
    return output


# ==================== 主函数 ====================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="项目核心源码整合工具 - 用于 AI 审查（支持项目内配置文件）"
    )
    parser.add_argument(
        "project_dir", nargs="?", default=".", help="项目根目录路径（默认当前目录）"
    )
    parser.add_argument(
        "-o", "--output", default="code2ai/", help="输出路径（目录则自动生成带时间戳文件名）"
    )
    parser.add_argument(
        "--max-size", type=int, help="单个文件最大字节数（默认使用配置值）"
    )

    args = parser.parse_args()
    root = Path(args.project_dir).resolve()

    if not root.is_dir():
        print(f"错误：路径 {root} 不存在或不是目录")
        return

    # 加载配置
    config = load_config(root)

    # 允许命令行覆盖 max_file_size
    if args.max_size is not None:
        config.setdefault("output", {})["max_file_size_kb"] = args.max_size // 1024

    output_path = generate_output_path(root, args.output, config)
    files = collect_core_files(root, config)

    print(f"正在扫描项目：{root}")
    print(f"使用配置：{'项目配置文件' if 'toml' in str(config) else '内置默认规则'}")
    print(f"找到 {len(files)} 个核心源码文件")
    print(f"输出文件：{output_path}\n")

    skipped = 0
    with open(output_path, "w", encoding="utf-8") as f:
        header = f"""# 项目核心源码汇总（供 AI 审查）
# 项目路径：{root}
# 生成时间：{datetime.now().isoformat()}
# 包含文件数：{len(files)}
# 配置来源：{'项目 code2ai_config.toml' if (root / 'code2ai_config.toml').exists() else '脚本内置默认规则'}
# 已优化排除：图片、上传文件、数据库、缓存、IDE 配置等

{"=" * 80}

"""
        f.write(header)

        max_size = (config.get("output", {}).get("max_file_size_kb", 1000)) * 1024

        for file_path in files:
            rel_path = file_path.relative_to(root)
            try:
                size = file_path.stat().st_size
                if size > max_size:
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
