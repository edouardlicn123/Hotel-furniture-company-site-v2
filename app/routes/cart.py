# app/routes/cart.py
# 购物车询价邮件发送 - 更新版（使用统一的 app.utils.mail.send_email 函数）
# 邮件正文为中文，无产品图片链接

from flask import Blueprint, request, jsonify, current_app
from app.models import Settings, SmtpConfig
from datetime import datetime
from app.utils.mail import send_email  # 已新建的统一邮件发送函数

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/send-inquiry', methods=['POST'])
def send_inquiry():
    """
    处理购物车询价请求并发送邮件
    - 使用 /admin/smtp 配置
    - 不保存到数据库
    - 邮件正文为中文，无产品图片链接
    """
    try:
        data = request.get_json()
        if not data or not data.get('items'):
            return jsonify({'success': False, 'message': 'No items in cart'}), 400

        # 获取站点设置（收件人 + 发送者名称）
        settings = Settings.query.first()
        if not settings:
            return jsonify({'success': False, 'message': 'Site settings not found'}), 500

        recipient = settings.email1
        if not recipient:
            return jsonify({'success': False, 'message': 'No recipient email configured. Please set email1 in admin settings'}), 500

        sender_name = settings.company_name or "Hotel Furniture Website"

        # 获取 SMTP 配置
        smtp = SmtpConfig.query.first()
        if not smtp:
            return jsonify({'success': False, 'message': 'SMTP configuration not found. Please set it up in /admin/smtp'}), 500

        if not smtp.mail_username or not smtp.mail_password:
            return jsonify({'success': False, 'message': 'SMTP configuration missing username or password'}), 500

        # 构建邮件主题和正文（中文）
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

        current_app.logger.info(f"Cart inquiry: Sending to {recipient} | Subject: {subject}")

        # 使用统一的 send_email 函数发送
        success, msg = send_email(
            smtp_server=smtp.mail_server,
            smtp_port=smtp.mail_port,
            username=smtp.mail_username,
            password=smtp.mail_password,  # 后续可考虑加密存储
            from_addr=smtp.mail_username,
            to_addr=recipient,
            subject=subject,
            body=body,
            is_html=False,
            use_ssl=smtp.mail_use_ssl,
            use_tls=smtp.mail_use_tls,
            sender_name=sender_name
        )

        if success:
            current_app.logger.info(f"Cart inquiry email sent successfully to {recipient} ({len(data['items'])} items)")
            return jsonify({
                'success': True,
                'message': 'Inquiry sent successfully! We will contact you soon.'
            }), 200

        current_app.logger.error(f"Cart inquiry email failed: {msg}")
        return jsonify({
            'success': False,
            'message': msg or 'Failed to send email. Please try again later or use screenshot/CSV method.'
        }), 500

    except Exception as e:
        error_msg = str(e)
        full_trace = traceback.format_exc()
        current_app.logger.error(f"Cart inquiry unexpected error: {error_msg}\n{full_trace}")
        return jsonify({
            'success': False,
            'message': 'Server error. Please try again later.'
        }), 500
