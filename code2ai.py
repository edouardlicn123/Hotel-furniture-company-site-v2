import os
import argparse
from pathlib import Path
from datetime import datetime

# ==================== 2026-01-09 项目最新核心文件监控范围（专题系列功能已完成） ====================

INCLUDE_EXTENSIONS = {
    '.py',          # Flask 后端、路由、模型、工具脚本、启动脚本
    '.html',        # Jinja2 模板（包括 partials、admin、series 模板）
    '.css',         # 所有 CSS（base.css、custom.css、themes/*.css）
    '.js',          # 前端 JS（如 custom.js）
    '.json',        # 配置（如 package.json，如果有）
    '.yaml', '.yml',# Docker、GitHub Actions 等
    '.toml',        # pyproject.toml
    '.ini', '.cfg', # 配置文件
    '.env.example', # 环境变量模板
    '.sh', '.bat',  # 启动脚本（run.sh、run.bat 等）
    '.sql',         # 数据库初始脚本（如有）
    '.md',          # README、文档
    '.dockerfile',  # Dockerfile（无扩展名）
}

# 严格排除的目录（运行时、生成物、IDE、依赖）
EXCLUDE_DIRS = {
    '__pycache__', '.git', '.svn', '.hg',
    '.idea', '.vscode',                     # IDE 配置
    'node_modules',                         # 前端依赖
    '.venv', 'venv', 'env', 'virtualenv',   # 虚拟环境
    'dist', 'build', 'target', '.next',     # 构建产物
    '.gradle', '.cache',                    # 缓存
    '.pytest_cache', '.mypy_cache', 'coverage',  # 测试缓存
    'code2ai',                              # 本脚本生成的输出目录（避免自引用）
    '.github',                              # CI/CD 配置（非核心业务代码）
    'instance',                             # Flask SQLite 数据库目录
    'migrations/versions',                  # Alembic 具体迁移文件（env.py 足以代表）
    'static/uploads',                       # 所有上传文件（logo、产品图片、系列图片等）
}

# 严格排除的文件
EXCLUDE_FILES = {
    '.gitignore', '.DS_Store', 'Thumbs.db',
    'project_review_*.txt',                 # 本脚本生成的文件
    'db.sqlite3', 'site.db', 'database.db', # 运行时数据库
}

# 数据库文件扩展名
DB_EXTENSIONS = {'.sqlite', '.sqlite3', '.db', '.mdb'}

# 所有图片及字体资源（彻底排除）
IMAGE_FONT_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
    '.webp', '.bmp', '.tiff', '.avif',
    '.woff', '.woff2', '.ttf', '.otf', '.eot'
}

def should_exclude(path: Path) -> bool:
    """判断是否应排除该路径（目录或文件）"""
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

    # 彻底排除 code2ai 目录
    if 'code2ai' in path.parts:
        return True

    # 排除所有图片和字体资源
    if path.suffix.lower() in IMAGE_FONT_EXTENSIONS:
        return True

    # 排除任何 uploads 下的内容（已在上方目录排除，但双保险）
    if 'static/uploads' in str(path):
        return True

    return False


def should_include(path: Path) -> bool:
    """判断文件是否为核心源码，应被包含"""
    # 标准扩展名
    if path.suffix.lower() in INCLUDE_EXTENSIONS:
        return True

    # 无扩展名的 Dockerfile
    if path.name.lower() == 'dockerfile':
        return True

    # 特别确保 themes 目录下所有 .css 被包含
    if path.suffix.lower() == '.css' and 'themes' in path.parts:
        return True

    # 特别包含 admin 模板目录下的 .html
    if path.suffix.lower() == '.html' and 'admin' in path.parts:
        return True

    # 特别包含 partials 目录下的所有 .html
    if path.suffix.lower() == '.html' and 'partials' in path.parts:
        return True

    # 新增：特别包含 series 前端模板目录下的 .html（专题系列功能已上线）
    if path.suffix.lower() == '.html' and path.parts[-2] == 'series' and 'templates' in path.parts:
        return True

    return False


def collect_files(root_dir: Path):
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        current_path = Path(dirpath)

        # 提前过滤子目录，提升性能
        dirnames[:] = [d for d in dirnames if not should_exclude(current_path / d)]

        for filename in filenames:
            file_path = current_path / filename

            if should_exclude(file_path):
                continue

            if should_include(file_path):
                files.append(file_path)

    return sorted(files)


def generate_output_path(root: Path, user_output: str) -> Path:
    """生成输出路径，默认在 code2ai/ 目录下带时间戳"""
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
        description="将项目核心源码整合为单个 txt 文件，供 AI 审查使用（2026-01-09 专题系列功能已完成版）"
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
        default=1_000_000,  # 1MB（当前源码文件都不大）
        help="单个文件最大字节数，超过则跳过（默认 1MB）"
    )

    args = parser.parse_args()
    root = Path(args.project_dir).resolve()

    if not root.is_dir():
        print(f"错误：路径 {root} 不存在或不是目录")
        return

    output_path = generate_output_path(root, args.output)
    files = collect_files(root)

    print(f"正在扫描项目：{root}")
    print(f"找到 {len(files)} 个核心源码文件（已排除图片、数据库、缓存、上传文件等）")
    print(f"输出文件：{output_path}\n")

    skipped = 0
    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write(f"# 项目核心源码汇总（供 AI 审查）\n")
        outfile.write(f"# 项目路径：{root}\n")
        outfile.write(f"# 生成时间：{datetime.now().isoformat()}\n")
        outfile.write(f"# 包含文件数：{len(files)}\n")
        outfile.write(f"# 已优化排除：图片、上传文件、数据库、缓存、IDE 配置等\n")
        outfile.write(f"# 当前状态：专题系列（Series）功能已完整上线（后台管理、前端展示、首页动态推荐、SEO+OG支持）\n\n")
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
