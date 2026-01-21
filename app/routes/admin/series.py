# app/routes/admin/series.py
# 后台专题系列管理 - 完整 CRUD（整合 admin_utils.py 通用工具 + ImageService）
# 更新日期：2026-01-21
# 优化点：
# - 使用 admin_utils.py 作为独立工具模块（避免循环导入）
# - 顶层导入 admin_required, flash_redirect, get_paginated_query
# - 列表页使用通用分页助手
# - 图片处理使用 ImageService（本地上传，支持多图追加 + 限制5张）
# - 所有用户提示为英文，日志记录完善
# - 异常处理健壮（rollback + 详细日志）
# - 添加上传/删除日志，便于调试
# - 确保 slug 唯一检查排除自身

from flask import Blueprint, render_template, request, current_app
from flask_login import current_user
from app.models import FeatureSeries
from app import db
from app.services.image_service import ImageService
from app.admin_utils import (
    admin_required,
    flash_redirect,
    get_paginated_query
)

series_bp = Blueprint('series', __name__, url_prefix='/series')


@series_bp.route('/')
@series_bp.route('/page/<int:page>')
@admin_required
def series_list(page=1):
    """Featured Series list page - with pagination"""
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


@series_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def series_add():
    """Add new featured series"""
    if request.method == 'GET':
        return render_template('admin/series_form.html', series=None)

    try:
        name = request.form.get('name', '').strip()
        if not name:
            return flash_redirect("Series name cannot be empty", "danger", "admin.series.series_add")

        slug = request.form.get('slug', '').strip()
        if not slug:
            slug = name.lower().replace(' ', '-').replace('_', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')

        if FeatureSeries.query.filter_by(slug=slug).first():
            return flash_redirect(f"Slug '{slug}' already exists", "danger", "admin.series.series_add")

        description = request.form.get('description') or None
        applicable_space = request.form.get('applicable_space') or None
        seo_title = request.form.get('seo_title') or None
        seo_description = request.form.get('seo_description') or None
        seo_keywords = request.form.get('seo_keywords') or None

        # Handle multiple image upload (max 5) using ImageService
        extra_files = request.files.getlist('photos')
        new_photos = ImageService.save_multiple(
            files=extra_files,
            subdir='series',
            prefix=f"{slug}_",
            max_count=5
        )

        if len(new_photos) < len(extra_files):
            current_app.logger.warning(f"Some images failed to upload for series '{name}': only {len(new_photos)} succeeded")

        photos_str = ','.join(new_photos) if new_photos else None

        # Create series
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

        current_app.logger.info(f"Featured series added: {name} (slug: {slug}) by {current_user.username} | Photos: {len(new_photos)}")
        return flash_redirect(
            f"Featured series '{name}' added successfully!",
            "success",
            "admin.series.series_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to add featured series")
        return flash_redirect(f"Save failed: {str(e)}", "danger", "admin.series.series_add")


@series_bp.route('/edit/<int:series_id>', methods=['GET', 'POST'])
@admin_required
def series_edit(series_id):
    """Edit existing featured series"""
    series = FeatureSeries.query.get_or_404(series_id)

    if request.method == 'GET':
        return render_template('admin/series_form.html', series=series)

    try:
        name = request.form.get('name', '').strip()
        if not name:
            return flash_redirect("Series name cannot be empty", "danger", "admin.series.series_edit", series_id=series_id)

        # Check name uniqueness (exclude self)
        if name != series.name and FeatureSeries.query.filter_by(name=name).first():
            return flash_redirect(f"Series name '{name}' already exists", "danger", "admin.series.series_edit", series_id=series_id)

        slug = request.form.get('slug', '').strip()
        if not slug:
            slug = name.lower().replace(' ', '-').replace('_', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')

        if slug != series.slug and FeatureSeries.query.filter_by(slug=slug).first():
            return flash_redirect(f"Slug '{slug}' already exists", "danger", "admin.series.series_edit", series_id=series_id)

        series.name = name
        series.slug = slug
        series.description = request.form.get('description') or None
        series.applicable_space = request.form.get('applicable_space') or None
        series.seo_title = request.form.get('seo_title') or None
        series.seo_description = request.form.get('seo_description') or None
        series.seo_keywords = request.form.get('seo_keywords') or None

        # Append new images (max total 5)
        current_count = len(series.photos.split(',')) if series.photos else 0
        remain_slots = max(0, 5 - current_count)

        new_photos = []
        if remain_slots > 0:
            extra_files = request.files.getlist('photos')
            new_photos = ImageService.save_multiple(
                files=extra_files,
                subdir='series',
                prefix=f"{slug}_",
                max_count=remain_slots
            )
            if new_photos:
                existing = series.photos.split(',') if series.photos else []
                series.photos = ','.join(existing + new_photos)
                current_app.logger.info(f"Added {len(new_photos)} new images to series '{name}'")
        elif request.files.getlist('photos'):
            current_app.logger.info(f"Ignored additional uploads for series '{name}' (reached 5-image limit)")

        db.session.commit()

        current_app.logger.info(f"Featured series updated: {name} (slug: {slug}) by {current_user.username} | New photos added: {len(new_photos)}")
        return flash_redirect(
            f"Featured series '{name}' updated successfully!",
            "success",
            "admin.series.series_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to update featured series")
        return flash_redirect(f"Update failed: {str(e)}", "danger", "admin.series.series_edit", series_id=series_id)


@series_bp.route('/delete/<int:series_id>', methods=['POST'])
@admin_required
def series_delete(series_id):
    """Delete featured series (also cleans up all associated images)"""
    series = FeatureSeries.query.get_or_404(series_id)
    name = series.name

    try:
        # Clean up images using unified service
        deleted_count = ImageService.delete_multiple(series.photos, subdir='series')
        current_app.logger.info(f"Deleted {deleted_count} images for series '{name}'")

        db.session.delete(series)
        db.session.commit()

        current_app.logger.info(f"Featured series deleted: {name} (id: {series_id}) by {current_user.username}")
        return flash_redirect(
            f"Featured series '{name}' has been permanently deleted",
            "success",
            "admin.series.series_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to delete featured series")
        return flash_redirect(f"Delete failed: {str(e)}", "danger", "admin.series.series_list")
