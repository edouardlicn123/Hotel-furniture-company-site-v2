# app/routes/contact.py - 最終穩定版（2026-01-20）
# 聯絡頁面路由 - 直接使用 yagmail 版
# 更新內容：
# - 強制 body 使用 UTF-8 編碼處理（解決 'ascii' codec can't encode characters 錯誤）
# - 自動為 HTML body 添加 <meta charset="utf-8">（確保中文顯示）
# - 收件人優先 Settings.email1，fallback 到 SMTP username
# - 支援 JSON 與 form 提交
# - 錯誤處理統一，日志完善
# - 與購物車詢價共用同一冷卻機制

from flask import Blueprint, request, jsonify, current_app, render_template
from app.utils.mail import send_email
from app.models import SmtpConfig, Settings

contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

@contact_bp.route('/', methods=['GET'])
def contact_page():
    """GET: 顯示聯絡頁面"""
    return render_template('contact.html')


@contact_bp.route('/send', methods=['POST'])
def send_contact():
    """
    POST: 處理聯絡表單提交（一般詢價，不帶產品附件）
    - 直接使用最新的 yagmail 實現（含冷卻、重試、sender_name 支持）
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
            'phone': data.get('phone', '').strip() or data.get('whatsapp', '').strip(),
            'subject': data.get('subject', 'General Inquiry').strip(),
            'message': data.get('message', '').strip(),
            'company': data.get('company', '').strip()
        }

        # 必填欄位檢查
        if not customer_info['name'] or not customer_info['email'] or not customer_info['message']:
            return jsonify({
                'success': False,
                'message': 'Name, Email and Message are required.'
            }), 400

        # 獲取 SMTP 配置與網站設置
        smtp_config = SmtpConfig.query.first()
        settings = Settings.query.first() or Settings()

        if not smtp_config or not smtp_config.is_active:
            current_app.logger.error("SMTP config missing or inactive")
            return jsonify({
                'success': False,
                'message': 'Mail service not configured. Please contact administrator.'
            }), 500

        # 收件人：優先使用 Settings 中的業務郵箱，fallback 到 SMTP username
        to_addr = settings.email1 or smtp_config.mail_username
        if not to_addr:
            return jsonify({
                'success': False,
                'message': 'Recipient email not configured.'
            }), 500

        # 發件人信息
        from_addr = smtp_config.mail_username
        sender_name = smtp_config.default_sender_name or settings.company_name or 'Hotel Furniture Website'

        # 主題（允許中文）
        subject = f"Contact Form: {customer_info['subject']} - From {customer_info['name']}"

        # 郵件正文（純 Python 拼接 HTML）
        body_lines = [
            "<h2>New Contact Inquiry</h2>",
            f"<p><strong>Name:</strong> {customer_info['name']}</p>",
            f"<p><strong>Email:</strong> {customer_info['email']}</p>",
        ]

        if customer_info['phone']:
            body_lines.append(f"<p><strong>Phone/WhatsApp:</strong> {customer_info['phone']}</p>")

        if customer_info['company']:
            body_lines.append(f"<p><strong>Company:</strong> {customer_info['company']}</p>")

        body_lines.extend([
            f"<p><strong>Subject:</strong> {customer_info['subject']}</p>",
            "<hr>",
            "<p><strong>Message:</strong><br>" + customer_info['message'].replace('\n', '<br>') + "</p>",
            "<hr>",
            "<p><em>This message was sent from the website contact form.</em></p>"
        ])

        body_str = "\n".join(body_lines)

        # ★ 關鍵修復：強制轉換為 UTF-8 兼容字符串（解決 ASCII 編碼錯誤）
        body = body_str.encode('utf-8').decode('utf-8', 'replace')

        # 自動添加 charset meta（確保收件顯示中文）
        if '<meta charset' not in body.lower():
            body = '<meta charset="utf-8">\n' + body

        # 直接調用最新的 yagmail 實現（無附件）
        success, message = send_email(
            smtp_server=smtp_config.mail_server,
            smtp_port=smtp_config.mail_port,
            username=smtp_config.mail_username,
            password=smtp_config.mail_password,
            from_addr=from_addr,
            to_addr=to_addr,
            subject=subject,
            body=body,
            is_html=True,
            use_ssl=smtp_config.mail_use_ssl,
            use_tls=smtp_config.mail_use_tls,
            sender_name=sender_name,
            attachments=None  # contact 表單無附件
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Your message has been sent successfully! We will reply soon.'
            })

        else:
            current_app.logger.warning(f"Contact form send failed: {message}")
            return jsonify({
                'success': False,
                'message': message or 'Failed to send message. Please try again later.'
            }), 500 if 'Server' in str(message) else 429

    except Exception as e:
        current_app.logger.exception("Unexpected error in contact/send")
        return jsonify({
            'success': False,
            'message': 'Server error occurred. Please try again later.'
        }), 500
