# app/routes/cart.py
# 购物车询价路由 - 完整版（使用统一邮件发送工具 send_email）
# 2026-01-13 更新：迁移到 app/utils/mail.py，统一错误处理

from flask import Blueprint, request, jsonify, current_app
from app.models import Settings, SmtpConfig
from app.utils.mail import send_email
from datetime import datetime

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/send-inquiry', methods=['POST'])
def send_inquiry():
    """
    处理购物车询价请求并发送邮件
    - 前端提交 JSON 数据（items + 可选客户信息）
    - 使用统一 send_email 函数发送
    - 返回 JSON 响应给前端（用于 toast 提示）
    """
    try:
        data = request.get_json()
        if not data or not data.get('items'):
            return jsonify({
                'success': False,
                'message': 'No items in cart'
            }), 400

        # 获取网站设置（收件人邮箱、公司名称等）
        settings = Settings.query.first()
        if not settings:
            current_app.logger.error("Site settings not found")
            return jsonify({
                'success': False,
                'message': 'Site settings not configured'
            }), 500

        recipient = settings.email1
        if not recipient:
            current_app.logger.error("No recipient email configured in settings")
            return jsonify({
                'success': False,
                'message': 'No recipient email configured'
            }), 500

        # 获取 SMTP 配置
        smtp = SmtpConfig.query.first()
        if not smtp:
            current_app.logger.error("SMTP configuration not found")
            return jsonify({
                'success': False,
                'message': 'SMTP configuration not found'
            }), 500

        if not smtp.mail_username or not smtp.mail_password:
            current_app.logger.error("SMTP credentials incomplete")
            return jsonify({
                'success': False,
                'message': 'SMTP credentials not configured'
            }), 500

        # 构造邮件主题和正文（正文用中文，面向运营团队）
        items = data['items']
        customer_email = data.get('customer_email', '未提供')
        customer_name = data.get('customer_name', '未提供')
        customer_phone = data.get('customer_phone', '未提供')
        customer_message = data.get('message', '').strip()

        subject = f"新的产品询价 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        body = f"""尊敬的销售团队，

客户提交了以下产品询价：

"""
        for idx, item in enumerate(items, 1):
            body += f"{idx}. {item.get('name', '未命名产品')} (编号: {item.get('code', 'N/A')})\n"
            if item.get('quantity'):
                body += f"   数量：{item.get('quantity')}\n"
            body += "\n"

        body += f"""客户联系方式：
- 姓名：{customer_name}
- 邮箱：{customer_email}
- 电话：{customer_phone}

客户留言：
{customer_message if customer_message else '无'}

发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请尽快跟进，谢谢！
"""

        # 发送邮件（使用统一工具函数）
        success, msg = send_email(
            smtp_server=smtp.mail_server,
            smtp_port=smtp.mail_port,
            username=smtp.mail_username,
            password=smtp.mail_password,
            from_addr=smtp.mail_username,
            to_addr=recipient,
            subject=subject,
            body=body,
            is_html=False,
            use_ssl=smtp.mail_use_ssl,
            use_tls=smtp.mail_use_tls,
            sender_name=settings.company_name or "Hotel Furniture Website"
        )

        if success:
            current_app.logger.info(f"Inquiry email sent successfully to {recipient}")
            return jsonify({
                'success': True,
                'message': 'Inquiry sent successfully! We will reply soon.'
            })

        else:
            current_app.logger.error(f"Inquiry email failed: {msg}")
            return jsonify({
                'success': False,
                'message': 'Failed to send inquiry. Please try again later or contact us directly.'
            }), 500

    except Exception as e:
        current_app.logger.exception("Unexpected error in cart inquiry")
        return jsonify({
            'success': False,
            'message': 'Server error occurred. Please try again later.'
        }), 500
