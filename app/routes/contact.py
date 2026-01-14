# app/routes/contact.py
# 联系页面路由 - 服务层重构版（2026-01-15）
# 更新内容：
# - 路由层大幅瘦身：仅负责接收请求、提取数据、调用 InquiryService、返回 JSON
# - 所有业务逻辑（冷却、校验、配置加载、正文构建、发送、日志）迁移到 InquiryService
# - 支持 JSON 和 form 提交
# - 与 cart 询价统一冷却机制（共享同一 session key，避免交叉刷）
# - 错误处理更统一

from flask import Blueprint, request, jsonify, current_app, render_template
from app.services.inquiry_service import InquiryService

contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

@contact_bp.route('/', methods=['GET'])
def contact_page():
    """GET: 显示联系页面（不变）"""
    return render_template('contact.html')


@contact_bp.route('/send', methods=['POST'])
def send_contact():
    """
    POST: 处理联系表单提交（薄路由层）
    - 支持 JSON 或 form 提交
    - 所有重逻辑交给 InquiryService.send_contact
    """
    try:
        # 支持 JSON 和 form
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict() or {}

        customer_info = {
            'name': data.get('name', '').strip(),
            'email': data.get('email', '').strip(),
            'whatsapp': data.get('whatsapp', '').strip(),
            'subject': data.get('subject', 'General Inquiry').strip(),
            'message': data.get('message', '').strip()
        }

        # 简单必填校验（详细校验交给 service）
        if not customer_info['name'] or not customer_info['email'] or not customer_info['message']:
            return jsonify({
                'success': False,
                'message': 'Name, Email and Message are required.'
            }), 400

        # 调用服务层统一处理
        success, message = InquiryService.send_contact(customer_info)

        if success:
            return jsonify({
                'success': True,
                'message': 'Your message has been sent successfully! We will reply soon.'
            })

        else:
            current_app.logger.warning(f"Contact form failed: {message}")
            return jsonify({
                'success': False,
                'message': message or 'Failed to send message. Please try again later.'
            }), 500 if 'Server' in message else 429  # 冷却返回 429

    except Exception as e:
        current_app.logger.exception("Unexpected error in contact/send")
        return jsonify({
            'success': False,
            'message': 'Server error occurred. Please try again later.'
        }), 500
