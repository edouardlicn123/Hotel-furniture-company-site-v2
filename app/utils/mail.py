# app/utils/mail.py - Updated with Multipart/Attachment Support (2026-01-16)
# 更新內容：
# - 增加 attachments 支持（MIMEMultipart）
# - 當 attachments 為空時，自動降級回純 MIMEText（保持原有相容性）
# - 支援重試機制與詳細錯誤記錄
# - 所有提示英文專業
# - 保留後端冷卻機制（與原有相同）

import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.utils import formataddr
from typing import List, Dict, Tuple

from flask import session, current_app, request
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def send_email(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    is_html: bool = False,
    use_ssl: bool = False,
    use_tls: bool = True,
    sender_name: str = "Hotel Furniture Website",
    attachments: List[Dict[str, str]] = None,  # 新增：附件列表（每個 dict 含 'filename', 'data', 'content_type'）
    max_retries: int = 3,
    initial_delay: float = 2.0
) -> Tuple[bool, str]:
    """
    Send email with optional attachments (multipart support)
    - If attachments is None or empty, falls back to plain MIMEText
    """
    # 後端冷卻（保持不變）
    COOLDOWN_SECONDS = 120
    LAST_SEND_KEY = 'last_email_send_time'

    now = datetime.utcnow()

    last_send_str = session.get(LAST_SEND_KEY)
    if last_send_str:
        try:
            last_send = datetime.fromisoformat(last_send_str)
            time_diff = now - last_send
            if time_diff < timedelta(seconds=COOLDOWN_SECONDS):
                remaining_sec = int(COOLDOWN_SECONDS - time_diff.total_seconds())
                remaining_min = (remaining_sec // 60) + 1 if remaining_sec % 60 else remaining_sec // 60
                logger.warning(f"Email sending restricted by cooldown | IP: {request.remote_addr} | Remaining approx {remaining_min} minutes")
                return False, f"Please wait approximately {remaining_min} minute(s) before sending another message."
        except Exception:
            logger.warning("Cooldown time parsing failed, ignored")
            pass

    # 配置校驗
    if not all([smtp_server, smtp_port, username, password, from_addr, to_addr]):
        logger.error("SMTP configuration incomplete")
        return False, "Incomplete SMTP configuration"

    # 建構郵件
    attachments = attachments or []  # 確保不為 None

    if attachments:
        # 有附件：使用 MIMEMultipart
        msg = MIMEMultipart()
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), from_addr))
        msg['To'] = to_addr

        # 附加正文
        subtype = 'html' if is_html else 'plain'
        msg.attach(MIMEText(body, subtype, 'utf-8'))

        # 附加檔案
        for attach in attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attach['data'])
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={attach['filename']}")
            msg.attach(part)
    else:
        # 無附件：純 MIMEText（原有邏輯）
        subtype = 'html' if is_html else 'plain'
        msg = MIMEText(body, subtype, 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), from_addr))
        msg['To'] = to_addr

    for attempt in range(1, max_retries + 1):
        server = None
        try:
            logger.info(f"Attempting SMTP connection: {smtp_server}:{smtp_port} | SSL: {use_ssl} | TLS: {use_tls}")

            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
                server.ehlo()
                if use_tls:
                    server.starttls()
                    server.ehlo()

            server.login(username, password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent successfully → {to_addr} | Subject: {subject}")

            session[LAST_SEND_KEY] = now.isoformat()
            session.modified = True

            return True, "Email sent successfully"

        except Exception as e:
            err_msg = f"Send failed (attempt {attempt}/{max_retries}): {str(e)}"
            logger.warning(err_msg)

            if attempt == max_retries:
                return False, "Failed to send email after all retries"

            delay = initial_delay * (2 ** (attempt - 1))
            time.sleep(delay)

        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass

    return False, "All retry attempts failed."
