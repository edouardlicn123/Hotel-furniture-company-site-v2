# app/routes/admin/feature.py
# 专题系列（Featured Series）后台管理 - 使用 admin_utils.py 通用工具
# 更新日期：2026-01-21（修复版 v2）
# 新修复内容：
# - 增加上传目录权限检查（如果不可写，直接闪现错误）
# - file.save() 添加 try-except 捕获保存失败（权限/路径问题等）
# - 成功/失败日志更详细（包含 filepath）
# - 如果上传失败，返回具体错误消息到用户（而非默默跳过）
# - 保持其他逻辑不变
# 使用提示：重启后上传，检查 Flask 终端日志（看是否有 "File save failed"）

import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, current_app
from flask_login import current_user
from app.models import FeatureSeries
from app import db
from app.admin_utils import (
    admin_required,
    flash_redirect,
    get_paginated_query,
    delete_admin_file
)

feature_bp = Blueprint('feature', __name__, url_prefix='/featured')

ALLOWED_IMG_EXT = {'png', 'jpg', 'jpeg', 'webp'}


@feature_bp.route('/')
@feature_bp.route('/page/<int:page>')
@admin_required
def feature_list(page=1):
    """专题系列列表页 - 支持分页"""
    pagination = get_paginated_query(
        FeatureSeries,
        page=page,
        per_page=12,
        order_by=FeatureSeries.created_at.desc()
    )
    return render_template(
        'admin/series_list.html',
        series_list=pagination.items,
        pagination=pagination
    )


@feature_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def feature_add():
    """新增专题系列"""
    if request.method == 'GET':
        return render_template('admin/series_form.html', series=None)

    try:
        name = request.form.get('name', '').strip()
        if not name:
            return flash_redirect("Series name cannot be empty", "danger", "admin.feature.feature_add")

        slug = request.form.get('slug', '').strip()
        if not slug:
            slug = name.lower().replace(' ', '-').replace('_', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')

        if FeatureSeries.query.filter_by(slug=slug).first():
            return flash_redirect(f"Slug '{slug}' already exists", "danger", "admin.feature.feature_add")

        description = request.form.get('description') or None
        applicable_space = request.form.get('applicable_space') or None
        seo_title = request.form.get('seo_title') or None
        seo_description = request.form.get('seo_description') or None
        seo_keywords = request.form.get('seo_keywords') or None

        # 处理多图上传（最多5张） - 强制保存到 series 目录
        photos = []
        extra_files = request.files.getlist('photos')
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'series')
        os.makedirs(upload_dir, exist_ok=True)

        # 检查目录权限
        if not os.access(upload_dir, os.W_OK):
            current_app.logger.error(f"Upload directory not writable: {upload_dir}")
            return flash_redirect("Upload directory permission denied! Please check server folder permissions.", "danger", "admin.feature.feature_add")

        for file in extra_files:
            if not file or not file.filename:
                continue

            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if ext not in ALLOWED_IMG_EXT:
                current_app.logger.warning(f"Unsupported file type: {file.filename}")
                continue

            filename = secure_filename(f"series_{slug}_{os.urandom(8).hex()}.{ext}")
            filepath = os.path.join(upload_dir, filename)

            try:
                file.save(filepath)
                photos.append(filename)
                current_app.logger.info(f"Series image uploaded successfully: {filename} to {filepath}")
            except Exception as save_e:
                current_app.logger.error(f"File save failed: {str(save_e)} for {filepath}")
                return flash_redirect(f"Image save failed: {str(save_e)} (Check server logs for details)", "danger", "admin.feature.feature_add")

        if len(photos) > 5:
            photos = photos[:5]  # 强制限制最多5张

        photos_str = ','.join(photos) if photos else None

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
        db.session.commit()

        current_app.logger.info(f"Featured series added: {name} (slug: {slug}) by {current_user.username}")
        return flash_redirect(
            f"Featured series '{name}' added successfully!",
            "success",
            "admin.feature.feature_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to add featured series")
        return flash_redirect(f"Save failed: {str(e)}", "danger", "admin.feature.feature_add")


