# app/utils/image_helper.py
import os
import requests
from flask import current_app, url_for
from urllib.parse import urljoin
from app.models import Settings

def get_image_url(subdir, filename):
    """
    获取图片URL，支持 GitHub 模式 + 本地缓存
    subdir: 'products' 或 'series'
    filename: 图片文件名（如 pc123456789_main_abc123.jpg）
    """
    if not filename:
        return url_for('static', filename='img/placeholder.jpg')

    # 获取当前设置（建议在生产环境优化为全局缓存）
    settings = Settings.query.first()
    if not settings or not settings.github_image_enabled:
        # 未开启 → 直接用原本地路径
        return url_for('static', filename=f'uploads/{subdir}/{filename}')

    # 开启 GitHub 模式 → 优先检查 static2 缓存
    cache_dir = os.path.join(current_app.root_path, 'static2', 'uploads', subdir)
    cache_path = os.path.join(cache_dir, filename)

    if os.path.exists(cache_path):
        return url_for('static', filename=f'static2/uploads/{subdir}/{filename}')

    # 缓存不存在 → 从 GitHub 下载
    remote_url = urljoin(settings.github_base_url, f'{subdir}/{filename}')
    try:
        resp = requests.get(remote_url, timeout=6)
        resp.raise_for_status()
        
        # 简单检查是否为图片
        content_type = resp.headers.get('content-type', '')
        if 'image/' not in content_type:
            raise ValueError("Downloaded content is not an image")

        # 保存到缓存
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(resp.content)
        
        current_app.logger.info(f"GitHub image cached: {filename} from {remote_url}")
        return url_for('static', filename=f'static2/uploads/{subdir}/{filename}')

    except Exception as e:
        current_app.logger.warning(f"Failed to cache GitHub image {filename}: {str(e)}")
        # 下载失败 → fallback 到原本地路径（如果存在）
        original_path = os.path.join(current_app.root_path, 'static', 'uploads', subdir, filename)
        if os.path.exists(original_path):
            return url_for('static', filename=f'uploads/{subdir}/{filename}')
        else:
            return url_for('static', filename='img/placeholder.jpg')
