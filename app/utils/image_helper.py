# app/utils/image_helper.py
# 获取图片 URL，支持 GitHub 远程 + 本地缓存（2026-01-14 优化版）

import os
import requests
from flask import current_app, url_for
from urllib.parse import urljoin
from datetime import datetime, timedelta
from app.models import Settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_image_url(subdir: str, filename: str) -> str:
    """
    获取产品/系列图片的完整 URL。
    
    支持两种模式：
    1. 本地模式（默认）：直接使用 static/uploads/{subdir}/{filename}
    2. GitHub 模式（后台开启 github_image_enabled）：优先从 static2 缓存读取，
       无缓存则从 GitHub 下载并缓存到 static2，失败则 fallback 到本地
    
    Args:
        subdir: 'products' 或 'series'
        filename: 图片文件名（如 abc123def456.jpg）
    
    Returns:
        完整的静态文件 URL（带 url_for）
    """
    if not filename:
        return url_for('static', filename='img/placeholder.jpg')

    # 获取网站设置（建议生产环境使用缓存或上下文处理器注入）
    settings = Settings.query.first()
    if not settings:
        current_app.logger.warning("Settings 表为空，使用本地图片路径")
        return url_for('static', filename=f'uploads/{subdir}/{filename}')

    # 如果未开启 GitHub 模式，直接返回本地路径
    if not settings.github_image_enabled:
        return url_for('static', filename=f'uploads/{subdir}/{filename}')

    # GitHub 模式：优先检查本地缓存 (static2)
    cache_dir = os.path.join(current_app.root_path, 'static2', 'uploads', subdir)
    cache_path = os.path.join(cache_dir, filename)
    cache_url = url_for('static', filename=f'static2/uploads/{subdir}/{filename}')

    if os.path.exists(cache_path):
        # 可选：检查缓存是否过期（例如超过 7 天重新拉取）
        mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.now() - mtime < timedelta(days=7):
            return cache_url

    # 缓存不存在或过期 → 从 GitHub 下载
    if not settings.github_base_url:
        current_app.logger.warning("GitHub 模式启用但 github_base_url 未配置，回退本地")
        return url_for('static', filename=f'uploads/{subdir}/{filename}')

    remote_url = urljoin(settings.github_base_url.rstrip('/') + '/', f'{subdir}/{filename}')

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        resp = session.get(remote_url, timeout=8)
        resp.raise_for_status()

        content_type = resp.headers.get('content-type', '')
        if 'image/' not in content_type:
            raise ValueError(f"非图片内容: {content_type}")

        # 保存到缓存目录
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(resp.content)

        current_app.logger.info(f"成功从 GitHub 缓存图片: {filename} ← {remote_url}")
        return cache_url

    except requests.exceptions.RequestException as e:
        current_app.logger.warning(f"GitHub 图片下载失败 {filename}: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"GitHub 缓存处理异常 {filename}: {str(e)}")

    # 所有失败情况 → 回退到本地原始路径（如果存在）
    local_path = os.path.join(current_app.root_path, 'static', 'uploads', subdir, filename)
    if os.path.exists(local_path):
        return url_for('static', filename=f'uploads/{subdir}/{filename}')

    # 最终兜底
    current_app.logger.warning(f"图片完全不可用: {subdir}/{filename}")
    return url_for('static', filename='img/placeholder.jpg')
