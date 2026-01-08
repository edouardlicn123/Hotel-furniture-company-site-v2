# app/routes/admin/password.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

password_bp = Blueprint('password', __name__, url_prefix='/change_password')

@password_bp.route('/', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not check_password_hash(current_user.password, old_password):
            flash('旧密码不正确', 'danger')
            return redirect(url_for('admin.password.change_password'))

        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'danger')
            return redirect(url_for('admin.password.change_password'))

        if len(new_password) < 6:
            flash('新密码至少需要6位字符', 'danger')
            return redirect(url_for('admin.password.change_password'))

        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('密码修改成功！请重新登录', 'success')
        return redirect(url_for('main.index'))  # 或登出

    return render_template('admin/change_password.html')
