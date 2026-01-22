# app/routes/admin/product.py
# 后台产品管理蓝图 - 完整优化版（整合 admin_utils.py 通用工具）
# 更新日期：2026-01-21
# 优化点：
# - 使用 admin_utils.py 作为独立工具模块（避免循环导入）
# - 顶层导入 admin_required, flash_redirect, save_admin_upload, delete_admin_file, get_paginated_query
# - 列表页使用通用分页助手
# - 图片上传统一使用 save_admin_upload
# - 所有用户提示信息已更新为中文，日志记录完善
# - 异常处理健壮（rollback + 详细日志）
# - 修复主图更换 bug：确保新上传主图正确覆盖旧值（包括旧值为 "None" 字符串的情况）
# - 添加上传日志，便于调试

from flask import Blueprint, render_template, request, current_app
from flask_login import current_user
from app.models import Product, Category
from app import db
from app.admin_utils import (
    admin_required,
    flash_redirect,
    save_admin_upload,
    delete_admin_file,
    get_paginated_query
)

product_bp = Blueprint('product', __name__, url_prefix='/products')

# 支持的图片格式（与 admin_utils.py 保持一致）
ALLOWED_IMG_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}


@product_bp.route('/')
@product_bp.route('/page/<int:page>')
@admin_required
def product_list(page=1):
    """产品列表页 - 使用通用分页"""
    pagination = get_paginated_query(
        Product,
        page=page,
        per_page=12,
        order_by=Product.created_at.desc()
    )
    return render_template(
        'admin/product_list.html',
        products=pagination.items,
        pagination=pagination
    )


