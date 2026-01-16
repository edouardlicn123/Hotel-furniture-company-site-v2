# app/routes/admin/password.py
# 后台密码修改路由 - 使用 admin_utils.py 通用工具
# 更新日期：2026-01-16
# 优化点：
# - 使用 admin_utils.py 作为独立工具模块（避免循环导入）
# - 顶层导入 admin_required 和 flash_redirect（安全、无循环风险）
# - 密码强度校验（至少8位）
# - 成功后强制登出重新登录（更安全）
# - 日志记录完善（含用户名）

from flask import Blueprint, render_template, request, current_app
from flask_login import current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.admin_utils import admin_required, flash_redirect

password_bp = Blueprint('password', __name__, url_prefix='/change_password')


@password_bp.route('/', methods=['GET', 'POST'])
@admin_required
def change_password():
    """修改后台管理员密码"""
    if request.method == 'GET':
        return render_template('admin/change_password.html')

    try:
        old_password = request.form.get('old_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not old_password or not new_password or not confirm_password:
            return flash_redirect("All password fields are required", "danger", "admin.password.change_password")

        if not check_password_hash(current_user.password, old_password):
            current_app.logger.warning(f"Password change failed: incorrect old password for user {current_user.username}")
            return flash_redirect("Current password is incorrect", "danger", "admin.password.change_password")

        if new_password != confirm_password:
            return flash_redirect("New passwords do not match", "danger", "admin.password.change_password")

        if len(new_password) < 8:
            return flash_redirect("New password must be at least 8 characters", "danger", "admin.password.change_password")

        current_user.password = generate_password_hash(new_password)
        db.session.commit()

        current_app.logger.info(f"Password changed successfully for user: {current_user.username}")

        logout_user()
        return flash_redirect(
            "Password changed successfully! Please log in again with your new password.",
            "success",
            "admin.main.login"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Unexpected error during password change")
        return flash_redirect("An error occurred. Please try again later.", "danger", "admin.password.change_password")
