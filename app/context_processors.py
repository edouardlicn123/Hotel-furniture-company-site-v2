# app/context_processors.py
from time import time
from flask import current_app
from app.models import Settings


def inject_seo_data():
    """原 inject_seo_data 函数，建议保留在这里"""
    # 如果你原来的 inject_seo_data 逻辑比较复杂，可以继续放在这里
    # 或者进一步拆分到单独的 seo.py 中
    from app.routes.main import inject_seo_data as original_inject
    return original_inject()


def inject_settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings()  # 防止 None
    return dict(settings=settings)


def inject_timestamp():
    return dict(
        current_timestamp=int(time())
    )


def register_context_processors(app):
    """统一注册所有上下文处理器"""
    app.context_processor(inject_seo_data)
    app.context_processor(inject_settings)
    app.context_processor(inject_timestamp)
