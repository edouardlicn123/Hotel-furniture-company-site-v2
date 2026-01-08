# app/routes/admin/product.py
# 后台产品管理蓝图 - 完整优化版（自动生成产品编号 + 安全图片上传 + 多图追加）

import os
import uuid
import random
import string
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.models import Product, Category
from app import db
from werkzeug.utils import secure_filename

product_bp = Blueprint('product', __name__, url_prefix='/products')

# 支持的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_product_code():
    """生成唯一的产品编号：pc + 9位随机数字"""
    while True:
        code = 'pc' + ''.join(random.choices(string.digits, k=9))
        if not Product.query.filter_by(product_code=code).first():
            return code

def get_upload_folder():
    """获取并确保上传目录存在"""
    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
    os.makedirs(folder, exist_ok=True)
    return folder

def save_uploaded_file(file, prefix=''):
    """
    安全保存上传文件，返回相对路径文件名
    使用 UUID 重命名，避免冲突和安全风险
    """
    if file and file.filename and allowed_file(file.filename):
        ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
        filename = f"{prefix}{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(get_upload_folder(), filename)
        file.save(filepath)
        return filename
    return None

def delete_file(filename):
    """安全删除静态文件"""
    if not filename:
        return
    filepath = os.path.join(get_upload_folder(), filename.strip())
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError:
            current_app.logger.warning(f"无法删除文件: {filepath}")

@product_bp.route('/')
@product_bp.route('/page/<int:page>')
@login_required
def product_list(page=1):
    pagination = Product.query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('admin/product_list.html',
                           products=pagination.items,
                           pagination=pagination)

@product_bp.route('/add', methods=['GET', 'POST'])
@login_required
def product_add():
    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('产品名称不能为空！', 'danger')
            return render_template('admin/product_form.html', product=None, categories=categories)

        # 产品编号：优先使用用户输入，若为空则自动生成
        product_code = request.form.get('product_code', '').strip()
        if not product_code:
            product_code = generate_product_code()
        else:
            if Product.query.filter_by(product_code=product_code).first():
                flash(f'产品编号 {product_code} 已存在，请修改或留空自动生成！', 'danger')
                return render_template('admin/product_form.html', product=None, categories=categories)

        # 其他字段
        description = request.form.get('description') or None
        category_id = request.form.get('category_id') or None
        if category_id == '':
            category_id = None

        # 规格与材质
        def get_int(value):
            try:
                return int(value) if value.strip() else None
            except (ValueError, AttributeError):
                return None

        length = get_int(request.form.get('length'))
        width = get_int(request.form.get('width'))
        height = get_int(request.form.get('height'))
        seat_height = get_int(request.form.get('seat_height'))

        base_material = request.form.get('base_material') or None
        surface_material = request.form.get('surface_material') or None
        featured_series = request.form.get('featured_series') or None
        applicable_space = request.form.get('applicable_space') or None

        # 处理主图
        image_filename = None
        main_image_file = request.files.get('image')
        if main_image_file and main_image_file.filename:
            image_filename = save_uploaded_file(main_image_file, prefix=f"{product_code}_main_")

        # 处理多图（支持多个文件）
        photos = []
        extra_files = request.files.getlist('photos')
        for file in extra_files:
            if file and file.filename:
                photo_name = save_uploaded_file(file, prefix=f"{product_code}_")
                if photo_name:
                    photos.append(photo_name)

        photos_str = ','.join(photos) if photos else None

        # 创建产品
        product = Product(
            product_code=product_code,
            name=name,
            description=description,
            image=image_filename,
            photos=photos_str,
            length=length,
            width=width,
            height=height,
            seat_height=seat_height,
            base_material=base_material,
            surface_material=surface_material,
            featured_series=featured_series,
            applicable_space=applicable_space,
            category_id=category_id
        )

        db.session.add(product)
        try:
            db.session.commit()
            flash(f'产品 "{name}" 添加成功！编号：{product_code}', 'success')
            return redirect(url_for('admin.product.product_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{str(e)}', 'danger')

    return render_template('admin/product_form.html', product=None, categories=categories)

@product_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('产品名称不能为空！', 'danger')
            return render_template('admin/product_form.html', product=product, categories=categories)

        product.name = name
        product.description = request.form.get('description') or None

        category_id = request.form.get('category_id') or None
        product.category_id = category_id if category_id != '' else None

        # 更新规格
        def get_int(value):
            try:
                return int(value) if value.strip() else None
            except (ValueError, AttributeError):
                return None

        product.length = get_int(request.form.get('length'))
        product.width = get_int(request.form.get('width'))
        product.height = get_int(request.form.get('height'))
        product.seat_height = get_int(request.form.get('seat_height'))

        product.base_material = request.form.get('base_material') or None
        product.surface_material = request.form.get('surface_material') or None
        product.featured_series = request.form.get('featured_series') or None
        product.applicable_space = request.form.get('applicable_space') or None

        # 替换主图
        main_image_file = request.files.get('image')
        if main_image_file and main_image_file.filename:
            new_image = save_uploaded_file(main_image_file, prefix=f"{product.product_code}_main_")
            if new_image:
                delete_file(product.image)  # 删除旧主图
                product.image = new_image

        # 追加多图（不替换原有）
        extra_files = request.files.getlist('photos')
        new_photos = []
        for file in extra_files:
            if file and file.filename:
                photo_name = save_uploaded_file(file, prefix=f"{product.product_code}_")
                if photo_name:
                    new_photos.append(photo_name)

        if new_photos:
            existing = product.photos.split(',') if product.photos else []
            product.photos = ','.join(existing + new_photos)

        try:
            db.session.commit()
            flash(f'产品 "{name}" 更新成功！', 'success')
            return redirect(url_for('admin.product.product_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')

    return render_template('admin/product_form.html', product=product, categories=categories)

@product_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    product_code = product.product_code

    # 删除所有关联图片
    delete_file(product.image)
    if product.photos:
        for photo in product.photos.split(','):
            delete_file(photo)

    db.session.delete(product)
    try:
        db.session.commit()
        flash(f'产品 "{name}"（编号：{product_code}）已彻底删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')

    return redirect(url_for('admin.product.product_list'))
