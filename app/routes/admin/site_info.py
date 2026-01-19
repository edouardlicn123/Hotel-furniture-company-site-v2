# app/routes/admin/site_info.py
# 后台网站设置管理 - 完整优化版（整合 admin_utils.py 通用工具）
# 更新日期：2026-01-19
# 优化点：
# - Logo 上传改用「先读内存 → 再写磁盘」方式，彻底解决 Windows [WinError 32] 文件占用问题
# - 使用 BytesIO + shutil.copyfileobj 确保上传文件流及时关闭
# - 其他逻辑保持不变，异常处理更清晰
# - 所有用户提示为英文，日志记录完善

from flask import Blueprint, render_template, request, current_app
from flask_login import current_user
from app.models import Settings
from app import db
import os
from PIL import Image
from io import BytesIO
import shutil
from app.admin_utils import admin_required, flash_redirect

site_info_bp = Blueprint('site_info', __name__, url_prefix='/settings')


@site_info_bp.route('/', methods=['GET', 'POST'])
@admin_required
def settings():
    """Website global settings management"""
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()

    # Load available themes
    themes_dir = os.path.join(current_app.root_path, 'static', 'css', 'themes')
    theme_files = ['default']
    try:
        if os.path.exists(themes_dir) and os.path.isdir(themes_dir):
            for f in os.listdir(themes_dir):
                if f.endswith('.css') and f != 'variables.css':
                    theme_files.append(f[:-4])
            theme_files.sort()
    except Exception as e:
        current_app.logger.error(f"Failed to load themes directory: {e}")

    # Fix invalid theme
    if settings.theme and settings.theme not in theme_files:
        settings.theme = 'default'
        db.session.commit()

    if request.method == 'POST':
        try:
            # Basic settings
            settings.company_name = request.form.get('company_name', '').strip()

            selected_theme = request.form.get('theme')
            settings.theme = selected_theme if selected_theme in theme_files else 'default'

            # Website mode
            settings.mode = request.form.get('mode', 'official')

            # Company introduction
            settings.basic_info = request.form.get('basic_info') or None
            settings.company_advantages = request.form.get('company_advantages') or None

            # Contact information
            settings.phone1 = request.form.get('phone1') or None
            settings.phone2 = request.form.get('phone2') or None
            settings.phone3 = request.form.get('phone3') or None
            settings.email1 = request.form.get('email1') or None
            settings.email2 = request.form.get('email2') or None
            settings.email3 = request.form.get('email3') or None
            settings.fax = request.form.get('fax') or None
            settings.address = request.form.get('address') or None

            # Social contacts
            settings.whatsapp1 = request.form.get('whatsapp1') or None
            settings.whatsapp2 = request.form.get('whatsapp2') or None
            settings.wechat1 = request.form.get('wechat1') or None
            settings.wechat2 = request.form.get('wechat2') or None

            # SEO fields
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

            # Logo upload handling - 使用内存缓冲方式（解决 Windows 文件占用问题）
            logo_file = request.files.get('logo')
            if logo_file and logo_file.filename:
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'logo')
                os.makedirs(upload_folder, exist_ok=True)

                # 生成最终文件名（固定为 company_logo，自动带扩展名）
                ext = logo_file.filename.rsplit('.', 1)[-1].lower() if '.' in logo_file.filename else 'png'
                final_filename = f'company_logo.{ext}'
                final_path = os.path.join(upload_folder, final_filename)

                try:
                    # 先把上传文件完全读到内存
                    file_content = BytesIO()
                    shutil.copyfileobj(logo_file.stream, file_content)
                    file_content.seek(0)  # 重置指针到开头

                    # 关闭原始上传流（非常重要！释放句柄）
                    logo_file.stream.close()

                    # 使用 PIL 检查尺寸
                    with Image.open(file_content) as img:
                        if img.width > 600 or img.height > 300:
                            return flash_redirect(
                                "Logo dimensions exceed 600×300, please upload a smaller image",
                                "danger",
                                "admin.site_info.settings"
                            )

                        # 重置指针，再次从内存写入磁盘
                        file_content.seek(0)

                        # 如果旧文件存在，先尝试删除（Windows 上更安全）
                        if os.path.exists(final_path):
                            try:
                                os.remove(final_path)
                            except PermissionError:
                                current_app.logger.warning("Old logo file locked, will overwrite directly")

                        # 从内存写入最终文件
                        with open(final_path, 'wb') as f:
                            shutil.copyfileobj(file_content, f)

                        # 保存到数据库（只存文件名，不带路径）
                        settings.logo = final_filename
                        current_app.logger.info(f"Logo updated successfully: {final_filename} by {current_user.username}")

                    # 清理内存缓冲
                    file_content.close()

                except Exception as e:
                    current_app.logger.warning(f"Logo processing failed: {str(e)}")
                    return flash_redirect(
                        f"Image processing failed: {str(e)}",
                        "danger",
                        "admin.site_info.settings"
                    )

            db.session.commit()
            current_app.logger.info(f"Site settings updated by {current_user.username}")
            return flash_redirect(
                "Website settings saved successfully!",
                "success",
                "admin.site_info.settings"
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Failed to save site settings")
            return flash_redirect(f"Save failed: {str(e)}", "danger", "admin.site_info.settings")

    return render_template(
        'admin/settings.html',
        settings=settings,
        theme_files=theme_files
    )
