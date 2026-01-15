# app/services/image_service.py
# 统一图片处理服务 - 生产级优化版（2026-01-15 更新）
# 主要改进：
# - 支持可选图片压缩（Pillow）
# - 添加文件大小限制（单文件 & 总大小）
# - 更详细的返回信息（成功/失败列表）
# - 统一日志记录
# - 预留 GitHub 远程 URL 获取接口
# - 支持批量操作的统计返回

import os
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image  # 需要 pip install Pillow

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_SINGLE_SIZE = 8 * 1024 * 1024      # 单文件最大 8MB
MAX_TOTAL_SIZE = 30 * 1024 * 1024      # 批量上传总大小限制 30MB
DEFAULT_MAX_COUNT = 10                 # 默认最大上传数量
COMPRESS_QUALITY = 85                  # 压缩质量（JPEG/WebP）
COMPRESS_MAX_SIZE = (1600, 1600)       # 压缩后最大尺寸（宽x高）

class ImageService:
    @staticmethod
    def get_upload_folder(subdir: str = 'products') -> Path:
        """获取并确保上传目录存在"""
        folder = Path(current_app.root_path) / 'static' / 'uploads' / subdir
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @staticmethod
    def allowed_file(filename: str) -> bool:
        """检查文件扩展名是否允许"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def generate_secure_filename(original: str, prefix: str = '') -> str:
        """生成安全的唯一文件名"""
        ext = secure_filename(original).rsplit('.', 1)[-1].lower()
        if ext == 'jpeg':
            ext = 'jpg'  # 统一后缀
        stem = uuid.uuid4().hex
        return f"{prefix}{stem}.{ext}"

    @classmethod
    def save_file(
        cls,
        file,
        subdir: str = 'products',
        prefix: str = '',
        compress: bool = True,
        max_size: Tuple[int, int] = COMPRESS_MAX_SIZE
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        保存单个文件（可选压缩）
        返回: (保存后的文件名, 错误信息 or None)
        """
        if not file or not file.filename or not cls.allowed_file(file.filename):
            return None, "Invalid file or extension not allowed"

        # 检查单文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_SINGLE_SIZE:
            return None, f"File too large (max {MAX_SINGLE_SIZE//1024//1024}MB)"

        filename = cls.generate_secure_filename(file.filename, prefix)
        full_path = cls.get_upload_folder(subdir) / filename

        try:
            file.save(full_path)

            # 可选压缩
            if compress and full_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}:
                try:
                    img = Image.open(full_path)
                    img.thumbnail(max_size)
                    if full_path.suffix.lower() in {'.jpg', '.jpeg'}:
                        img.save(full_path, 'JPEG', quality=COMPRESS_QUALITY, optimize=True)
                    elif full_path.suffix.lower() == '.png':
                        img.save(full_path, 'PNG', optimize=True)
                    elif full_path.suffix.lower() == '.webp':
                        img.save(full_path, 'WEBP', quality=COMPRESS_QUALITY)
                    logger.info(f"图片压缩成功: {filename}")
                except Exception as e:
                    logger.warning(f"图片压缩失败（继续使用原图）: {filename} - {e}")

            logger.info(f"文件上传成功: {filename} -> {subdir}")
            return filename, None

        except Exception as e:
            logger.error(f"保存文件失败 {filename}: {e}")
            if full_path.exists():
                try:
                    full_path.unlink()
                except:
                    pass
            return None, str(e)

    @classmethod
    def save_multiple(
        cls,
        files,
        subdir: str = 'products',
        prefix: str = '',
        max_count: int = DEFAULT_MAX_COUNT,
        compress: bool = True
    ) -> Dict:
        """
        保存多个文件
        返回字典示例:
        {
            'saved': ['file1.jpg', 'file2.webp'],
            'failed': [{'filename': 'xxx.png', 'reason': 'too large'}],
            'total_saved': 2,
            'total_failed': 1
        }
        """
        saved = []
        failed = []
        total_size = 0

        for file in files:
            if len(saved) >= max_count:
                failed.append({'filename': file.filename, 'reason': 'Reached max count limit'})
                continue

            if not file or not file.filename:
                continue

            # 粗略预估大小
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            if total_size + file_size > MAX_TOTAL_SIZE:
                failed.append({'filename': file.filename, 'reason': 'Total size limit exceeded'})
                continue

            name, error = cls.save_file(file, subdir, prefix, compress=compress)
            if name:
                saved.append(name)
                total_size += file_size  # 使用原始大小估算
            else:
                failed.append({'filename': file.filename or 'unknown', 'reason': error or 'Unknown error'})

        return {
            'saved': saved,
            'failed': failed,
            'total_saved': len(saved),
            'total_failed': len(failed)
        }

    @staticmethod
    def delete_file(filename: str, subdir: str = 'products') -> Tuple[bool, Optional[str]]:
        """安全删除单个文件"""
        if not filename:
            return False, "No filename provided"

        path = ImageService.get_upload_folder(subdir) / filename.strip()
        if not path.exists():
            logger.info(f"文件不存在，无需删除: {filename}")
            return True, None

        try:
            path.unlink()
            logger.info(f"文件删除成功: {filename}")
            return True, None
        except OSError as e:
            logger.warning(f"删除文件失败 {filename}: {e}")
            return False, str(e)

    @staticmethod
    def delete_multiple(filenames_str: Optional[str], subdir: str = 'products') -> Dict:
        """批量删除逗号分隔的文件名，返回统计"""
        if not filenames_str:
            return {'deleted': 0, 'failed': 0, 'details': []}

        filenames = [f.strip() for f in filenames_str.split(',') if f.strip()]
        deleted_count = 0
        failed = []

        for fn in filenames:
            success, error = ImageService.delete_file(fn, subdir)
            if success:
                deleted_count += 1
            else:
                failed.append({'filename': fn, 'reason': error or 'Unknown'})

        return {
            'deleted': deleted_count,
            'failed': len(failed),
            'details': failed
        }

    @staticmethod
    def get_image_url(filename: str, subdir: str = 'products') -> str:
        """
        获取图片完整 URL（本地或未来 GitHub 模式）
        当前返回本地路径，后续可无缝切换到 GitHub 缓存模式
        """
        if not filename:
            return current_app.config.get('PLACEHOLDER_URL', '/static/img/placeholder.jpg')

        # 当前：本地路径
        return f"/static/uploads/{subdir}/{filename.lstrip('/')}"

        # 未来扩展示例（GitHub 模式）：
        # settings = Settings.query.first()
        # if settings and settings.github_image_enabled:
        #     return get_remote_image_url(filename, subdir)  # 参考 image_helper.py
