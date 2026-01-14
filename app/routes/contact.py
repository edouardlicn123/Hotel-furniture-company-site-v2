# app/routes/contact.py
# 联系页面路由 - 最终优化版（2026-01-14）
# 所有可能出错的操作全部放进 try 块，确保始终返回 JSON

from flask import Blueprint, request, jsonify, session, current_app, render_template
from datetime import datetime, timedelta
from app.models import Settings, SmtpConfig
from app.utils.mail import send_email

contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

@contact_bp.route('/', methods=['GET'])
def contact_page():
    """GET: 显示联系页面"""
    return render_template('contact.html')


@contact_bp.route('/send', methods=['POST'])
def send_contact():
    """POST: 处理联系表单提交并发送邮件"""
    # ==================== 频率限制：2分钟冷却 ====================
    last_submit = session.get('last_contact_submit')
    if last_submit:
        last_time = datetime.fromtimestamp(last_submit)
        if datetime.now() - last_time < timedelta(minutes=2):
            remaining = int((timedelta(minutes=2) - (datetime.now() - last_time)).total_seconds() / 60)
            if remaining <= 0:
                remaining = 1
            return jsonify({
                'success': False,
                'message': f'Please do not submit too frequently. Please try again in {remaining} minute{"s" if remaining > 1 else ""}.'
            }), 429

    # ==================== 获取提交数据（支持 JSON 和 form） ====================
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form.to_dict() or {}

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    whatsapp = data.get('whatsapp', '').strip()
    subject = data.get('subject', 'General Inquiry').strip()
    message = data.get('message', '').strip()

    # ==================== 必填字段 + 邮箱格式校验 ====================
    if not all([name, email, message]):
        return jsonify({
            'success': False,
            'message': 'Name, Email and Message are required.'
        }), 400

    if '@' not in email or '.' not in email.split('@')[-1] or len(email) < 6:
        return jsonify({
            'success': False,
            'message': 'Please enter a valid email address.'
        }), 400

    # ==================== 记录提交时间，防止重复 ====================
    session['last_contact_submit'] = datetime.now().timestamp()

    # ==================== 全部可能出错的操作放进 try 块 ====================
    try:
        # 获取网站设置
        settings = Settings.query.first()
        if not settings:
            current_app.logger.error("Settings table is empty or not found")
            return jsonify({
                'success': False,
                'message': 'Server configuration error (settings not found).'
            }), 500

        if not settings.email1:
            current_app.logger.error("No recipient email configured in settings")
            return jsonify({
                'success': False,
                'message': 'Server configuration error (missing recipient email).'
            }), 500

        recipient = settings.email1
        sender_name = settings.company_name or "Hotel Furniture Website"

        # 获取 SMTP 配置
        smtp_config = SmtpConfig.query.first()
        if not smtp_config:
            current_app.logger.error("SMTP config table is empty or not found")
            return jsonify({
                'success': False,
                'message': 'Server SMTP configuration error (config not found).'
            }), 500

        if not all([
            smtp_config.mail_server,
            smtp_config.mail_port,
            smtp_config.mail_username,
            smtp_config.mail_password
        ]):
            current_app.logger.error("Incomplete SMTP configuration")
            return jsonify({
                'success': False,
                'message': 'Server SMTP configuration error (missing fields).'
            }), 500

        # 构造邮件主题与正文（中文，面向运营）
        mail_subject = f"网站新留言 - {subject} - {name}"
        mail_body = f"""收到新的网站联系留言：

----------------------------------------
客户姓名:   {name}
邮箱地址:   {email}
WhatsApp/电话: {whatsapp or '未提供'}
主题:       {subject}
----------------------------------------
留言内容:
{message}
----------------------------------------
提交时间:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (HKT)
来源IP:     {request.remote_addr}
----------------------------------------
请尽快回复客户，谢谢！
"""

        # 发送邮件
        success, msg = send_email(
            smtp_server=smtp_config.mail_server,
            smtp_port=smtp_config.mail_port,
            username=smtp_config.mail_username,
            password=smtp_config.mail_password,
            from_addr=smtp_config.mail_username,
            to_addr=recipient,
            subject=mail_subject,
            body=mail_body,
            is_html=False,
            use_ssl=smtp_config.mail_use_ssl,
            use_tls=smtp_config.mail_use_tls,
            sender_name=sender_name
        )

        if success:
            current_app.logger.info(f"Contact email sent to {recipient} | From: {name} <{email}>")
            return jsonify({
                'success': True,
                'message': 'Your message has been sent successfully! We will reply soon.'
            })

        else:
            current_app.logger.error(f"Contact email failed: {msg}")
            return jsonify({
                'success': False,
                'message': msg or 'Failed to send message. Please try again later.'
            }), 500

    except Exception as e:
        current_app.logger.exception("Unexpected error in contact form submission")
        return jsonify({
            'success': False,
            'message': 'Server error occurred. Please try again later.'
        }), 500
