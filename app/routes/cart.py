# app/routes/cart.py
# 购物车询价路由 - 服务层完整适配版（2026-01-15 最終強化版）
# 更新内容：
# - 路由层极简：仅接收、校验、调用 service、返回 JSON
# - force=True 兼容 Content-Type 异常
# - 详细错误响应（让前端显示具体原因）
# - 冷却错误返回 429，其他返回 500
# - 完整异常捕获 + 日志
# - 与 inquiry_service.py 完美兼容

from flask import Blueprint, request, jsonify, current_app
from app.services.inquiry_service import InquiryService

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/send-inquiry', methods=['POST'])
def send_inquiry():
    """
    处理购物车询价请求（薄路由层）
    前端提交 JSON 示例：
    {
        "items": [{"name": "...", "code": "...", "quantity": 1, "image": "xxx.jpg"}, ...],
        "customer_name": "...",
        "customer_email": "...",
        "customer_phone": "...",
        "customer_company": "...",  # 可选
        "message": "..."
    }
    """
    try:
        # 强制解析 JSON（兼容前端 Content-Type 不标准或缺失）
        data = request.get_json(force=True)

        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request: No JSON data received in body'
            }), 400

        # 提取 items
        items = data.get('items', [])
        if not items or not isinstance(items, list):
            return jsonify({
                'success': False,
                'message': 'Missing or invalid "items" field (must be a non-empty list)'
            }), 400

        # 提取 customer_info
        customer_info = data.get('customer_info', {})
        if not isinstance(customer_info, dict):
            return jsonify({
                'success': False,
                'message': '"customer_info" must be an object (dictionary)'
            }), 400

        # 简单必填校验（详细校验已在 service 层）
        if not customer_info.get('name') or not customer_info.get('email'):
            return jsonify({
                'success': False,
                'message': 'Name and Email are required in customer_info'
            }), 400

        # 调用服务层（传递 items 和 customer_info）
        success, message = InquiryService.send_inquiry(
            items=items,
            customer_info=customer_info
        )

        if success:
            return jsonify({
                'success': True,
                'message': message or 'Inquiry sent successfully! We will contact you soon.'
            })

        else:
            current_app.logger.warning(f"Inquiry failed: {message}")
            # 冷却错误返回 429，其他返回 500
            status_code = 429 if any(word in message.lower() for word in ["wait", "cooldown", "please wait"]) else 500
            return jsonify({
                'success': False,
                'message': message or 'Failed to send inquiry. Please try again later.'
            }), status_code

    except ValueError as ve:
        # JSON 解析失败（force=True 后仍可能出错）
        current_app.logger.warning(f"JSON parse error: {str(ve)}")
        return jsonify({
            'success': False,
            'message': 'Invalid JSON format in request body. Please check your data.'
        }), 400

    except Exception as e:
        current_app.logger.exception("Unexpected error in /cart/send-inquiry")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}. Please try again later.'
        }), 500
