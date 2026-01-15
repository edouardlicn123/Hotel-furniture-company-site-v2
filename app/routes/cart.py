# app/routes/cart.py
# 购物车询价路由 - 极薄路由层（2026-01-15 最终强化版）
# 职责：仅负责接收请求、基本校验、调用服务层、返回标准 JSON
# 所有业务逻辑（邮件发送、冷却、格式化等）均已移至 inquiry_service.py

from flask import Blueprint, request, jsonify, current_app, render_template
from app.services.inquiry_service import InquiryService

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/send-inquiry', methods=['POST'])
def send_inquiry():
    """
    处理在线购物车询价请求（薄路由层）
    
    预期请求格式（JSON）：
    {
        "items": [
            {"product_code": "pc123456789", "name": "Deluxe King Bed", "quantity": 2},
            ...
        ],
        "customer_info": {
            "name": "张先生",
            "email": "zhang@example.com",
            "phone": "+8613812345678",
            "company": "XX酒店设计公司",      // 可选
            "message": "需要尽快报价，项目位于上海"  // 可选
        }
    }
    
    返回格式：
    成功： { "success": true, "message": "..." }
    失败： { "success": false, "message": "具体原因" }
    """
    try:
        # 强制解析 JSON，兼容 Content-Type 缺失或异常情况
        data = request.get_json(force=True)

        if not data:
            return jsonify({
                'success': False,
                'message': '请求体中未包含有效的 JSON 数据'
            }), 400

        # 1. 校验 items
        items = data.get('items')
        if not items or not isinstance(items, list) or len(items) == 0:
            return jsonify({
                'success': False,
                'message': 'items 字段必须是非空数组'
            }), 400

        # 2. 校验 customer_info
        customer_info = data.get('customer_info')
        if not customer_info or not isinstance(customer_info, dict):
            return jsonify({
                'success': False,
                'message': 'customer_info 必须是一个对象'
            }), 400

        # 最基本必填字段校验（更细致的校验放在 service 层）
        required_fields = ['name', 'email']
        missing = [f for f in required_fields if not customer_info.get(f)]
        if missing:
            return jsonify({
                'success': False,
                'message': f"customer_info 缺少必填字段：{', '.join(missing)}"
            }), 400

        # 3. 调用服务层执行核心逻辑（邮件发送、冷却检查等）
        success, message = InquiryService.send_inquiry(
            items=items,
            customer_info=customer_info
        )

        if success:
            return jsonify({
                'success': True,
                'message': message or '询价已成功发送，我们将尽快与您联系！'
            })

        else:
            # 根据消息内容智能判断状态码
            if any(word in message.lower() for word in ['wait', 'cooldown', 'please wait', '冷却', '请稍后']):
                status_code = 429
            else:
                status_code = 400 if 'invalid' in message.lower() or '缺少' in message else 500

            current_app.logger.warning(f"询价失败: {message}")
            return jsonify({
                'success': False,
                'message': message
            }), status_code

    except ValueError as ve:
        # JSON 解析失败
        current_app.logger.warning(f"JSON 解析失败: {str(ve)}")
        return jsonify({
            'success': False,
            'message': '请求的 JSON 格式无效，请检查数据结构'
        }), 400

    except Exception as e:
        current_app.logger.exception("处理询价请求时发生意外错误")
        return jsonify({
            'success': False,
            'message': '服务器内部错误，请稍后重试或联系管理员'
        }), 500


# 在线询价车页面（GET）
@cart_bp.route('/onlinecart')
def online_cart():
    """顯示在线询价车页面"""
    from app.models import Settings
    settings = Settings.query.first() or Settings()  # 防止 None
    return render_template('cart/onlinecart.html', settings=settings)


# 离线选货清单页面（GET）
@cart_bp.route('/offlinecart')
def offline_cart():
    """显示离线选货清单页面"""
    return render_template('cart/offlinecart.html')


