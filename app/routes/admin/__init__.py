# app/routes/admin/__init__.py
"""
Admin 后台主蓝图入口
负责注册所有子蓝图，确保路由顺序和命名空间清晰
所有子蓝图应统一使用 url_prefix='/admin/子功能'
"""

from flask import Blueprint

# 创建主蓝图（所有后台路由的前缀统一为 /admin）
admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin',
    template_folder='templates/admin',      # 可选：统一指定后台模板目录
    static_folder='static/admin'            # 可选：如果未来有后台专用静态资源
)

# 导入所有子蓝图（顺序重要：先公共 → 再业务 → 最后敏感操作）
# 建议保持这个顺序，便于调试和阅读
from .main import main_bp           # 登录、首页、登出
from .password import password_bp   # 密码修改（敏感，靠后）
from .site_info import site_info_bp # 网站设置
from .smtp import smtp_bp           # 邮件配置（敏感）
from .product import product_bp     # 产品管理
from .series import series_bp       # 系列管理
from .feature import feature_bp     # 精选/专题系列（与 series 类似，放在业务类）

# 注册所有子蓝图
# 注意：注册顺序也会影响路由匹配优先级（先注册的优先匹配）
admin_bp.register_blueprint(main_bp)
admin_bp.register_blueprint(password_bp)
admin_bp.register_blueprint(site_info_bp)
admin_bp.register_blueprint(smtp_bp)
admin_bp.register_blueprint(product_bp)
admin_bp.register_blueprint(series_bp)
admin_bp.register_blueprint(feature_bp)

# 可选：注册一个全局错误处理器或上下文处理器（如果不希望分散到 __init__.py）
# @admin_bp.context_processor
# def admin_context():
#     return dict(
#         admin_title="酒店家具后台管理",
#         current_user=current_user
#     )

# 可选：全局 before_request 钩子（例如记录后台访问日志）
# @admin_bp.before_request
# def before_admin_request():
#     if current_user.is_authenticated:
#         current_app.logger.info(f"Admin access: {current_user.username} -> {request.path}")
