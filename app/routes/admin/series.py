# app/routes/admin/series.py
# 后台专题系列管理 - 完整 CRUD（图片处理已迁移到统一服务层）

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import FeatureSeries
from app import db
from app.services.image_service import ImageService   # ← 新增：统一图片服务

series_bp = Blueprint('series', __name__, url_prefix='/series')


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
            slug = name.lower().replace(' ', '-').replace('_', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')

        if FeatureSeries.query.filter_by(slug=slug).first():
            flash(f'系统名称 "{slug}" 已存在，请修改！', 'danger')
            return render_template('admin/series_form.html', series=None)

        description = request.form.get('description') or None
        applicable_space = request.form.get('applicable_space') or None
        seo_title = request.form.get('seo_title') or None
        seo_description = request.form.get('seo_description') or None
        seo_keywords = request.form.get('seo_keywords') or None

        # 处理多图上传（最多5张） - 使用统一图片服务
        extra_files = request.files.getlist('photos')
        new_photos = ImageService.save_multiple(
            files=extra_files,
            subdir='series',
            prefix=f"{slug}_",
            max_count=5
        )

        if len(new_photos) < len(extra_files):
            flash(f'部分图片上传失败，仅成功 {len(new_photos)} 张（最多允许5张）', 'warning')

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

        # 追加新图片（最多总共5张） - 使用统一图片服务
        extra_files = request.files.getlist('photos')
        current_count = len(series.photos.split(',')) if series.photos else 0
        remain_slots = max(0, 5 - current_count)

        if extra_files and remain_slots > 0:
            new_photos = ImageService.save_multiple(
                files=extra_files,
                subdir='series',
                prefix=f"{slug}_",
                max_count=remain_slots
            )

            if new_photos:
                existing = series.photos.split(',') if series.photos else []
                series.photos = ','.join(existing + new_photos)
        elif extra_files:
            flash('已达到5张图片上限，无法继续添加', 'warning')

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

    # 使用统一服务删除所有关联图片
    ImageService.delete_multiple(series.photos, subdir='series')

    db.session.delete(series)
    try:
        db.session.commit()
        flash(f'专题系列 "{name}" 已彻底删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')

    return redirect(url_for('admin.series.series_list'))
