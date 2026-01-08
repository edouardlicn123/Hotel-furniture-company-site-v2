# app/routes/admin/__init__.py

from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 导入子模块（顺序重要，确保路由注册）
from .main import main_bp
from .site_info import site_info_bp
from .product import product_bp
from .feature import feature_bp
from .password import password_bp

# 注册子蓝图
admin_bp.register_blueprint(main_bp)
admin_bp.register_blueprint(site_info_bp)
admin_bp.register_blueprint(product_bp)
admin_bp.register_blueprint(feature_bp)
admin_bp.register_blueprint(password_bp)