@product_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def product_add():
    """新增产品"""
    categories = Category.query.all()

    if request.method == 'GET':
        return render_template('admin/product_form.html', product=None, categories=categories)

    try:
        name = request.form.get('name', '').strip()
        if not name:
            return flash_redirect("产品名称不能为空", "danger", "admin.product.product_add")

        # 产品编号：优先用户输入，否则自动生成
        product_code = request.form.get('product_code', '').strip()
        if product_code:
            if Product.query.filter_by(product_code=product_code).first():
                return flash_redirect(f"产品编号 '{product_code}' 已存在", "danger", "admin.product.product_add")
        else:
            product_code = generate_product_code()  # 保留原有生成逻辑

        # 其他字段
        description = request.form.get('description') or None
        category_id = request.form.get('category_id') or None
        if category_id == '':
            category_id = None

        # 规格（安全转换）
        def get_int(value):
            try:
                return int(value.strip()) if value and value.strip() else None
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

        # 主图上传
        image_filename = None
        main_image_file = request.files.get('image')
        if main_image_file and main_image_file.filename:
            success, filename, error = save_admin_upload(
                main_image_file,
                prefix=f"{product_code}_main_",
                allowed_extensions=ALLOWED_IMG_EXT
            )
            if success:
                image_filename = filename
                current_app.logger.info(f"新增产品主图上传成功：{filename}")
            else:
                current_app.logger.warning(f"主图上传失败：{error}")
                return flash_redirect(f"主图上传失败：{error}", "danger", "admin.product.product_add")

        # 多图上传（追加，支持多张）
        photos = []
        extra_files = request.files.getlist('photos')
        for file in extra_files:
            if file and file.filename:
                success, filename, error = save_admin_upload(
                    file,
                    prefix=f"{product_code}_",
                    allowed_extensions=ALLOWED_IMG_EXT
                )
                if success:
                    photos.append(filename)
                    current_app.logger.info(f"新增产品额外图片上传成功：{filename}")

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
        db.session.commit()

        current_app.logger.info(f"产品新增成功：{name} (编号：{product_code}) 由 {current_user.username} 操作")
        return flash_redirect(
            f"产品 '{name}' 添加成功！编号：{product_code}",
            "success",
            "admin.product.product_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("新增产品失败")
        return flash_redirect(f"保存失败：{str(e)}", "danger", "admin.product.product_add")


@product_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def product_edit(product_id):
    """编辑产品"""
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == 'GET':
        return render_template('admin/product_form.html', product=product, categories=categories)

    try:
        name = request.form.get('name', '').strip()
        if not name:
            return flash_redirect("产品名称不能为空", "danger", "admin.product.product_edit", product_id=product_id)

        product.name = name
        product.description = request.form.get('description') or None

        category_id = request.form.get('category_id') or None
        product.category_id = category_id if category_id != '' else None

        # 更新规格
        def get_int(value):
            try:
                return int(value.strip()) if value and value.strip() else None
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

        # 替换主图（关键修复：确保有新上传时强制覆盖旧值，包括旧值为 "None"）
        main_image_file = request.files.get('image')
        if main_image_file and main_image_file.filename:
            success, filename, error = save_admin_upload(
                main_image_file,
                prefix=f"{product.product_code}_main_",
                allowed_extensions=ALLOWED_IMG_EXT
            )
            if success:
                # 删除旧主图（如果存在且不是 "None"）
                if product.image and product.image.strip() and product.image.strip() != 'None':
                    delete_admin_file(product.image.strip(), subdir='products')
                    current_app.logger.info(f"删除旧主图：{product.image}")
                product.image = filename
                current_app.logger.info(f"主图已替换为：{filename}")
            else:
                current_app.logger.warning(f"主图替换失败：{error}")
                flash(f"主图上传失败：{error}", "warning")

        # 追加多图（不替换原有）
        extra_files = request.files.getlist('photos')
        new_photos = []
        for file in extra_files:
            if file and file.filename:
                success, filename, error = save_admin_upload(
                    file,
                    prefix=f"{product.product_code}_",
                    allowed_extensions=ALLOWED_IMG_EXT
                )
                if success:
                    new_photos.append(filename)
                    current_app.logger.info(f"额外图片上传成功：{filename}")

        if new_photos:
            existing = product.photos.split(',') if product.photos else []
            product.photos = ','.join(existing + new_photos)
            current_app.logger.info(f"新增 {len(new_photos)} 张额外图片")

        db.session.commit()

        current_app.logger.info(f"产品更新成功：{name} (编号：{product.product_code}) 由 {current_user.username} 操作")
        return flash_redirect(
            f"产品 '{name}' 更新成功！",
            "success",
            "admin.product.product_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("更新产品失败")
        return flash_redirect(f"更新失败：{str(e)}", "danger", "admin.product.product_edit", product_id=product_id)


@product_bp.route('/delete/<int:product_id>', methods=['POST'])
@admin_required
def product_delete(product_id):
    """删除产品（同时清理所有关联图片）"""
    product = Product.query.get_or_404(product_id)
    name = product.name
    product_code = product.product_code

    try:
        # 清理主图（跳过 "None"）
        if product.image and product.image.strip() and product.image.strip() != 'None':
            delete_admin_file(product.image.strip(), subdir='products')

        # 清理多图
        if product.photos:
            for photo in product.photos.split(','):
                photo_stripped = photo.strip()
                if photo_stripped:
                    delete_admin_file(photo_stripped, subdir='products')

        db.session.delete(product)
        db.session.commit()

        current_app.logger.info(f"产品已删除：{name} (编号：{product_code}) 由 {current_user.username} 操作")
        return flash_redirect(
            f"产品 '{name}' (编号：{product_code}) 已永久删除",
            "success",
            "admin.product.product_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("删除产品失败")
        return flash_redirect(f"删除失败：{str(e)}", "danger", "admin.product.product_list")


# 保留原有辅助函数（可考虑逐步迁移到 admin_utils.py）
def generate_product_code():
    """生成唯一产品编号：pc + 9位随机数字"""
    import random
    import string
    while True:
        code = 'pc' + ''.join(random.choices(string.digits, k=9))
        if not Product.query.filter_by(product_code=code).first():
            return code
