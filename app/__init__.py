# app/__init__.py
# Flask 应用工厂 - 项目核心入口（更新版：添加全局时间戳上下文处理器，修复防缓存问题）

import os
from time import time  # 用于生成当前时间戳
from flask import Flask, jsonify, render_template, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from werkzeug.exceptions import RequestEntityTooLarge

# 支持本地开发使用 .env 文件（强烈推荐）
try:
    from dotenv import load_dotenv
    load_dotenv()  # 自动加载项目根目录下的 .env 文件
except ImportError:
    pass  # 如果未安装 python-dotenv，则跳过（生产环境通常不需要）

# 全局实例
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

# 登录管理配置（英文提示，更符合国际项目）
login_manager.login_view = 'admin.main.login'
login_manager.login_message = 'Please log in to access the admin panel'
login_manager.login_message_category = 'warning'

def create_app():
    app = Flask(__name__)

    app.config['TESTING'] = False
    app.testing = False

    # SECRET_KEY 从环境变量读取（安全最佳实践）
    secret_key = os.environ.get('FLASK_SECRET_KEY')
    if not secret_key:
        # 仅用于本地开发时的临时 fallback，上线前必须设置真实密钥！
        secret_key = 'dev-only-insecure-key-change-me-2026'
        print("警告：未检测到 FLASK_SECRET_KEY 环境变量，使用临时不安全的开发密钥！")
        print("强烈建议：")
        print("1. 在项目根目录创建 .env 文件，添加：FLASK_SECRET_KEY=你的超长随机字符串")
        print("2. 或在系统环境变量中设置 FLASK_SECRET_KEY")
        print("生成安全密钥示例：python -c \"import secrets; print(secrets.token_urlsafe(64))\"")
        print("生产环境请务必使用至少 64 字符的强随机密钥！")

    app.config['SECRET_KEY'] = secret_key

    # 数据库配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 限制请求体最大大小（防止恶意大文件上传）
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # 加载用户模型（用于登录管理）
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 注册蓝图
    from app.routes.main import main_bp, inject_seo_data
    from app.routes.products import products_bp
    from app.routes.featured import featured_bp
    from app.routes.admin import admin_bp
    from app.routes.series import series_bp
    from app.routes.cart import cart_bp
    from app.routes.contact import contact_bp


    app.register_blueprint(contact_bp) 
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(featured_bp, url_prefix='/featured')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(series_bp)
    app.register_blueprint(cart_bp)

    # 全局上下文处理器（注入 SEO、公司信息等变量到所有模板）
    app.context_processor(inject_seo_data)

    # 新增：全局上下文处理器 - 注入当前时间戳（用于模板防缓存）
    @app.context_processor
    def inject_timestamp():
        return dict(
            current_timestamp = int(time())  # 当前 Unix 时间戳（秒级）
        )

    # 错误处理器 - 使用英文模板
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        # 可选：生产环境记录日志
        current_app.logger.error(f"500 Internal Server Error: {str(e)}")
        return render_template('errors/500.html'), 500

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(error):
        # 后台管理请求 → 返回 JSON（适合 AJAX 上传场景）
        if request.path.startswith('/admin'):
            return jsonify({
                'success': False,
                'message': 'File or request too large! Maximum allowed is 16MB. Please compress images or upload in smaller batches.'
            }), 413

        # 前端或其他请求 → 返回 HTML 友好页面
        return render_template(
            'errors/413.html',
            message='The uploaded content exceeds the maximum allowed size (16MB). Please compress your files and try again.'
        ), 413

    return app