@feature_bp.route('/edit/<int:series_id>', methods=['GET', 'POST'])
@admin_required
def feature_edit(series_id):
    """编辑专题系列"""
    series = FeatureSeries.query.get_or_404(series_id)

    if request.method == 'GET':
        return render_template('admin/series_form.html', series=series)

    try:
        name = request.form.get('name', '').strip()
        if not name:
            return flash_redirect("Series name cannot be empty", "danger", "admin.feature.feature_edit", series_id=series_id)

        if name != series.name and FeatureSeries.query.filter_by(name=name).first():
            return flash_redirect(f"Series name '{name}' already exists", "danger", "admin.feature.feature_edit", series_id=series_id)

        slug = request.form.get('slug', '').strip()
        if not slug:
            slug = name.lower().replace(' ', '-').replace('_', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')

        if slug != series.slug and FeatureSeries.query.filter_by(slug=slug).first():
            return flash_redirect(f"Slug '{slug}' already exists", "danger", "admin.feature.feature_edit", series_id=series_id)

        series.name = name
        series.slug = slug
        series.description = request.form.get('description') or None
        series.applicable_space = request.form.get('applicable_space') or None
        series.seo_title = request.form.get('seo_title') or None
        series.seo_description = request.form.get('seo_description') or None
        series.seo_keywords = request.form.get('seo_keywords') or None

        # 追加新图片（最多总共5张） - 强制保存到 series 目录
        current_photos = series.photos.split(',') if series.photos else []
        remain_slots = max(0, 5 - len(current_photos))

        if remain_slots > 0:
            extra_files = request.files.getlist('photos')
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'series')
            os.makedirs(upload_dir, exist_ok=True)

            # 检查目录权限
            if not os.access(upload_dir, os.W_OK):
                current_app.logger.error(f"Upload directory not writable: {upload_dir}")
                return flash_redirect("Upload directory permission denied! Please check server folder permissions.", "danger", "admin.feature.feature_edit", series_id=series_id)

            for file in extra_files[:remain_slots]:
                if not file or not file.filename:
                    continue

                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if ext not in ALLOWED_IMG_EXT:
                    current_app.logger.warning(f"Unsupported file type: {file.filename}")
                    continue

                filename = secure_filename(f"series_{slug}_{os.urandom(8).hex()}.{ext}")
                filepath = os.path.join(upload_dir, filename)

                try:
                    file.save(filepath)
                    current_photos.append(filename)
                    current_app.logger.info(f"Series image uploaded (edit) successfully: {filename} to {filepath}")
                except Exception as save_e:
                    current_app.logger.error(f"File save failed: {str(save_e)} for {filepath}")
                    return flash_redirect(f"Image save failed: {str(save_e)} (Check server logs for details)", "danger", "admin.feature.feature_edit", series_id=series_id)

        series.photos = ','.join(current_photos) if current_photos else None

        db.session.commit()

        current_app.logger.info(f"Featured series updated: {name} (slug: {slug}) by {current_user.username}")
        return flash_redirect(
            f"Featured series '{name}' updated successfully!",
            "success",
            "admin.feature.feature_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to update featured series")
        return flash_redirect(f"Update failed: {str(e)}", "danger", "admin.feature.feature_edit", series_id=series_id)


@feature_bp.route('/delete/<int:series_id>', methods=['POST'])
@admin_required
def feature_delete(series_id):
    """删除专题系列（同时清理图片）"""
    series = FeatureSeries.query.get_or_404(series_id)
    name = series.name

    try:
        # 清理所有关联图片（指定 series 目录）
        if series.photos:
            for photo in series.photos.split(','):
                delete_admin_file(photo.strip(), subdir='series')

        db.session.delete(series)
        db.session.commit()

        current_app.logger.info(f"Featured series deleted: {name} (id: {series_id}) by {current_user.username}")
        return flash_redirect(
            f"Featured series '{name}' has been permanently deleted",
            "success",
            "admin.feature.feature_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to delete featured series")
        return flash_redirect(f"Delete failed: {str(e)}", "danger", "admin.feature.feature_list")
