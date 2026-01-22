# app/routes/admin/series.py
# 后台专题系列管理 - 完整 CRUD（整合 admin_utils.py 通用工具 + ImageService）
# 更新日期：2026-01-21
# 优化点：
# - 使用 admin_utils.py 作为独立工具模块（避免循环导入）
# - 顶层导入 admin_required, flash_redirect, get_paginated_query
# - 列表页使用通用分页助手
# - 图片处理使用 ImageService（本地上传，支持多图追加 + 限制5张）
# - 所有用户提示信息已更新为中文，日志记录完善
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


@series_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def series_add():
    """新增专题系列"""
    if request.method == 'GET':
        return render_template('admin/series_form.html', series=None)

    try:
        name = request.form.get('name', '').strip()
        if not name:
            return flash_redirect("系列名称不能为空", "danger", "admin.series.series_add")

        slug = request.form.get('slug', '').strip()
        if not slug:
            slug = name.lower().replace(' ', '-').replace('_', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')

        if FeatureSeries.query.filter_by(slug=slug).first():
            return flash_redirect(f"Slug '{slug}' 已存在", "danger", "admin.series.series_add")

        description = request.form.get('description') or None
        applicable_space = request.form.get('applicable_space') or None
        seo_title = request.form.get('seo_title') or None
        seo_description = request.form.get('seo_description') or None
        seo_keywords = request.form.get('seo_keywords') or None

        # 处理多图上传（最多5张） - 使用 ImageService
        extra_files = request.files.getlist('photos')
        new_photos = ImageService.save_multiple(
            files=extra_files,
            subdir='series',
            prefix=f"{slug}_",
            max_count=5
        )

        if len(new_photos) < len(extra_files):
            current_app.logger.warning(f"系列 '{name}' 部分图片上传失败：仅成功 {len(new_photos)} 张")

        photos_str = ','.join(new_photos) if new_photos else None

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
        db.session.commit()

        current_app.logger.info(f"专题系列新增成功：{name} (slug: {slug}) 由 {current_user.username} 操作 | 图片数量：{len(new_photos)}")
        return flash_redirect(
            f"专题系列 '{name}' 添加成功！",
            "success",
            "admin.series.series_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("新增专题系列失败")
        return flash_redirect(f"保存失败：{str(e)}", "danger", "admin.series.series_add")


@series_bp.route('/edit/<int:series_id>', methods=['GET', 'POST'])
@admin_required
def series_edit(series_id):
    """编辑专题系列"""
    series = FeatureSeries.query.get_or_404(series_id)

    if request.method == 'GET':
        return render_template('admin/series_form.html', series=series)

    try:
        name = request.form.get('name', '').strip()
        if not name:
            return flash_redirect("系列名称不能为空", "danger", "admin.series.series_edit", series_id=series_id)

        # 检查名称唯一性（排除自身）
        if name != series.name and FeatureSeries.query.filter_by(name=name).first():
            return flash_redirect(f"系列名称 '{name}' 已存在", "danger", "admin.series.series_edit", series_id=series_id)

        slug = request.form.get('slug', '').strip()
        if not slug:
            slug = name.lower().replace(' ', '-').replace('_', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')

        if slug != series.slug and FeatureSeries.query.filter_by(slug=slug).first():
            return flash_redirect(f"Slug '{slug}' 已存在", "danger", "admin.series.series_edit", series_id=series_id)

        series.name = name
        series.slug = slug
        series.description = request.form.get('description') or None
        series.applicable_space = request.form.get('applicable_space') or None
        series.seo_title = request.form.get('seo_title') or None
        series.seo_description = request.form.get('seo_description') or None
        series.seo_keywords = request.form.get('seo_keywords') or None

        # 追加新图片（总共最多5张）
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
                current_app.logger.info(f"为系列 '{name}' 添加 {len(new_photos)} 张新图片")
        elif request.files.getlist('photos'):
            current_app.logger.info(f"忽略系列 '{name}' 的额外上传图片（已达5张上限）")

        db.session.commit()

        current_app.logger.info(f"专题系列更新成功：{name} (slug: {slug}) 由 {current_user.username} 操作 | 新增图片：{len(new_photos)}")
        return flash_redirect(
            f"专题系列 '{name}' 更新成功！",
            "success",
            "admin.series.series_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("更新专题系列失败")
        return flash_redirect(f"更新失败：{str(e)}", "danger", "admin.series.series_edit", series_id=series_id)


@series_bp.route('/delete/<int:series_id>', methods=['POST'])
@admin_required
def series_delete(series_id):
    """删除专题系列（同时清理所有关联图片）"""
    series = FeatureSeries.query.get_or_404(series_id)
    name = series.name

    try:
        # 使用统一服务清理图片
        deleted_count = ImageService.delete_multiple(series.photos, subdir='series')
        current_app.logger.info(f"删除系列 '{name}' 的 {deleted_count} 张图片")

        db.session.delete(series)
        db.session.commit()

        current_app.logger.info(f"专题系列已永久删除：{name} (id: {series_id}) 由 {current_user.username} 操作")
        return flash_redirect(
            f"专题系列 '{name}' 已永久删除",
            "success",
            "admin.series.series_list"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("删除专题系列失败")
        return flash_redirect(f"删除失败：{str(e)}", "danger", "admin.series.series_list")
