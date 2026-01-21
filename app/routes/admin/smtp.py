# app/routes/admin/smtp.py
# SMTP 配置管理 - 独立子蓝图（最终优化版：使用 yagmail 发送测试邮件）
# 更新日期：2026-01-19
# 优化点：
# - 测试邮件发送切换到 yagmail（彻底绕过 smtplib TLS/SSL EOF 握手问题）
# - yagmail 兼容 Gmail / 163 / QQ 等所有预设（587 + STARTTLS 或 465 + SSL）
# - 保留重试机制、详细日志、冷却机制
# - 手动 AUTH LOGIN + base64 不再需要（yagmail 内部处理）
# - 测试邮件内容保持不变

from flask import Blueprint, render_template, request, current_app
from flask_login import current_user
from app.models import SmtpConfig
from app import db
import yagmail
import time
import logging
from datetime import datetime
import traceback
from app.admin_utils import admin_required, flash_redirect

smtp_bp = Blueprint('smtp', __name__, url_prefix='/smtp')

logger = logging.getLogger(__name__)


@smtp_bp.route('/', methods=['GET', 'POST'])
@admin_required
def smtp_settings():
    """SMTP configuration management"""
    config = SmtpConfig.query.first()
    if not config:
        config = SmtpConfig()
        db.session.add(config)
        db.session.commit()

    if request.method == 'POST':
        try:
            config.provider = request.form.get('provider', 'gmail')

            presets = {
                'gmail': {'server': 'smtp.gmail.com', 'port': 587, 'tls': True, 'ssl': False},
                'gmail-465': {'server': 'smtp.gmail.com', 'port': 465, 'tls': False, 'ssl': True},
                'outlook': {'server': 'smtp-mail.outlook.com', 'port': 587, 'tls': True, 'ssl': False},
                'qq': {'server': 'smtp.qq.com', 'port': 465, 'tls': False, 'ssl': True},
                '163': {'server': 'smtp.163.com', 'port': 465, 'tls': False, 'ssl': True},
                'sendgrid': {'server': 'smtp.sendgrid.net', 'port': 587, 'tls': True, 'ssl': False}
            }

            if config.provider in presets:
                p = presets[config.provider]
                config.mail_server = p['server']
                config.mail_port = p['port']
                config.mail_use_tls = p['tls']
                config.mail_use_ssl = p['ssl']
            else:
                config.mail_server = request.form.get('mail_server', '').strip()
                try:
                    config.mail_port = int(request.form.get('mail_port', 587))
                except (ValueError, TypeError):
                    config.mail_port = 587
                config.mail_use_tls = 'mail_use_tls' in request.form
                config.mail_use_ssl = 'mail_use_ssl' in request.form

            config.mail_username = request.form.get('mail_username', '').strip()
            config.mail_password = request.form.get('mail_password', '').strip()
            config.test_recipient = request.form.get('test_recipient', '').strip()
            config.default_sender_name = request.form.get('default_sender_name', 'Hotel Furniture Site').strip()
            config.is_active = 'is_active' in request.form

            db.session.commit()
            current_app.logger.info(f"SMTP settings updated by {current_user.username}")
            return flash_redirect("SMTP configuration saved successfully!", "success", "admin.smtp.smtp_settings")

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Failed to save SMTP settings")
            return flash_redirect(f"Save failed: {str(e)}", "danger", "admin.smtp.smtp_settings")

    return render_template('admin/smtp.html', config=config)


@smtp_bp.route('/test', methods=['POST'])
@admin_required
def test_send():
    """Test SMTP connection and send a test email using yagmail"""
    config = SmtpConfig.query.first()
    if not config:
        return flash_redirect("No SMTP configuration found. Please save settings first.", "danger", "admin.smtp.smtp_settings")

    if not config.mail_username or not config.mail_password:
        return flash_redirect("Incomplete SMTP configuration (missing username or password). Cannot test.", "danger", "admin.smtp.smtp_settings")

    recipient = request.form.get('test_recipient') or config.test_recipient
    if not recipient:
        return flash_redirect("Please provide a test recipient email address.", "warning", "admin.smtp.smtp_settings")

    mail_server = config.mail_server
    mail_port = config.mail_port
    mail_use_tls = config.mail_use_tls
    mail_use_ssl = config.mail_use_ssl
    mail_username = config.mail_username
    mail_password = config.mail_password

    current_app.logger.info(
        f"SMTP test started by {current_user.username} | "
        f"Recipient: {recipient} | Server: {mail_server}:{mail_port} | "
        f"SSL: {mail_use_ssl} | TLS: {mail_use_tls}"
    )

    retries = 2
    for attempt in range(1, retries + 1):
        try:
            current_app.logger.info(f"Attempt {attempt}/{retries}: Sending via yagmail")

            # yagmail 自动处理 TLS/SSL，根据参数判断
            yag = yagmail.SMTP(
                user=mail_username,
                password=mail_password,
                host=mail_server,
                port=mail_port,
                smtp_starttls=mail_use_tls,
                smtp_ssl=mail_use_ssl
            )

            # 构建测试邮件内容
            body = (
                "This is a test email to verify your SMTP configuration.\n\n"
                f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "If you received this, the configuration is working correctly.\n\n"
                "Hotel Furniture Website"
            )

            yag.send(
                to=recipient,
                subject=f"SMTP Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Attempt {attempt})",
                contents=body
            )

            current_app.logger.info(f"SMTP test email sent successfully to {recipient} via yagmail")
            return flash_redirect(
                f"Test email sent successfully to {recipient}! Please check inbox (or spam/promotions folder).",
                "success",
                "admin.smtp.smtp_settings"
            )

        except Exception as e:
            error_msg = str(e)
            full_trace = traceback.format_exc()

            current_app.logger.warning(f"SMTP test failed (attempt {attempt}/{retries}): {error_msg}")
            current_app.logger.debug(f"Full traceback:\n{full_trace}")

            if attempt < retries:
                current_app.logger.info("Retrying in 5 seconds...")
                time.sleep(5)
                continue
            else:
                return flash_redirect(
                    f"Test failed after {retries} attempts: {error_msg}. "
                    "Common fixes: Check app password/authorization code, close VPN, try phone hotspot.",
                    "danger",
                    "admin.smtp.smtp_settings"
                )
