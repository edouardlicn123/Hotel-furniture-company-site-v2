# app/routes/admin/smtp.py
# SMTP 配置管理 - 独立子蓝图（优化版：手动 smtplib 发送 + 兼容163/Gmail + 纯From地址）
# 更新日期：2026-01-16
# 优化点：
# - 使用 admin_utils.py 作为独立工具模块（彻底避免循环导入）
# - 顶层导入 admin_required 和 flash_redirect（安全、无风险）
# - 所有用户提示改为英文（国际化）
# - 移除 print 调试，改用 current_app.logger
# - 测试发送失败时记录详细日志（含 traceback）
# - 增强安全性：密码不记录日志，异常处理更健壮

from flask import Blueprint, render_template, request, current_app
from flask_login import current_user
from app.models import SmtpConfig
from app import db
import socket
import time
import base64
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import traceback
from app.admin_utils import admin_required, flash_redirect

smtp_bp = Blueprint('smtp', __name__, url_prefix='/smtp')


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
    """Test SMTP connection and send a test email"""
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

    current_app.logger.info(f"SMTP test started by {current_user.username} | Recipient: {recipient} | Server: {mail_server}:{mail_port}")

    retries = 2
    for attempt in range(retries + 1):
        server = None
        try:
            if mail_use_ssl:
                server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=20)
            else:
                server = smtplib.SMTP(mail_server, mail_port, timeout=20)
                server.ehlo()
                if mail_use_tls:
                    server.starttls()
                    server.ehlo()

            # Manual AUTH LOGIN with base64 UTF-8 (compatible with non-ASCII auth codes)
            server.docmd("AUTH LOGIN")
            server.docmd(base64.b64encode(mail_username.encode('utf-8')).decode('ascii'))
            server.docmd(base64.b64encode(mail_password.encode('utf-8')).decode('ascii'))

            # Build test message
            msg = MIMEText(
                "This is a test email to verify your SMTP configuration.\n\n"
                f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "If you received this, the configuration is working correctly.\n\n"
                "Hotel Furniture Website",
                'plain',
                'utf-8'
            )
            msg['From'] = mail_username  # Pure email address (compatible with strict servers like 163)
            msg['To'] = recipient
            msg['Subject'] = f"SMTP Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Attempt {attempt + 1})"

            server.send_message(msg)
            server.quit()

            current_app.logger.info(f"SMTP test email sent successfully to {recipient}")
            return flash_redirect(
                f"Test email sent successfully to {recipient}! Please check inbox (or spam/promotions folder).",
                "success",
                "admin.smtp.smtp_settings"
            )

        except Exception as e:
            error_msg = str(e)
            full_trace = traceback.format_exc()

            current_app.logger.warning(f"SMTP test failed (attempt {attempt + 1}/{retries + 1}): {error_msg}")
            current_app.logger.debug(f"Full traceback:\n{full_trace}")

            if attempt < retries:
                current_app.logger.info("Retrying in 5 seconds...")
                time.sleep(5)
                continue
            else:
                return flash_redirect(
                    f"Test failed after {retries + 1} attempts: {error_msg}. Please check logs for details.",
                    "danger",
                    "admin.smtp.smtp_settings"
                )

        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass
