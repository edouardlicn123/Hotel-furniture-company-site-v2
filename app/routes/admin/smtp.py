# app/routes/admin/smtp.py
# SMTP 配置管理 - 更新版（使用统一的 app.utils.mail.send_email 函数进行测试发送）

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app import db
from app.models import SmtpConfig
from datetime import datetime
import traceback
import socket
import time
from app.utils.mail import send_email  # 已新建的统一邮件发送函数

smtp_bp = Blueprint('smtp', __name__, url_prefix='/smtp')

@smtp_bp.route('/', methods=['GET', 'POST'])
@login_required
def smtp_settings():
    config = SmtpConfig.query.first()
    if not config:
        config = SmtpConfig()
        db.session.add(config)
        db.session.commit()

    if request.method == 'POST':
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
        flash('SMTP 配置已保存！', 'success')

        return redirect(url_for('admin.smtp.smtp_settings'))

    return render_template('admin/smtp.html', config=config)


@smtp_bp.route('/test', methods=['POST'])
@login_required
def test_send():
    config = SmtpConfig.query.first()
    if not config:
        flash('未找到 SMTP 配置，请先保存设置', 'danger')
        return redirect(url_for('admin.smtp.smtp_settings'))

    if not config.mail_username or not config.mail_password:
        flash('SMTP 配置不完整（缺少用户名或密码），无法测试发送', 'danger')
        return redirect(url_for('admin.smtp.smtp_settings'))

    recipient = request.form.get('test_recipient') or config.test_recipient
    if not recipient:
        flash('请先填写一个测试收件邮箱（在页面下方）', 'warning')
        return redirect(url_for('admin.smtp.smtp_settings'))

    mail_server = config.mail_server
    mail_port = config.mail_port
    mail_use_tls = config.mail_use_tls
    mail_use_ssl = config.mail_use_ssl
    mail_username = config.mail_username
    mail_password = config.mail_password
    sender_name = config.default_sender_name or '酒店家具官网'

    print(f"★ [SMTP TEST] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始测试...")
    print(f"★ 配置：Server={mail_server}, Port={mail_port}")
    print(f"★ TLS={mail_use_tls}, SSL={mail_use_ssl}")
    print(f"★ Username: {mail_username}")
    print(f"★ 收件人: {recipient}")

    try:
        ip = socket.gethostbyname(mail_server)
        print(f"★ 解析 IP: {ip}")
    except Exception as e:
        print(f"★ IP 解析失败: {e}")

    retries = 2
    for attempt in range(retries + 1):
        try:
            # 使用统一的 send_email 函数发送测试邮件
            success, msg = send_email(
                smtp_server=mail_server,
                smtp_port=mail_port,
                username=mail_username,
                password=mail_password,
                from_addr=mail_username,
                to_addr=recipient,
                subject=f"SMTP 测试邮件 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (尝试 {attempt + 1})",
                body="这是一封测试邮件，证明你的 SMTP 配置正确！\n\n"
                     f"发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                     "如果收到此邮件，说明配置成功。",
                is_html=False,
                use_ssl=mail_use_ssl,
                use_tls=mail_use_tls,
                sender_name=sender_name
            )

            if success:
                print("★ [SMTP TEST] 发送成功！")
                flash(f'测试邮件已成功发送至 {recipient}！请检查收件箱（或垃圾箱/促销邮件）。', 'success')
                break
            else:
                raise Exception(msg)

        except Exception as e:
            error_msg = str(e)
            full_traceback = traceback.format_exc()
            print(f"★ [SMTP TEST] 第 {attempt + 1} 次失败: {error_msg}")
            print(f"★ 完整 traceback:\n{full_traceback}")

            if attempt < retries:
                print("★ 等待 5 秒后重试...")
                time.sleep(5)
                continue
            else:
                flash(f'测试发送失败（尝试 {retries + 1} 次）：{error_msg}<br>请查看终端日志。', 'danger')
                current_app.logger.error(f"SMTP 测试发送失败: {error_msg}\n{full_traceback}")

    return redirect(url_for('admin.smtp.smtp_settings'))
