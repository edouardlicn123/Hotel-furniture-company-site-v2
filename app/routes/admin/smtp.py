# app/routes/admin/smtp.py
# SMTP 配置管理 - 独立子蓝图（最终优化版：使用 yagmail 发送测试邮件）
# 更新日期：2026-01-19
# 优化点：
# - 测试邮件发送切换到 yagmail（彻底绕过 smtplib TLS/SSL EOF 握手问题）
# - 保留重试机制、详细日志、冷却机制
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
    """SMTP 配置管理"""
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
            config.default_sender_name = request.form.get('default_sender_name', '酒店家具官网').strip()
            config.is_active = 'is_active' in request.form

            db.session.commit()
            current_app.logger.info(f"SMTP 设置已由 {current_user.username} 更新")
            return flash_redirect("SMTP 配置保存成功！", "success", "admin.smtp.smtp_settings")

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("保存 SMTP 配置失败")
            return flash_redirect(f"保存失败：{str(e)}", "danger", "admin.smtp.smtp_settings")

    return render_template('admin/smtp.html', config=config)


@smtp_bp.route('/test', methods=['POST'])
@admin_required
def test_send():
    """使用 yagmail 测试 SMTP 连接并发送测试邮件"""
    config = SmtpConfig.query.first()
    if not config:
        return flash_redirect("未找到 SMTP 配置，请先保存设置。", "danger", "admin.smtp.smtp_settings")

    if not config.mail_username or not config.mail_password:
        return flash_redirect("SMTP 配置不完整（缺少用户名或密码），无法测试。", "danger", "admin.smtp.smtp_settings")

    recipient = request.form.get('test_recipient') or config.test_recipient
    if not recipient:
        return flash_redirect("请提供测试收件人邮箱地址。", "warning", "admin.smtp.smtp_settings")

    mail_server = config.mail_server
    mail_port = config.mail_port
    mail_use_tls = config.mail_use_tls
    mail_use_ssl = config.mail_use_ssl
    mail_username = config.mail_username
    mail_password = config.mail_password

    current_app.logger.info(
        f"SMTP 测试由 {current_user.username} 发起 | "
        f"收件人：{recipient} | 服务器：{mail_server}:{mail_port} | "
        f"SSL：{mail_use_ssl} | TLS：{mail_use_tls}"
    )

    retries = 2
    for attempt in range(1, retries + 1):
        try:
            current_app.logger.info(f"第 {attempt}/{retries} 次尝试：使用 yagmail 发送")

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
                "这是一封测试邮件，用于验证您的 SMTP 配置是否正常。\n\n"
                f"发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "如果您收到此邮件，说明配置正确。\n\n"
                "酒店家具官网"
            )

            yag.send(
                to=recipient,
                subject=f"SMTP 测试邮件 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}（第 {attempt} 次）",
                contents=body
            )

            current_app.logger.info(f"SMTP 测试邮件成功发送至 {recipient}（使用 yagmail）")
            return flash_redirect(
                f"测试邮件已成功发送至 {recipient}！请检查收件箱（或垃圾邮件/推广邮件文件夹）。",
                "success",
                "admin.smtp.smtp_settings"
            )

        except Exception as e:
            error_msg = str(e)
            full_trace = traceback.format_exc()

            current_app.logger.warning(f"SMTP 测试失败（第 {attempt}/{retries} 次）：{error_msg}")
            current_app.logger.debug(f"完整 traceback：\n{full_trace}")

            if attempt < retries:
                current_app.logger.info("5 秒后重试...")
                time.sleep(5)
                continue
            else:
                return flash_redirect(
                    f"经过 {retries} 次尝试后测试失败：{error_msg}。 "
                    "常见解决方法：检查应用专用密码/授权码、关闭 VPN、尝试手机热点、确认端口和加密方式。",
                    "danger",
                    "admin.smtp.smtp_settings"
                )
