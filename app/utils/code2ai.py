#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
code2ai.py - 项目核心源码汇总工具（带索引版）

功能：扫描项目目录，收集核心源码文件，生成带清晰索引的审查文件。
      新增：文件清单 + 醒目分隔符 + 开始/结束标记

支持动态配置：优先读取 code2ai_config.toml，其次使用内置默认规则。
"""

import os
import argparse
import tomllib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# ==================== 默认内置规则 ====================

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
        lambda p: p.suffix.lower() == '.css' and 'themes' in p.parts,
        lambda p: p.suffix.lower() == '.html' and 'admin' in p.parts,
        lambda p: p.suffix.lower() == '.html' and 'partials' in p.parts and 'admin' in p.name.lower(),
        lambda p: p.suffix.lower() == '.html' and p.parts[-2] == 'series' and 'templates' in p.parts,
        lambda p: p.name == 'cart.html' and 'templates' in p.parts,
        lambda p: p.name == 'contact.html' and 'templates' in p.parts,
        lambda p: p.name == 'cart.js' and p.parent.name == 'js' and 'static' in p.parts,
        lambda p: p.name == 'smtp.py' and 'admin' in p.parts,
        lambda p: p.name == 'cart.py' and 'routes' in p.parts,
        lambda p: p.name.lower() == 'dockerfile',
        lambda p: p.name == 'contact.py' and 'routes' in p.parts,
    ],
    "output": {
        "default_dir": "code2ai",
        "max_file_size_kb": 10240   # 修改為 10MB (10240KB)
    }
}

# ==================== 配置加载 ====================

def load_config(root: Path) -> Dict[str, Any]:
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

# ==================== 文件过滤函数 ====================

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
    if path.suffix.lower() in include.get("extensions", []):
        return True
    for rule in special:
        if callable(rule) and rule(path):
            return True
    return False

def collect_core_files(root_dir: Path, config: Dict[str, Any]) -> List[Path]:
    core_files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        current_path = Path(dirpath)
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

# ==================== 分隔线常量 ====================

SEPARATOR = "────────────────────────────────────────────────────────────────"

# ==================== 主函数 ====================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="项目核心源码整合工具 - 带索引版（用于 AI 审查）"
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

    config = load_config(root)

    # 允许命令行参数覆盖最大文件大小（单位：字节）
    if args.max_size is not None:
        config.setdefault("output", {})["max_file_size_kb"] = args.max_size // 1024

    output_path = generate_output_path(root, args.output, config)
    files = collect_core_files(root, config)

    print(f"正在扫描项目：{root}")
    print(f"使用配置：{'项目配置文件' if (root / 'code2ai_config.toml').exists() else '内置默认规则'}")
    print(f"找到 {len(files)} 个核心源码文件")
    print(f"输出文件：{output_path}\n")

    skipped = 0
    # 使用配置中的值，fallback 到 10MB (10240KB)
    max_size = (config.get("output", {}).get("max_file_size_kb", 10240)) * 1024

    # 先收集文件信息，用于生成清单
    file_info_list = []
    for file_path in files:
        rel_path = file_path.relative_to(root)
        try:
            size = file_path.stat().st_size
            if size > max_size:
                print(f"跳过超大文件：{rel_path} ({size/1024:.1f} KB)")
                skipped += 1
                continue
            file_info_list.append((rel_path, size))
        except Exception as e:
            print(f"无法获取文件信息：{rel_path} ({e})")
            skipped += 1

    # 开始写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        # 头部信息
        header = f"""# 项目核心源码汇总（供 AI 审查）
# 项目路径：{root}
# 生成时间：{datetime.now().isoformat()}
# 包含文件数：{len(file_info_list)}
# 配置来源：{'项目 code2ai_config.toml' if (root / 'code2ai_config.toml').exists() else '脚本内置默认规则'}
# 已优化排除：图片、上传文件、数据库、缓存、IDE 配置等

{SEPARATOR}

# 完整文件清单（用于快速定位）
{SEPARATOR}
"""
        f.write(header)

        # 写入文件清单
        for i, (rel_path, size) in enumerate(file_info_list, 1):
            rel_path_str = str(rel_path)
            f.write(f"{i:2d}. {rel_path_str:<60} ({size:,} 字节)\n")

        f.write(f"\n共 {len(file_info_list)} 个文件（已跳过 {skipped} 个超大/异常文件）\n\n")
        f.write(f"{SEPARATOR}\n")
        f.write("# 文件内容开始\n")
        f.write(f"{SEPARATOR}\n\n")

        # 逐个写入文件内容
        for rel_path, _ in file_info_list:
            file_path = root / rel_path
            size = file_path.stat().st_size

            f.write(f"{SEPARATOR}\n")
            f.write(f"# 文件: {rel_path}\n")
            f.write(f"# 大小: {size:,} 字节\n")
            f.write(f"# 路径: {rel_path}\n")
            f.write(f"{SEPARATOR}\n")
            f.write("```\n")

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                f.write(content.rstrip() + "\n")
            except Exception as e:
                f.write(f"# 读取失败：{e}\n")

            f.write("```\n")
            f.write(f"\n{SEPARATOR}\n")
            f.write(f"# 文件 {rel_path} 结束\n")
            f.write(f"{SEPARATOR}\n\n")

    total_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n生成完成！")
    print(f"   输出文件：{output_path}")
    if skipped:
        print(f"   跳过 {skipped} 个文件（超大或异常）")
    print(f"   总大小：{total_mb:.2f} MB")


if __name__ == "__main__":
    main()
