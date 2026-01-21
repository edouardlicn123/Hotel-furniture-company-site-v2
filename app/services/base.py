# app/admin/base.py
from flask import Blueprint, flash, redirect, url_for, request
from flask_login import login_required
from functools import wraps
from typing import Callable

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f: Callable):
    """增强版登录检查，可自定义提示"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # 可在此处添加额外的管理员权限检查
        return f(*args, **kwargs)
    return decorated_function

class AdminBaseView:
    """未来可做更复杂的基类视图，目前可作为标记类"""
    pass

# 通用成功/失败消息模板
def flash_success(msg: str, category='success'):
    flash(msg, category)

def flash_error(msg: str, category='danger'):
    flash(msg, category)
