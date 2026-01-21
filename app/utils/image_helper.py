# app/utils/image_helper.py
# 获取图片 URL - 2026-01-21 最终版：彻底移除 GitHub 模式，只使用本地图片

import os
from flask import current_app, url_for


def get_image_url(subdir: str, filename: str) -> str:
    """
    直接返回本地图片的完整 URL。
    
    Args:
        subdir: 'products' 或 'series'
        filename: 图片文件名（例如：abc123def456.jpg）
    
    Returns:
        完整的静态文件 URL，例如：/static/uploads/products/abc123def456.jpg
    """
    if not filename:
        return url_for('static', filename='img/placeholder.jpg')

    # 强制使用本地路径
    return url_for('static', filename=f'uploads/{subdir}/{filename}')
