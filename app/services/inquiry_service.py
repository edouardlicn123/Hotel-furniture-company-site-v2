# app/services/inquiry_service.py
# Inquiry & Contact Core Service Layer - Professional English Version (2026-01-16)
# 更新內容：
# - 統一使用 timezone.utc 避免 naive/aware datetime 衝突
# - 自動區分純聯絡表單與帶商品詢價（主旨與標題不同）
# - 保持 attachments 支持（聯絡表單傳空列表時不附加）
# - 所有用戶提示全英文，專業禮貌
# - 日誌更詳細，便於除錯

import os
import logging
import mimetypes
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
from flask import current_app, session, request
from app.models import Settings, SmtpConfig
from app.utils.mail import send_email

logger = logging.getLogger(__name__)

# Constants
COOLDOWN_SECONDS = 120
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024      # 5MB per file
MAX_TOTAL_ATTACHMENTS_SIZE = 10 * 1024 * 1024  # 10MB total
LAST_INQUIRY_KEY = 'last_inquiry_time'


class InquiryService:
    @staticmethod
    def _check_cooldown() -> Tuple[bool, Optional[str]]:
        """Check cooldown (shared for inquiry & contact)"""
        last_time_str = session.get(LAST_INQUIRY_KEY)
        if last_time_str:
            try:
                last_time = datetime.fromisoformat(last_time_str)
                if last_time.tzinfo is None:
                    last_time = last_time.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                if now - last_time < timedelta(seconds=COOLDOWN_SECONDS):
                    remaining_sec = int(COOLDOWN_SECONDS - (now - last_time).total_seconds())
                    mins = (remaining_sec // 60) + 1 if remaining_sec % 60 else remaining_sec // 60
                    return False, f"Please wait approximately {mins} minute(s) before sending another message (server protection)."
            except Exception as e:
                logger.warning(f"Cooldown parsing error: {e}")
        return True, None

    @staticmethod
    def _update_cooldown():
        """Update cooldown timestamp (UTC)"""
        session[LAST_INQUIRY_KEY] = datetime.now(timezone.utc).isoformat()
        session.modified = True

    @staticmethod
    def _get_common_config() -> Tuple[Optional[Settings], Optional[SmtpConfig], Optional[str]]:
        """Get and validate common configuration"""
        settings = Settings.query.first()
        if not settings or not settings.email1:
            logger.error("Settings or recipient email not configured")
            return None, None, "Server configuration error: missing recipient email"

        smtp = SmtpConfig.query.first()
        if not smtp or not all([smtp.mail_server, smtp.mail_port, smtp.mail_username, smtp.mail_password]):
            logger.error("SMTP configuration incomplete")
            return None, None, "SMTP configuration incomplete"

        return settings, smtp, None

    @staticmethod
    def _validate_input(customer_info: Dict, is_inquiry: bool = True) -> Tuple[bool, Optional[str]]:
        """Basic input validation"""
        required = ['name', 'email']
        if is_inquiry:
            required.append('phone')  # 購物車詢價要求電話/WhatsApp

        for field in required:
            if not customer_info.get(field) or not str(customer_info[field]).strip():
                return False, f"Please provide your {field.capitalize()}"

        email = customer_info.get('email', '').strip()
        if '@' not in email or '.' not in email.split('@')[-1]:
            return False, "Please enter a valid email address"

        return True, None

    @staticmethod
    def _prepare_attachments(items: List[Dict]) -> Tuple[List[Dict], str]:
        """Prepare product main images as attachments (only when items exist)"""
        attachments = []
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
        total_size = 0
        attach_count = 0
        skipped = []

        for item in items:
            image_filename = item.get('image')
            if not image_filename:
                continue

            file_path = os.path.join(upload_folder, image_filename.strip())
            if not os.path.exists(file_path):
                skipped.append(image_filename)
                continue

            try:
                file_size = os.path.getsize(file_path)
                if file_size > MAX_ATTACHMENT_SIZE:
                    skipped.append(f"{image_filename} (file too large)")
                    continue

                if total_size + file_size > MAX_TOTAL_ATTACHMENTS_SIZE:
                    skipped.append(f"{image_filename} (total size limit exceeded)")
                    continue

                with open(file_path, 'rb') as f:
                    data = f.read()

                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'

                attachments.append({
                    'filename': image_filename,
                    'data': data,
                    'content_type': content_type
                })

                total_size += file_size
                attach_count += 1

            except Exception as e:
                logger.warning(f"Failed to read attachment {image_filename}: {e}")
                skipped.append(image_filename)

        desc = f"Product main images ({attach_count} attached"
        if skipped:
            desc += f", {len(skipped)} skipped due to size/error)"
        else:
            desc += ")"

        return attachments, desc

    @staticmethod
    def _build_inquiry_body_html(items: List[Dict], customer_info: Dict, settings, attach_desc: str) -> str:
        """HTML formatted email body (English)"""
        send_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        is_contact_only = len(items) == 0
        title = "New Contact Message" if is_contact_only else f"New Inquiry - {len(items)} Product{'s' if len(items) != 1 else ''}"

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, Helvetica, sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; }}
                h2 {{ color: #2c5282; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background: #2c5282; color: white; }}
                tr:nth-child(even) {{ background: #f8f9fa; }}
                .section {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h2>{title}</h2>
            
            <div class="section">
        """

        if not is_contact_only:
            html += """
                <h3>Requested Products</h3>
                <table>
                    <tr><th>#</th><th>Product Name</th><th>Code</th><th>Quantity</th></tr>
            """
            for idx, item in enumerate(items, 1):
                name = item.get('name', 'Unnamed Product')
                code = item.get('product_code', 'N/A')
                qty = item.get('quantity', 1)
                html += f"<tr><td>{idx}</td><td>{name}</td><td>{code}</td><td>{qty}</td></tr>"

            html += "</table></div><div class=\"section\">"

        html += f"""
                <strong>Customer Information:</strong><br>
                Name: {customer_info.get('name', 'Not provided')}<br>
                Email: {customer_info.get('email', 'Not provided')}<br>
                Phone/WhatsApp: {customer_info.get('phone', customer_info.get('whatsapp', 'Not provided'))}
            </div>

            <div class="section">
                <strong>Message:</strong><br>
                {customer_info.get('message', 'No message provided').replace('\n', '<br>')}
            </div>

            <div class="section">
                <strong>Additional Information:</strong><br>
                Subject: {customer_info.get('subject', 'General Inquiry')}<br>
                Sent at: {send_time}<br>
                IP Address: {request.remote_addr}<br>
                Website Mode: {getattr(settings, 'mode', 'official').title()}<br>
                {attach_desc if not is_contact_only else 'No attachments (contact form)'}
            </div>

            <p>Thank you for your message. Our team will contact you soon.</p>
        </body>
        </html>
        """

        return html

    @staticmethod
    def send_inquiry(items: List[Dict], customer_info: Dict) -> Tuple[bool, str]:
        """
        Send inquiry or contact email
        - items: empty list [] for pure contact form
        - Automatically handles subject/title difference
        """
        # 1. Cooldown & Basic Validation
        allowed, cooldown_msg = InquiryService._check_cooldown()
        if not allowed:
            return False, cooldown_msg

        is_inquiry = len(items) > 0
        valid, err = InquiryService._validate_input(customer_info, is_inquiry=is_inquiry)
        if not valid:
            return False, err

        settings, smtp, config_err = InquiryService._get_common_config()
        if config_err:
            return False, config_err

        # 2. Prepare content
        attachments, attach_desc = InquiryService._prepare_attachments(items)

        if len(items) == 0:
            subject = f"New Contact Message - {customer_info.get('subject', 'General Inquiry')}"
        else:
            subject = f"New Inquiry - {len(items)} Product{'s' if len(items) != 1 else ''} - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

        body = InquiryService._build_inquiry_body_html(items, customer_info, settings, attach_desc)
        recipient = settings.email1
        sender_name = settings.company_name or "Hotel Furniture Website"

        # 3. Send email
        success, msg = send_email(
            smtp_server=smtp.mail_server,
            smtp_port=smtp.mail_port,
            username=smtp.mail_username,
            password=smtp.mail_password,
            from_addr=smtp.mail_username,
            to_addr=recipient,
            subject=subject,
            body=body,
            is_html=True,
            use_ssl=smtp.mail_use_ssl,
            use_tls=smtp.mail_use_tls,
            sender_name=sender_name,
            attachments=attachments
        )

        if success:
            InquiryService._update_cooldown()
            logger.info(f"Email sent successfully → {recipient} | Type: {'Inquiry' if is_inquiry else 'Contact'} | Items: {len(items)} | IP: {request.remote_addr}")
            return True, "Your message has been sent successfully! We will get back to you soon."

        logger.error(f"Email failed: {msg}")
        return False, "Failed to send your message. Please try again later or contact us directly via email or WhatsApp."
