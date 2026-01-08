# app/routes/admin/site_info.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.models import Settings
from app import db
import os
from PIL import Image

site_info_bp = Blueprint('site_info', __name__, url_prefix='/settings')

@site_info_bp.route('/', methods=['GET', 'POST'])
@login_required
def settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()

    themes_dir = os.path.join(current_app.root_path, 'static', 'css', 'themes')
    theme_files = ['default']
    try:
        if os.path.exists(themes_dir) and os.path.isdir(themes_dir):
            for f in os.listdir(themes_dir):
                if f.endswith('.css') and f != 'variables.css':
                    theme_files.append(f[:-4])
            theme_files.sort()
    except Exception as e:
        current_app.logger.error(f"读取主题失败: {e}")

    if settings.theme and settings.theme not in theme_files:
        settings.theme = 'default'
        db.session.commit()

    if request.method == 'POST':
        try:
            settings.company_name = request.form.get('company_name', '').strip()
            selected_theme = request.form.get('theme')
            if selected_theme in theme_files:
                settings.theme = selected_theme
            else:
                settings.theme = 'default'

            # SEO 字段
            settings.seo_home_title = request.form.get('seo_home_title', '')
            settings.seo_home_description = request.form.get('seo_home_description', '')
            settings.seo_home_keywords = request.form.get('seo_home_keywords', '')
            settings.seo_products_title = request.form.get('seo_products_title', '')
            settings.seo_products_description = request.form.get('seo_products_description', '')
            settings.seo_products_keywords = request.form.get('seo_products_keywords', '')
            settings.seo_about_title = request.form.get('seo_about_title', '')
            settings.seo_about_description = request.form.get('seo_about_description', '')
            settings.seo_contact_title = request.form.get('seo_contact_title', '')
            settings.seo_contact_description = request.form.get('seo_contact_description', '')

            # Logo 处理
            logo_file = request.files.get('logo')
            if logo_file and logo_file.filename:
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'logo')
                os.makedirs(upload_folder, exist_ok=True)
                ext = logo_file.filename.rsplit('.', 1)[-1].lower() if '.' in logo_file.filename else 'png'
                temp_path = os.path.join(upload_folder, f'temp_company_logo.{ext}')
                logo_file.save(temp_path)
                try:
                    with Image.open(temp_path) as img:
                        if img.width > 600 or img.height > 300:
                            os.remove(temp_path)
                            flash('Logo 尺寸超过 600×300，请重新上传！', 'danger')
                        else:
                            final_path = os.path.join(upload_folder, 'company_logo')
                            if os.path.exists(final_path):
                                os.remove(final_path)
                            os.rename(temp_path, final_path)
                            settings.logo = 'company_logo'
                            flash('Logo 更新成功！', 'success')
                except Exception as e:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    flash(f'图片处理失败：{e}', 'danger')

            db.session.commit()
            flash('网站设置保存成功！', 'success')
            return redirect(url_for('admin.site_info.settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{e}', 'danger')

    return render_template('admin/settings.html', settings=settings, theme_files=theme_files)
