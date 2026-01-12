# app/__init__.py
# Flask 应用工厂 - 项目核心入口

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail  # 新增：邮件发送支持（为 SMTP 功能准备）

# 全局实例
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()  # 全局 Mail 实例，后续在 create_app 中初始化

# 登录管理配置
login_manager.login_view = 'admin.main.login'  # 未登录跳转到登录页
login_manager.login_message = '请先登录后台管理系统'
login_manager.login_message_category = 'warning'

def create_app():
    app = Flask(__name__)

    app.config['TESTING'] = False
    app.testing = False

    # 基础配置
    app.config['SECRET_KEY'] = 'xai-super-secret-2026-random-string-abc123xyz'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)  # 初始化邮件扩展（后续动态配置会覆盖）

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

    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(featured_bp, url_prefix='/featured')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(series_bp)
    app.register_blueprint(cart_bp)

    # 全局上下文处理器（注入 SEO、公司信息等变量到所有模板）
    app.context_processor(inject_seo_data)

    return app
