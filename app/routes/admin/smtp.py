# app/routes/admin/smtp.py
# SMTP 配置管理 - 改进版：使用标准 smtplib 登录方式 + 重试机制

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app import db
from app.models import SmtpConfig
from datetime import datetime
import traceback
import socket
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

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
            'sendgrid': {'server': 'smtp.sendgrid.net', 'port': 587, 'tls': True, 'ssl': False},
            # 可自行添加更多，例如腾讯企业邮
            'exmail': {'server': 'smtp.exmail.qq.com', 'port': 465, 'tls': False, 'ssl': True},
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
    use_tls = config.mail_use_tls
    use_ssl = config.mail_use_ssl
    username = config.mail_username
    password = config.mail_password
    sender_name = config.default_sender_name or '酒店家具官网'

    print(f"\n★ [SMTP TEST] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始测试...")
    print(f"★ 配置：Server={mail_server}, Port={mail_port}, SSL={use_ssl}, TLS={use_tls}")
    print(f"★ Username: {username}")
    print(f"★ 收件人: {recipient}")

    try:
        ip = socket.gethostbyname(mail_server)
        print(f"★ 域名解析 IP: {ip}")
    except Exception as e:
        print(f"★ IP 解析失败: {e}")

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        server = None
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=20)
            else:
                server = smtplib.SMTP(mail_server, mail_port, timeout=20)
                server.ehlo()  # 标识客户端
                if use_tls:
                    server.starttls()
                    server.ehlo()

            print(f"★ 连接成功，正在登录 (尝试 {attempt}/{max_retries})...")
            server.login(username, password)
            print("★ 登录成功！")

            # 准备测试邮件
            msg = MIMEText(
                "这是一封测试邮件，证明你的 SMTP 配置正确！\n\n"
                f"发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "如果收到此邮件，说明配置成功。\n\n"
                "—— 酒店家具官网系统自动发送",
                'plain', 'utf-8'
            )

            # 发件人（建议使用纯邮箱地址，避免中文发件名被拦截）
            msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), username))
            msg['To'] = recipient
            msg['Subject'] = Header(f"SMTP 测试邮件 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'utf-8')

            server.send_message(msg)
            server.quit()

            print("★ [SMTP TEST] 发送成功！")
            flash(f'测试邮件已成功发送至 {recipient}！请检查收件箱或垃圾箱。', 'success')
            break

        except smtplib.SMTPAuthenticationError:
            flash('认证失败：用户名或密码（授权码）错误，请检查 SMTP 配置', 'danger')
            print("★ 认证失败（用户名/密码/授权码错误）")
            break  # 认证错误无需重试

        except (smtplib.SMTPConnectError, ConnectionError, OSError) as e:
            error_msg = str(e)
            print(f"★ 连接失败 (尝试 {attempt}): {error_msg}")
            if attempt < max_retries:
                delay = 3 * attempt  # 3s → 6s → 9s
                print(f"★ 等待 {delay} 秒后重试...")
                time.sleep(delay)
                continue
            flash(f'连接失败（尝试 {max_retries} 次）：{error_msg}<br>请检查网络或 SMTP 服务器地址/端口', 'danger')

        except Exception as e:
            error_msg = str(e)
            full_trace = traceback.format_exc()
            print(f"★ 未知错误 (尝试 {attempt}): {error_msg}")
            print(f"★ 完整 traceback:\n{full_trace}")
            if attempt < max_retries:
                time.sleep(3)
                continue
            flash(f'发送失败（尝试 {max_retries} 次）：{error_msg}<br>请查看终端日志', 'danger')
            current_app.logger.error(f"SMTP 测试失败: {error_msg}\n{full_trace}")

        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass

    return redirect(url_for('admin.smtp.smtp_settings'))
