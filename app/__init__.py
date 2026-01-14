# app/__init__.py （精简后版本）

import os
from flask import Flask

# 导入拆分后的模块
from app.extensions import db, migrate, login_manager, mail, init_extensions
from app.context_processors import register_context_processors
from app.error_handlers import register_error_handlers

# 导入蓝图（建议保持在这里，或后续也可以移到单独的 blueprint_registry.py）
from app.routes.main import main_bp
from app.routes.products import products_bp
from app.routes.featured import featured_bp
from app.routes.admin import admin_bp
from app.routes.series import series_bp
from app.routes.cart import cart_bp
from app.routes.contact import contact_bp


def create_app():
    app = Flask(__name__)

    # 配置
    app.config['TESTING'] = False
    app.testing = False

    # SECRET_KEY（保持原逻辑）
    secret_key = os.environ.get('FLASK_SECRET_KEY')
    if not secret_key:
        secret_key = 'dev-only-insecure-key-change-me-2026'
        print("警告：使用不安全的开发密钥！请设置 FLASK_SECRET_KEY 环境变量")
    app.config['SECRET_KEY'] = secret_key

    # 数据库 + 其他配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

    # ==================== 初始化扩展 ====================
    init_extensions(app)

    # ==================== 注册蓝图 ====================
    app.register_blueprint(contact_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(featured_bp, url_prefix='/featured')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(series_bp)
    app.register_blueprint(cart_bp)

    # ==================== 注册上下文处理器 & 错误处理器 ====================
    register_context_processors(app)
    register_error_handlers(app)

    # 加载用户模型（用于登录）
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
