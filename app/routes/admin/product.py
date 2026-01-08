# app/routes/admin/product.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.models import Product, Category
from app import db
import os
import random
import string

product_bp = Blueprint('product', __name__, url_prefix='/products')

def generate_product_code():
    while True:
        digits = ''.join(random.choices(string.digits, k=9))
        code = f"pc{digits}"
        if not Product.query.filter_by(product_code=code).first():
            return code

@product_bp.route('/')
@product_bp.route('/page/<int:page>')
@login_required
def product_list(page=1):
    pagination = Product.query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    products = pagination.items
    return render_template('admin/product_list.html', products=products, pagination=pagination)

@product_bp.route('/add', methods=['GET', 'POST'])
@login_required
def product_add():
    categories = Category.query.all()
    if request.method == 'POST':
        # （保持原有完整添加逻辑，这里省略以节省篇幅，可直接复制原 admin.py 中的 product_add 内容）
        # ... 原有添加逻辑 ...
        return render_template('admin/product_form.html', product=None, categories=categories)

@product_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    # （保持原有编辑逻辑）
    # ... 原有编辑逻辑 ...
    pass

@product_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def product_delete(product_id):
    # （保持原有删除逻辑）
    pass
