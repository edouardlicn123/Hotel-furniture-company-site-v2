# app/__init__.py
# Flask 应用工厂函数（2026-01-14 优化版）
# 更新内容：
# - 增强安全性与日志提示
# - 自动创建 instance 目录
# - 支持 FLASK_ENV 标准环境变量（development/production/testing）
# - 蓝图注册顺序保持清晰（公共 → 产品 → 业务 → admin）
# - 代码更健壮、可维护

import os
from pathlib import Path
from flask import Flask

# 导入拆分后的模块
from app.extensions import db, migrate, login_manager, mail, init_extensions
from app.context_processors import register_context_processors
from app.error_handlers import register_error_handlers

# 蓝图导入（集中管理，便于维护）
from app.routes.main import main_bp
from app.routes.products import products_bp
from app.routes.featured import featured_bp
from app.routes.admin import admin_bp
from app.routes.series import series_bp
from app.routes.cart import cart_bp
from app.routes.contact import contact_bp


def create_app(config_name: str | None = None) -> Flask:
    """
    Flask 应用工厂函数
    
    支持环境：
    - FLASK_ENV=development / production / testing
    - 通过环境变量或 instance/config.py 覆盖配置
    """
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',
                template_folder='templates')

    # =====================================
    # 1. 确保 instance 目录存在（防止路径错误）
    # =====================================
    os.makedirs(app.instance_path, exist_ok=True)

    # =====================================
    # 2. 基础配置（优先环境变量）
    # =====================================
    # SECRET_KEY - 强烈建议生产环境通过环境变量设置
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY') or \
                               'dev-insecure-key-please-change-immediately-2026'
    
    if app.config['SECRET_KEY'] == 'dev-insecure-key-please-change-immediately-2026':
        app.logger.warning("!!! 警告：正在使用不安全的默认 SECRET_KEY !!! "
                          "请立即设置 FLASK_SECRET_KEY 环境变量（生产环境必填）")
    else:
        app.logger.info("SECRET_KEY 已安全加载")

    # 数据库配置
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{Path(app.instance_path) / 'site.db'}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 上传限制

    # 会话与安全配置
    flask_env = os.environ.get('FLASK_ENV', 'development')
    app.config['ENV'] = flask_env
    app.config['DEBUG'] = flask_env == 'development'
    app.config['TESTING'] = flask_env == 'testing'

    app.config['SESSION_COOKIE_SECURE'] = flask_env == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24 * 31  # 31 天（更实用）

    # =====================================
    # 3. 加载 instance/config.py（可选，生产环境推荐使用）
    # =====================================
    app.config.from_pyfile('config.py', silent=True)

    # =====================================
    # 4. 初始化扩展
    # =====================================
    init_extensions(app)

    # =====================================
    # 5. 注册蓝图（按功能优先级排序）
    # =====================================
    # 核心公共页面
    app.register_blueprint(main_bp)
    app.register_blueprint(contact_bp)

    # 产品与系列
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(series_bp, url_prefix='/series')
    app.register_blueprint(featured_bp, url_prefix='/featured')

    # 业务功能
    app.register_blueprint(cart_bp, url_prefix='/cart')

    # 管理后台（最后注册，避免路由冲突）
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # =====================================
    # 6. 上下文处理器 & 错误处理器
    # =====================================
    register_context_processors(app)
    register_error_handlers(app)

    # =====================================
    # 7. 用户加载器（Flask-Login）
    # =====================================
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    # =====================================
    # 8. 启动日志
    # =====================================
    db_type = app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0]
    app.logger.info(
        f"Flask 应用启动成功 | "
        f"环境: {flask_env} | "
        f"Debug: {app.debug} | "
        f"数据库: {db_type} | "
        f"Instance Path: {app.instance_path}"
    )

    return app
