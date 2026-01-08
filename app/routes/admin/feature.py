# app/routes/admin/feature.py

from flask import Blueprint, render_template
from flask_login import login_required

feature_bp = Blueprint('feature', __name__, url_prefix='/featured')

@feature_bp.route('/')
@login_required
def feature_list():
    return render_template('admin/feature_list.html')  # 未来开发列表页

@feature_bp.route('/add')
@login_required
def feature_add():
    return render_template('admin/feature_form.html')  # 占位

# 后续可扩展编辑、删除等
