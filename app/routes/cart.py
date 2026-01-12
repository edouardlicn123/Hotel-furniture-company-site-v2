# app/routes/cart.py
# Cart inquiry email sending - using pure smtplib (consistent with admin/smtp.py style)
# 2026-01-12 version - no dependency on flask-mail, fully manual sending
# Current version: email body in Chinese, no product image links

from flask import Blueprint, request, jsonify, current_app
from app.models import Settings, SmtpConfig
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import base64
import traceback

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/send-inquiry', methods=['POST'])
def send_inquiry():
    """
    Handle cart inquiry request and send email manually via smtplib
    - Uses SMTP settings from /admin/smtp
    - Does not save to database
    - Email content in Chinese, no product image links
    """
    try:
        data = request.get_json()
        if not data or not data.get('items'):
            return jsonify({'error': 'No items in cart'}), 400

        # Get site settings (for recipient email and sender name)
        settings = Settings.query.first()
        if not settings:
            return jsonify({'error': 'Site settings not found'}), 500

        recipient = settings.email1
        if not recipient:
            return jsonify({'error': 'No recipient email configured. Please set email1 in admin settings'}), 500

        # Get SMTP configuration from SmtpConfig table
        smtp = SmtpConfig.query.first()
        if not smtp:
            return jsonify({'error': 'SMTP configuration not found. Please set it up in /admin/smtp'}), 500

        if not smtp.mail_username or not smtp.mail_password:
            return jsonify({'error': 'SMTP configuration missing username or password'}), 500

        # Build email subject and body (body in Chinese)
        subject = f"New Hotel Furniture Inquiry - {len(data['items'])} items ({data.get('email', 'Anonymous')})"

        body = f"""您好，收到新的询价请求：

客户联系方式：
- 邮箱：{data.get('email', '未提供')}
- WhatsApp：{data.get('whatsapp', '未提供')}

请求商品列表：
"""
        for i, item in enumerate(data['items'], 1):
            body += f"{i}. {item['name']}（编号：{item['code']}）\n"

        body += f"""
发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (+8区时间)
备注：此为网站购物车自动提交的询价，请尽快联系客户跟进。
"""

        # Create email message
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = smtp.mail_username          # Force pure email address
        msg['To'] = recipient

        # Connect and send (same logic as admin/smtp.py test)
        print(f"★ [CART INQUIRY] Starting send - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"★ Config: Server={smtp.mail_server}, Port={smtp.mail_port}")
        print(f"★ TLS={smtp.mail_use_tls}, SSL={smtp.mail_use_ssl}")
        print(f"★ Username: {smtp.mail_username}")
        print(f"★ Recipient: {recipient}")

        if smtp.mail_use_ssl:
            server = smtplib.SMTP_SSL(smtp.mail_server, smtp.mail_port, timeout=20)
        else:
            server = smtplib.SMTP(smtp.mail_server, smtp.mail_port, timeout=20)
            if smtp.mail_use_tls:
                server.starttls()

        server.ehlo()
        server.docmd("AUTH LOGIN")
        server.docmd(base64.b64encode(smtp.mail_username.encode('utf-8')).decode('ascii'))
        server.docmd(base64.b64encode(smtp.mail_password.encode('utf-8')).decode('ascii'))

        server.send_message(msg)
        server.quit()

        print("★ [CART INQUIRY] Send successful!")

        current_app.logger.info(
            f"Cart inquiry email sent successfully to {recipient} ({len(data['items'])} items)"
        )

        return jsonify({
            'success': True,
            'message': 'Inquiry sent successfully! We will contact you soon.'
        }), 200

    except Exception as e:
        error_msg = str(e)
        full_trace = traceback.format_exc()
        print(f"★ [CART INQUIRY] Send failed: {error_msg}")
        print(f"★ Full traceback:\n{full_trace}")

        current_app.logger.error(f"Cart inquiry email send failed: {error_msg}\n{full_trace}")

        return jsonify({
            'success': False,
            'error': error_msg or 'Failed to send email. Please try again later or use screenshot/CSV method to contact us.'
        }), 500
