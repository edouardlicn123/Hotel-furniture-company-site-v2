# app/services/image_service.py
import os
import uuid
from pathlib import Path
from typing import Optional, List, Tuple
from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class ImageService:
    @staticmethod
    def get_upload_folder(subdir: str = 'products') -> Path:
        """获取并确保上传目录存在"""
        folder = Path(current_app.root_path) / 'static' / 'uploads' / subdir
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @staticmethod
    def generate_secure_filename(original: str, prefix: str = '') -> str:
        """生成安全的唯一文件名"""
        ext = secure_filename(original).rsplit('.', 1)[-1].lower()
        stem = uuid.uuid4().hex
        return f"{prefix}{stem}.{ext}"

    @classmethod
    def save_file(cls, file, subdir: str = 'products', prefix: str = '') -> Optional[str]:
        """保存单个文件，返回相对路径文件名或 None"""
        if not file or not file.filename or not allowed_file(file.filename):
            return None

        filename = cls.generate_secure_filename(file.filename, prefix)
        full_path = cls.get_upload_folder(subdir) / filename
        file.save(full_path)
        return filename

    @classmethod
    def save_multiple(cls, files, subdir: str = 'products', prefix: str = '', max_count: int = 10) -> List[str]:
        """保存多个文件，返回成功保存的文件名列表"""
        saved = []
        for file in files:
            if len(saved) >= max_count:
                break
            name = cls.save_file(file, subdir, prefix)
            if name:
                saved.append(name)
        return saved

    @staticmethod
    def delete_file(filename: str, subdir: str = 'products') -> bool:
        """安全删除文件"""
        if not filename:
            return False
        path = ImageService.get_upload_folder(subdir) / filename.strip()
        if path.exists():
            try:
                path.unlink()
                return True
            except OSError as e:
                current_app.logger.warning(f"删除文件失败 {filename}: {e}")
        return False

    @staticmethod
    def delete_multiple(filenames_str: Optional[str], subdir: str = 'products'):
        """删除逗号分隔的多个文件"""
        if not filenames_str:
            return
        for fn in filenames_str.split(','):
            ImageService.delete_file(fn.strip(), subdir)
