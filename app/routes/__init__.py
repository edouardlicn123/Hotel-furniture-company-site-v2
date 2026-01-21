# app/routes/__init__.py

from flask import Blueprint
from .admin import admin_bp

def init_app(app):
    app.register_blueprint(admin_bp)
    # 其他蓝图...
