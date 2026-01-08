# app/routes/admin/series.py
# 后台专题系列管理 - 完整 CRUD（高度复用产品管理逻辑）

import os
import uuid
import random
import string
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.models import FeatureSeries, Product
from app import db
from werkzeug.utils import secure_filename

series_bp = Blueprint('series', __name__, url_prefix='/series')

# 支持的图片格式（与产品一致）
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    """获取并确保系列图片上传目录存在"""
    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'series')
    os.makedirs(folder, exist_ok=True)
    return folder

def save_uploaded_file(file, prefix=''):
    """安全保存上传文件，返回相对路径文件名（UUID 重命名）"""
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

@series_bp.route('/')
@login_required
def series_list():
    page = request.args.get('page', 1, type=int)
    pagination = FeatureSeries.query.order_by(FeatureSeries.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('admin/series_list.html',
                           series_list=pagination.items,
                           pagination=pagination)

@series_bp.route('/add', methods=['GET', 'POST'])
@login_required
def series_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('系列名称不能为空！', 'danger')
            return render_template('admin/series_form.html', series=None)

        slug = request.form.get('slug', '').strip()
        if not slug:
            # 自动生成 slug（简易版：小写 + 连字符）
            slug = name.lower().replace(' ', '-').replace('_', '-')
            # 去除非字母数字字符
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        # 检查 slug 唯一性
        if FeatureSeries.query.filter_by(slug=slug).first():
            flash(f'系统名称 "{slug}" 已存在，请修改！', 'danger')
            return render_template('admin/series_form.html', series=None)

        description = request.form.get('description') or None
        applicable_space = request.form.get('applicable_space') or None
        seo_title = request.form.get('seo_title') or None
        seo_description = request.form.get('seo_description') or None
        seo_keywords = request.form.get('seo_keywords') or None

        # 处理多图上传（最多5张）
        photos = []
        extra_files = request.files.getlist('photos')
        for file in extra_files:
            if file and file.filename:
                if len(photos) >= 5:
                    flash('最多只能上传5张系列图片！', 'warning')
                    break
                photo_name = save_uploaded_file(file, prefix=f"{slug}_")
                if photo_name:
                    photos.append(photo_name)

        photos_str = ','.join(photos) if photos else None

        # 创建系列
        series = FeatureSeries(
            name=name,
            slug=slug,
            description=description,
            applicable_space=applicable_space,
            photos=photos_str,
            seo_title=seo_title,
            seo_description=seo_description,
            seo_keywords=seo_keywords
        )

        db.session.add(series)
        try:
            db.session.commit()
            flash(f'专题系列 "{name}" 添加成功！', 'success')
            return redirect(url_for('admin.series.series_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{str(e)}', 'danger')

    return render_template('admin/series_form.html', series=None)

@series_bp.route('/edit/<int:series_id>', methods=['GET', 'POST'])
@login_required
def series_edit(series_id):
    series = FeatureSeries.query.get_or_404(series_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('系列名称不能为空！', 'danger')
            return render_template('admin/series_form.html', series=series)

        # 检查名称唯一性（排除自身）
        if name != series.name and FeatureSeries.query.filter_by(name=name).first():
            flash(f'系列名称 "{name}" 已存在！', 'danger')
            return render_template('admin/series_form.html', series=series)

        slug = request.form.get('slug', '').strip()
        if not slug:
            slug = name.lower().replace(' ', '-').replace('_', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        # 检查 slug 唯一性（排除自身）
        if slug != series.slug and FeatureSeries.query.filter_by(slug=slug).first():
            flash(f'系统名称 "{slug}" 已存在！', 'danger')
            return render_template('admin/series_form.html', series=series)

        series.name = name
        series.slug = slug
        series.description = request.form.get('description') or None
        series.applicable_space = request.form.get('applicable_space') or None
        series.seo_title = request.form.get('seo_title') or None
        series.seo_description = request.form.get('seo_description') or None
        series.seo_keywords = request.form.get('seo_keywords') or None

        # 追加新图片
        extra_files = request.files.getlist('photos')
        new_photos = []
        for file in extra_files:
            if file and file.filename:
                if len(new_photos) + (len(series.photos.split(',')) if series.photos else 0) >= 5:
                    flash('最多只能上传5张系列图片！', 'warning')
                    break
                photo_name = save_uploaded_file(file, prefix=f"{slug}_")
                if photo_name:
                    new_photos.append(photo_name)

        if new_photos:
            existing = series.photos.split(',') if series.photos else []
            series.photos = ','.join(existing + new_photos)

        try:
            db.session.commit()
            flash(f'专题系列 "{name}" 更新成功！', 'success')
            return redirect(url_for('admin.series.series_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')

    return render_template('admin/series_form.html', series=series)

@series_bp.route('/delete/<int:series_id>', methods=['POST'])
@login_required
def series_delete(series_id):
    series = FeatureSeries.query.get_or_404(series_id)
    name = series.name

    # 删除所有关联图片
    if series.photos:
        for photo in series.photos.split(','):
            delete_file(photo)

    db.session.delete(series)
    try:
        db.session.commit()
        flash(f'专题系列 "{name}" 已彻底删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')

    return redirect(url_for('admin.series.series_list'))
