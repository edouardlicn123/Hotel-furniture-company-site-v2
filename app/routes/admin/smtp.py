# app/routes/admin/smtp.py
# SMTP 配置管理 - 独立子蓝图
# 注意：为了避免循环导入，建议将 mail 的导入移到函数内部使用（延迟导入）

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app import db  # 先只导入 db，避免循环
from app.models import SmtpConfig
from flask_mail import Message
from datetime import datetime

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
        # 获取表单数据
        config.provider = request.form.get('provider', 'gmail')

        # 根据 provider 智能填充常见字段（减少用户手动输入错误）
        presets = {
            'gmail': {
                'server': 'smtp.gmail.com',
                'port': 587,
                'tls': True,
                'ssl': False
            },
            'outlook': {
                'server': 'smtp-mail.outlook.com',
                'port': 587,
                'tls': True,
                'ssl': False
            },
            'qq': {
                'server': 'smtp.qq.com',
                'port': 465,
                'tls': False,
                'ssl': True
            },
            '163': {
                'server': 'smtp.163.com',
                'port': 465,
                'tls': False,
                'ssl': True
            },
            'sendgrid': {
                'server': 'smtp.sendgrid.net',
                'port': 587,
                'tls': True,
                'ssl': False
            }
        }

        if config.provider in presets:
            p = presets[config.provider]
            config.mail_server = p['server']
            config.mail_port = p['port']
            config.mail_use_tls = p['tls']
            config.mail_use_ssl = p['ssl']
        else:
            # custom 或 enterprise 模式，手动填写
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

        # 立即更新全局 mail 配置（让发送立即生效，无需重启）
        current_app.config['MAIL_SERVER'] = config.mail_server
        current_app.config['MAIL_PORT'] = config.mail_port
        current_app.config['MAIL_USE_TLS'] = config.mail_use_tls
        current_app.config['MAIL_USE_SSL'] = config.mail_use_ssl
        current_app.config['MAIL_USERNAME'] = config.mail_username
        current_app.config['MAIL_PASSWORD'] = config.mail_password

        return redirect(url_for('admin.smtp.smtp_settings'))

    return render_template('admin/smtp.html', config=config)


@smtp_bp.route('/test', methods=['POST'])
@login_required
def test_send():
    config = SmtpConfig.query.first()
    if not config or not config.mail_username or not config.mail_password:
        flash('SMTP 配置不完整（缺少用户名或密码），无法测试发送', 'danger')
        return redirect(url_for('admin.smtp.smtp_settings'))

    recipient = request.form.get('test_recipient') or config.test_recipient
    if not recipient:
        flash('请先填写一个测试收件邮箱（在页面下方）', 'warning')
        return redirect(url_for('admin.smtp.smtp_settings'))

    try:
        # 延迟导入 mail，避免循环导入问题
        from app import mail

        msg = Message(
            subject=f"SMTP 测试邮件 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            sender=(config.default_sender_name, config.mail_username),
            recipients=[recipient],
            body="这是一封测试邮件，证明你的 SMTP 配置正确！\n\n"
                 f"发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                 "如果收到此邮件，说明配置成功。"
        )
        mail.send(msg)
        flash(f'测试邮件已成功发送至 {recipient}！请检查收件箱（或垃圾箱）。', 'success')
    except Exception as e:
        flash(f'测试发送失败：{str(e)}<br>请检查账号密码、网络、端口等配置。', 'danger')
        current_app.logger.error(f"SMTP 测试发送失败: {str(e)}")

    return redirect(url_for('admin.smtp.smtp_settings'))
