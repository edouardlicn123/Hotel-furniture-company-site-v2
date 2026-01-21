# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

# 全局扩展实例（延迟绑定到 app）
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()


def init_extensions(app):
    """统一初始化所有扩展"""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # 登录相关配置（建议集中在这里）
    login_manager.login_view = 'admin.main.login'
    login_manager.login_message = 'Please log in to access the admin panel'
    login_manager.login_message_category = 'warning'
