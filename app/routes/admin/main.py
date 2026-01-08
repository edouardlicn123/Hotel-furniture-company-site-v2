# app/routes/admin/main.py

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, logout_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('admin/index.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 这里仅保留路由，实际登录逻辑建议移到独立 auth 模块
    # 当前项目已有完整 login 逻辑，但为拆分清晰，建议后续单独处理
    # 临时保留跳转（实际项目请保留原 login 逻辑到此处或 auth）
    return redirect(url_for('admin.index'))  # 占位

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))  # 前端首页
