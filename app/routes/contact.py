# app/routes/contact.py
# 联系页面路由 - 更新版（使用已新建的 app.utils.mail.send_email）

from flask import Blueprint, request, jsonify, session, current_app, render_template
from datetime import datetime, timedelta
from app.models import Settings, SmtpConfig
from app.utils.mail import send_email  # 已新建的文件，包含 send_email 函数

contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

# 页面路由：/contact （GET 显示页面）
@contact_bp.route('/', methods=['GET'])
def contact_page():
    return render_template('contact.html')

# 发送路由：/contact/send （POST - 支持表单 & JSON）
@contact_bp.route('/send', methods=['POST'])
def send_contact():
    # ==================== 1. Rate limiting: 30 分钟冷却 ====================
    last_submit = session.get('last_contact_submit')
    if last_submit:
        last_time = datetime.fromtimestamp(last_submit)
        if datetime.now() - last_time < timedelta(minutes=30):
            remaining = int((timedelta(minutes=30) - (datetime.now() - last_time)).total_seconds() / 60)
            return jsonify({
                'success': False,
                'message': f'Please do not submit too frequently. Try again in {remaining} minute{"s" if remaining > 1 else ""}.'
            }), 429

    # ==================== 2. 获取数据 - 支持表单 & JSON ====================
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form.to_dict() or {}

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    whatsapp = data.get('whatsapp', '').strip()
    subject = data.get('subject', 'General Inquiry').strip()  # 默认主题
    message = data.get('message', '').strip()

    # ==================== 3. 必填字段校验 ====================
    if not all([name, email, message]):
        return jsonify({
            'success': False,
            'message': 'Please fill in Name, Email and Message.'
        }), 400

    if '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({
            'success': False,
            'message': 'Please enter a valid email address.'
        }), 400

    # ==================== 4. 记录提交时间，防止重复 ====================
    session['last_contact_submit'] = datetime.now().timestamp()

    # ==================== 5. 发送邮件（调用统一的 send_email 函数） ====================
    try:
        settings = Settings.query.first()
        if not settings or not settings.email1:
            current_app.logger.error("Settings or recipient email not configured")
            return jsonify({
                'success': False,
                'message': 'Server configuration error (missing recipient email).'
            }), 500

        recipient = settings.email1
        sender_name = settings.company_name or "Hotel Furniture Website"

        smtp_config = SmtpConfig.query.first()
        if not smtp_config or not smtp_config.mail_username or not smtp_config.mail_password:
            current_app.logger.error("SMTP configuration incomplete")
            return jsonify({
                'success': False,
                'message': 'Server SMTP configuration error.'
            }), 500

        mail_subject = f"New Contact: {subject} from {name}"
        mail_body = f"""
New contact message received:

Name:     {name}
Email:    {email}
WhatsApp: {whatsapp or 'Not provided'}
Subject:  {subject}

Message:
{message}

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (HKT)
IP:      {request.remote_addr}
"""

        current_app.logger.info(f"Sending contact email to {recipient} | Subject: {mail_subject}")

        success, msg = send_email(
            smtp_server=smtp_config.mail_server,
            smtp_port=smtp_config.mail_port,
            username=smtp_config.mail_username,
            password=smtp_config.mail_password,  # 后续可考虑加密存储
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
            current_app.logger.info(f"Contact email sent successfully to {recipient}")
            return jsonify({
                'success': True,
                'message': 'Your message has been sent successfully! We will reply soon.'
            })

        current_app.logger.error(f"Contact email sending failed: {msg}")
        return jsonify({
            'success': False,
            'message': msg or 'Failed to send message. Please try again later.'
        }), 500

    except Exception as e:
        current_app.logger.exception("Unexpected error in contact form")
        return jsonify({
            'success': False,
            'message': 'Server error occurred. Please try again later.'
        }), 500
