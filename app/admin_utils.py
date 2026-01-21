# app/admin_utils.py
# 后台管理通用工具模块（独立于 routes/admin 包，避免循环导入）
# 包含：权限装饰器、统一响应/跳转、图片上传/删除、分页助手等
# 使用方式：所有 admin 子蓝图都从这里导入，例如：
# from app.admin_utils import admin_required, flash_redirect

from functools import wraps
import os
from flask import (
    jsonify, flash, redirect, url_for, request, current_app
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from app import db

# ========================
# 权限校验装饰器
# ========================
def admin_required(f):
    """强化版登录校验 + 未来角色扩展点"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access the admin panel', 'warning')
            return redirect(url_for('admin.main.login', next=request.url))
        
        # 未来可加角色判断，例如：
        # if not current_user.is_admin:
        #     flash('权限不足', 'danger')
        #     return redirect(url_for('admin.main.index'))
            
        return f(*args, **kwargs)
    return decorated_function


# ========================
# 统一响应与跳转工具
# ========================
def flash_redirect(message, category='info', endpoint='admin.main.index', **kwargs):
    """
    统一闪现消息 + 重定向
    用法示例：
    return flash_redirect("操作成功", "success", "admin.product.product_list")
    """
    flash(message, category)
    return redirect(url_for(endpoint, **kwargs))


def admin_json_response(success=True, message="", data=None, status_code=200):
    """统一后台 AJAX/JSON 返回格式"""
    response = {
        'success': success,
        'message': message,
        'data': data or {}
    }
    return jsonify(response), status_code


# ========================
# 图片上传/删除工具
# ========================
ALLOWED_IMG_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}

def get_upload_path(subdir='products'):
    """获取并确保上传目录存在"""
    base = os.path.join(current_app.root_path, 'static', 'uploads', subdir)
    os.makedirs(base, exist_ok=True)
    return base


def save_admin_upload(file, prefix='', allowed_extensions=None):
    """
    后台专用文件上传方法（带基本校验）
    返回: (成功?, 新文件名 or None, 错误消息)
    """
    if not file or not file.filename:
        return False, None, "No file selected"
    
    ext = ''
    if '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
    else:
        return False, None, "File has no extension"
    
    if allowed_extensions and ext not in allowed_extensions:
        return False, None, f"Unsupported file type (allowed: {', '.join(allowed_extensions)})"
    
    filename = secure_filename(f"{prefix}{os.urandom(8).hex()}.{ext}")
    filepath = os.path.join(get_upload_path(), filename)
    file.save(filepath)
    return True, filename, None


def delete_admin_file(filename, subdir='products'):
    """安全删除上传的文件"""
    if not filename:
        return True, "No file to delete"
    
    filepath = os.path.join(get_upload_path(subdir), filename.strip())
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True, "File deleted successfully"
        except OSError as e:
            current_app.logger.warning(f"Failed to delete file {filename}: {e}")
            return False, f"Delete failed: {str(e)}"
    return True, "File does not exist"


# ========================
# 分页查询助手
# ========================
def get_paginated_query(model, page=1, per_page=12, order_by=None):
    """
    通用分页查询助手
    用法示例：
    pagination = get_paginated_query(Product, page=page, per_page=12, order_by=Product.created_at.desc())
    """
    query = model.query
    if order_by is not None:
        query = query.order_by(order_by)
    return query.paginate(page=page, per_page=per_page, error_out=False)


# ========================
# 其他通用工具（可继续扩展）
# ========================
def handle_form_errors(form):
    """统一处理 WTForms 错误（如果未来引入 WTForms）"""
    if not form.errors:
        return None
    error_msgs = []
    for field, errors in form.errors.items():
        error_msgs.append(f"{field}: {', '.join(errors)}")
    return "; ".join(error_msgs)


def get_admin_base_context():
    """后台常用上下文注入（可选）"""
    return {
        'settings': Settings.query.first() or Settings(),
        'current_year': datetime.now().year,
        'app_version': '2.0.x'  # 可从配置读取
    }
