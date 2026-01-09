# app/routes/admin/main.py - 完整后台管理核心路由（含登录/登出/首页）

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.security import check_password_hash
from app.models import User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
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
    # 如果用户已经登录，直接跳转到后台首页（防止重复登录）
    if current_user.is_authenticated:
        return redirect(url_for('admin.main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form  # 可选：记住我

        # 查询用户
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            print("正在登录用户:", user.username)  # 调试输出
            login_user(user, remember=remember)
            print("登录完成，session:", session)  # 调试输出：检查 session 是否有 '_user_id'
            flash('登录成功！欢迎回来。', 'success')

            # 支持 next 参数：从哪里来回哪里去
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.main.index'))
        else:
            flash('用户名或密码错误，请重试。', 'danger')

    # GET 或验证失败：渲染登录页面
    return render_template('admin/login.html')

@main_bp.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    flash('已安全退出登录', 'info')
    return redirect(url_for('main.index'))  # 回到前端首页
