# app/routes/cart.py
# 购物车询价路由 - 服务层完整适配版（2026-01-15）
# 更新内容：
# - 修复：调用正确的 InquiryService.send_inquiry() 方法（移除不存在的 send_inquiry_from_cart）
# - 路由层保持极简：仅接收数据、简单校验、调用 service、返回 JSON
# - 所有业务（冷却、附件、配置、正文、发送、日志）完全由 InquiryService 处理
# - 与最新 inquiry_service.py 完美兼容（send_inquiry + send_contact）

from flask import Blueprint, request, jsonify, current_app
from app.services.inquiry_service import InquiryService

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/send-inquiry', methods=['POST'])
def send_inquiry():
    """
    处理购物车询价请求（薄路由层）
    - 前端提交 JSON: {
        "items": [{"name": "...", "code": "...", "quantity": 1, "image": "xxx.jpg"}, ...],
        "customer_name": "...",
        "customer_email": "...",
        "customer_phone": "...",
        "customer_company": "...",  # 可选
        "message": "..."
      }
    """
    try:
        data = request.get_json(force=True)  # force=True 兼容 Content-Type 异常

        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400

        items = data.get('items', [])
        if not items:
            return jsonify({
                'success': False,
                'message': 'No items in cart'
            }), 400

        customer_info = {
            'name': data.get('customer_name', '').strip(),
            'email': data.get('customer_email', '').strip(),
            'phone': data.get('customer_phone', '').strip(),
            'company': data.get('customer_company', '').strip(),
            'message': data.get('message', '').strip()
        }

        # 可选简单必填校验（详细校验已在 service）
        if not customer_info['name'] or not customer_info['email']:
            return jsonify({
                'success': False,
                'message': 'Name and Email are required.'
            }), 400

        # 调用服务层（正确方法）
        success, message = InquiryService.send_inquiry(
            items=items,
            customer_info=customer_info
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Inquiry sent successfully! We will contact you soon.'
            })

        else:
            current_app.logger.warning(f"Inquiry failed: {message}")
            # 冷却错误返回 429，其他返回 500
            status_code = 429 if "wait" in message.lower() else 500
            return jsonify({
                'success': False,
                'message': message or 'Failed to send inquiry. Please try again later.'
            }), status_code

    except Exception as e:
        current_app.logger.exception("Unexpected error in cart/send-inquiry")
        return jsonify({
            'success': False,
            'message': 'Server error. Please try again later.'
        }), 500
