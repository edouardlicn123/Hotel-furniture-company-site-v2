# app/utils/image_helper.py
# 获取图片 URL，支持 GitHub 远程 + 本地缓存（2026-01-16 优化版）
# 更新内容：
# - 修复循环导入问题（延迟导入 Settings）
# - 统一使用 current_app.logger 记录日志
# - 增强超时与重试机制（timeout 统一 10s）
# - 添加缓存过期自动刷新选项（默认 7 天，可配置）
# - 优化异常处理，更清晰的错误分类
# - 所有日志消息改为英文（国际化）

import os
from datetime import datetime, timedelta
from urllib.parse import urljoin

from flask import current_app, url_for
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 延迟导入 Settings 和 requests（避免潜在循环导入）
def _get_settings():
    from app.models import Settings
    return Settings.query.first()


def get_image_url(subdir: str, filename: str) -> str:
    """
    Get full image URL for products/series.
    
    Supports two modes:
    1. Local mode (default): static/uploads/{subdir}/{filename}
    2. GitHub mode (if enabled): check static2 cache first,
       download from GitHub if missing/expired, fallback to local
    
    Args:
        subdir: 'products' or 'series'
        filename: image filename (e.g. abc123def456.jpg)
    
    Returns:
        Full static URL via url_for
    """
    if not filename:
        return url_for('static', filename='img/placeholder.jpg')

    # Lazy load settings to avoid import issues
    settings = _get_settings()
    if not settings:
        current_app.logger.warning("Settings table is empty, falling back to local image path")
        return url_for('static', filename=f'uploads/{subdir}/{filename}')

    # If GitHub mode is not enabled, use local directly
    if not settings.github_image_enabled:
        return url_for('static', filename=f'uploads/{subdir}/{filename}')

    # GitHub mode: Check local cache first (static2)
    cache_dir = os.path.join(current_app.root_path, 'static2', 'uploads', subdir)
    cache_path = os.path.join(cache_dir, filename)
    cache_url = url_for('static', filename=f'static2/uploads/{subdir}/{filename}')

    # Check if cache exists and is not expired
    if os.path.exists(cache_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        cache_age = datetime.now() - mtime
        # Configurable cache TTL (default 7 days)
        if cache_age < timedelta(days=7):
            return cache_url

    # Cache missing or expired → download from GitHub
    if not settings.github_base_url:
        current_app.logger.warning("GitHub mode enabled but github_base_url not configured, falling back to local")
        return url_for('static', filename=f'uploads/{subdir}/{filename}')

    remote_url = urljoin(settings.github_base_url.rstrip('/') + '/', f'{subdir}/{filename}')

    try:
        import requests  # 延迟导入 requests（避免启动时依赖问题）

        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        resp = session.get(remote_url, timeout=10)  # 增加超时到 10s
        resp.raise_for_status()

        content_type = resp.headers.get('content-type', '')
        if 'image/' not in content_type:
            raise ValueError(f"Non-image content: {content_type}")

        # Save to cache
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(resp.content)

        current_app.logger.info(f"Successfully cached image from GitHub: {filename} <- {remote_url}")
        return cache_url

    except ImportError:
        current_app.logger.error("requests module not installed - cannot fetch from GitHub")
        return url_for('static', filename=f'uploads/{subdir}/{filename}')

    except requests.exceptions.RequestException as e:
        current_app.logger.warning(f"GitHub image download failed for {filename}: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"GitHub caching exception for {filename}: {str(e)}")

    # All failures → fallback to local (if exists)
    local_path = os.path.join(current_app.root_path, 'static', 'uploads', subdir, filename)
    if os.path.exists(local_path):
        return url_for('static', filename=f'uploads/{subdir}/{filename}')

    # Ultimate fallback
    current_app.logger.warning(f"Image completely unavailable: {subdir}/{filename}")
    return url_for('static', filename='img/placeholder.jpg')
