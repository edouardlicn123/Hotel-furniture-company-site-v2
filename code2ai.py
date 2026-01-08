import os
import argparse
from pathlib import Path
from datetime import datetime

# 根据当前项目开发进度（2026年1月）优化监控范围
# 聚焦：后端 Flask、静态资源、主题 CSS、模板、配置、脚本、数据库迁移等核心代码
# 明确排除所有图片文件（包括 products 目录下的展示图），仅保留源码
INCLUDE_EXTENSIONS = {
    '.py',          # Flask 后端、脚本、工具
    '.html',        # Jinja2 模板
    '.css',         # 所有主题 CSS（特别是 themes/ 目录）
    '.js',          # 前端交互脚本
    '.json',        # 配置、package.json 等
    '.yaml', '.yml',# Docker Compose、GitHub Actions 等
    '.toml',        # pyproject.toml
    '.ini', '.cfg', # 配置文件
    '.env.example', # 环境变量示例
    '.sh', '.bat',  # 部署/启动脚本
    '.sql',         # 数据库迁移、初始数据
    '.md',          # README、文档（核心说明）
    '.dockerfile', 'dockerfile',  # Dockerfile
}

# 更严格的排除目录（避免噪声、敏感、二进制、生成物）
EXCLUDE_DIRS = {
    '__pycache__', '.git', '.svn', '.hg',
    '.idea', '.vscode',                     # IDE 配置
    'node_modules',                         # 前端依赖（体积巨大）
    '.venv', 'venv', 'env',                 # 虚拟环境
    'dist', 'build', 'target', '.next',     # 构建产物
    '.gradle', '.cache',                    # 缓存
    '.pytest_cache', '.mypy_cache', 'coverage',  # 测试缓存
    'code2ai',                              # 生成的审查输出目录（避免自引用）
    '.github',                              # workflows（非核心业务代码）
    'docs', 'examples',                     # 文档和示例（非项目主体）
    'instance',                             # Flask 默认 SQLite 数据库目录
    'migrations/versions',                  # Alembic 迁移版本（可从 migrations/env.py 推导，通常不需重复）
}

EXCLUDE_FILES = {
    '.gitignore', '.DS_Store', 'Thumbs.db',
    'project_review_*.txt',                 # 本脚本生成的审查文件
    'db.sqlite3', 'database.db',            # 实际运行数据库文件
}

DB_EXTENSIONS = {'.sqlite', '.sqlite3', '.db', '.mdb'}

# 明确排除所有图片格式（包括预数据图片）
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.bmp', '.tiff'}

def should_exclude(path: Path) -> bool:
    """
    判断是否应该排除某个路径（文件或目录）
    增强：更彻底排除生成物、敏感文件、运行时数据
    """
    if path.name in EXCLUDE_DIRS:
        return True
    if path.name in EXCLUDE_FILES:
        return True

    # 数据库文件
    if path.suffix.lower() in DB_EXTENSIONS:
        return True

    # 备份/临时文件
    if path.name.endswith('~') or path.name.startswith('.#'):
        return True

    # 彻底排除 code2ai 目录所有内容
    if 'code2ai' in path.parts:
        return True

    # 排除所有图片文件（包括 static/uploads/products/ 下的产品展示图）
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        return True

    # 排除字体、二进制图标等（非核心展示资源）
    if path.suffix.lower() in {'.woff2', '.ttf'}:
        return True

    # 排除 uploads 目录下所有内容（logo、products 等）
    if 'static/uploads' in path.parts:
        return True

    return False


def should_include(path: Path) -> bool:
    """判断文件是否应该被包含（严格聚焦核心源码）"""
    # 明确扩展名匹配
    if path.suffix.lower() in INCLUDE_EXTENSIONS:
        return True

    # Dockerfile 无扩展名特殊处理
    if path.name.lower() == 'dockerfile':
        return True

    # 特别包含 themes 目录下的所有 .css
    if path.suffix.lower() == '.css' and 'themes' in path.parts:
        return True

    return False


def collect_files(root_dir: Path):
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        current_path = Path(dirpath)

        # 原地修改 dirnames，提前跳过排除目录（大幅提升性能）
        dirnames[:] = [d for d in dirnames if not should_exclude(current_path / d)]

        for filename in filenames:
            file_path = current_path / filename

            if should_exclude(file_path):
                continue

            if should_include(file_path):
                files.append(file_path)

    return sorted(files)


def generate_output_path(root: Path, user_output: str) -> Path:
    """
    生成输出路径。
    默认优先使用 code2ai/ 目录并带时间戳，避免覆盖。
    """
    output = Path(user_output).expanduser().resolve()

    if output.is_dir() or output.suffix == "" or str(output).endswith("code2ai"):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"project_review_{timestamp}.txt"
        target_dir = root / "code2ai"
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / filename

    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def main():
    parser = argparse.ArgumentParser(
        description="将项目核心源码整合为单个 txt 文件，供 AI 审查使用（2026-01 更新版：完全排除所有图片文件）"
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="项目根目录路径（默认当前目录）"
    )
    parser.add_argument(
        "-o", "--output",
        default="code2ai/",
        help="输出路径。若为目录（默认 code2ai/），自动生成带时间戳的文件"
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=800_000,  # 恢复为 800KB（不再包含图片，文件更小）
        help="单个文件最大字节数，超过则跳过（默认 800KB）"
    )

    args = parser.parse_args()
    root = Path(args.project_dir).resolve()

    if not root.is_dir():
        print(f"错误：路径 {root} 不存在或不是目录")
        return

    output_path = generate_output_path(root, args.output)
    files = collect_files(root)

    print(f"正在扫描项目：{root}")
    print(f"找到 {len(files)} 个核心源码文件（已完全排除所有图片、二进制、上传文件等）")
    print(f"输出文件：{output_path}\n")

    skipped = 0
    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write(f"# 项目核心源码汇总（供 AI 审查）\n")
        outfile.write(f"# 项目路径：{root}\n")
        outfile.write(f"# 生成时间：{datetime.now().isoformat()}\n")
        outfile.write(f"# 包含文件数：{len(files)}\n\n")
        outfile.write("=" * 80 + "\n\n")

        for file_path in files:
            rel_path = file_path.relative_to(root)
            try:
                size = file_path.stat().st_size
                if size > args.max_size:
                    print(f"跳过超大文件：{rel_path} ({size/1024:.1f} KB)")
                    skipped += 1
                    continue

                content = file_path.read_text(encoding="utf-8", errors="replace")

                outfile.write(f"### 文件: {rel_path}\n")
                outfile.write(f"# 大小: {size} 字节\n")
                outfile.write("```\n")
                outfile.write(content.rstrip() + "\n")
                outfile.write("```\n")
                outfile.write("\n" + "-" * 80 + "\n\n")

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
