# app/routes/admin/main.py
# 后台管理核心路由（登录/首页/登出） - 使用 admin_utils.py 通用工具
# 更新日期：2026-01-16
# 优化点：
# - 使用 admin_utils.py 作为独立工具模块（避免循环导入）
# - 顶层导入 admin_required 和 flash_redirect（安全、无循环风险）
# - 移除调试 print，改用 current_app.logger
# - 增强安全性：登录失败记录警告日志
# - 支持 next 参数安全校验（防止开放重定向）
# - 所有用户提示信息已更新为中文，日志记录完善

from flask import Blueprint, render_template, request, redirect, url_for, current_app
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash
from app.models import User
from app.admin_utils import admin_required, flash_redirect

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@admin_required
def index():
    """后台管理首页"""
    return render_template('admin/index.html')


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    登录页面
    - GET: 显示登录表单
    - POST: 处理登录验证
    """
    # 已登录用户直接跳转首页（防止重复登录）
    if current_user.is_authenticated:
        return redirect(url_for('admin.main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = 'remember' in request.form

        if not username or not password:
            return flash_redirect("用户名和密码不能为空", "danger", "admin.main.login")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            current_app.logger.info(f"管理员登录成功：{username} 来自 {request.remote_addr}")

            # 支持安全的 next 参数（防止开放重定向攻击）
            next_page = request.args.get('next')
            if next_page and '//' not in next_page and next_page.startswith('/admin'):
                return redirect(next_page)
            else:
                return flash_redirect("登录成功！欢迎回来", "success", "admin.main.index")
        else:
            current_app.logger.warning(f"管理员登录失败：{username} 来自 {request.remote_addr}")
            return flash_redirect("用户名或密码错误，请重试", "danger", "admin.main.login")

    # GET 或验证失败
    return render_template('admin/login.html')


@main_bp.route('/logout')
@admin_required
def logout():
    """登出"""
    username = current_user.username
    logout_user()
    current_app.logger.info(f"管理员已安全退出：{username}")
    return flash_redirect("已安全退出登录", "info", "main.index")  # 回到前端首页
