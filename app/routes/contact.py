# app/routes/contact.py
# 聯絡頁面路由 - 服務層重構版（2026-01-16 修正版）
# 更新內容：
# - 使用現有的 InquiryService.send_inquiry([], customer_info) 處理聯絡表單
# - 支援 JSON 與 form 提交
# - 與購物車詢價共用冷卻機制
# - 錯誤處理統一

from flask import Blueprint, request, jsonify, current_app, render_template
from app.services.inquiry_service import InquiryService

contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

@contact_bp.route('/', methods=['GET'])
def contact_page():
    """GET: 顯示聯絡頁面"""
    return render_template('contact.html')


@contact_bp.route('/send', methods=['POST'])
def send_contact():
    """
    POST: 處理聯絡表單提交
    - 支援 JSON 或 form 提交
    - 使用 InquiryService.send_inquiry 處理（傳空 items 列表）
    """
    try:
        # 支援 JSON 與 form 提交
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict() or {}

        customer_info = {
            'name': data.get('name', '').strip(),
            'email': data.get('email', '').strip(),
            'whatsapp': data.get('whatsapp', '').strip(),  # 或 'phone'
            'subject': data.get('subject', 'General Inquiry').strip(),
            'message': data.get('message', '').strip()
        }

        # 簡單前端必填檢查（後端 service 會再嚴格驗證）
        if not customer_info['name'] or not customer_info['email'] or not customer_info['message']:
            return jsonify({
                'success': False,
                'message': 'Name, Email and Message are required.'
            }), 400

        # ★ 關鍵修正：使用現有 send_inquiry 方法，傳空商品列表 ★
        success, message = InquiryService.send_inquiry([], customer_info)

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
            }), 500 if 'Server' in message else 429  # 冷卻時建議回 429

    except Exception as e:
        current_app.logger.exception("Unexpected error in contact/send")
        return jsonify({
            'success': False,
            'message': 'Server error occurred. Please try again later.'
        }), 500
