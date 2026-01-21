# app/utils/mail.py - 2026-01-20 超級穩定版（強制 utf-8 bytes 序列化，徹底解決 ascii codec 錯誤）

import smtplib
import time
import logging
from typing import List, Dict, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from email.utils import formataddr
from email import encoders  # 用來強制編碼

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
    body: str | bytes,
    is_html: bool = False,
    use_ssl: bool = False,
    use_tls: bool = True,
    sender_name: str = "Hotel Furniture Website",
    attachments: List[Dict[str, str]] = None,
    max_retries: int = 3,
    initial_delay: float = 2.0
) -> Tuple[bool, str]:
    """
    使用標準庫 smtplib 發送郵件，強制所有內容 utf-8 bytes 序列化
    徹底避免 'ascii' codec 錯誤，完美兼容 163 郵箱中文
    """
    # 冷卻機制
    COOLDOWN_SECONDS = 120
    LAST_SEND_KEY = 'last_email_send_time'

    now = datetime.utcnow()
    last_send_str = session.get(LAST_SEND_KEY)
    if last_send_str:
        try:
            last_send = datetime.fromisoformat(last_send_str)
            if (now - last_send) < timedelta(seconds=COOLDOWN_SECONDS):
                remaining_sec = int(COOLDOWN_SECONDS - (now - last_send).total_seconds())
                remaining_min = (remaining_sec // 60) + (1 if remaining_sec % 60 else 0)
                logger.warning(f"Email cooldown active | IP: {request.remote_addr} | Wait ~{remaining_min} min")
                return False, f"請等待約 {remaining_min} 分鐘後再發送"
        except Exception:
            pass

    # 配置校驗
    if not all([smtp_server, smtp_port, username, password, from_addr, to_addr]):
        logger.error("SMTP 配置不完整")
        return False, "SMTP 配置不完整，請檢查後台"

    # 附件處理
    processed_attachments = []
    attachments = attachments or []
    for attach in attachments:
        filename = attach.get('filename')
        data = attach.get('data')
        if filename and data:
            if isinstance(data, str):
                data = data.encode('utf-8')
            processed_attachments.append((filename, data))

    # 163 郵箱：465 端口強制 SSL
    use_ssl = use_ssl or (smtp_port == 465)
    use_tls = use_tls and not use_ssl

    # 構建 MIME 郵件
    msg = MIMEMultipart()
    msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), from_addr))
    msg['To'] = to_addr
    msg['Subject'] = Header(subject, 'utf-8')

    # 正文
    if isinstance(body, bytes):
        body = body.decode('utf-8', 'replace')

    if is_html:
        if '<meta charset' not in body.lower():
            body = '<meta charset="utf-8">\n' + body
        msg.attach(MIMEText(body, 'html', 'utf-8'))
    else:
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # 附件
    for filename, data in processed_attachments:
        part = MIMEApplication(data)
        part.add_header('Content-Disposition', 'attachment', filename=str(Header(filename, 'utf-8')))
        msg.attach(part)

    # 【關鍵修復】強制把整個 msg 轉成 utf-8 bytes，避免 ascii 干預
    try:
        msg_bytes = msg.as_bytes(policy=None)  # 使用 as_bytes() 而非 as_string()
        if not isinstance(msg_bytes, bytes):
            msg_bytes = msg_bytes.encode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"msg 序列化失敗: {str(e)}")
        return False, f"郵件內容序列化失敗: {str(e)}"

    # 發送重試
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"嘗試 {attempt}/{max_retries}：連接 {smtp_server}:{smtp_port} | "
                        f"From: {msg['From']} | Subject: {msg['Subject']}")

            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
                if use_tls:
                    server.starttls()

            server.login(username, password)
            server.sendmail(from_addr, to_addr, msg_bytes)  # 使用 bytes 版本！
            server.quit()

            logger.info(f"郵件發送成功 → {to_addr}")

            session[LAST_SEND_KEY] = now.isoformat()
            session.modified = True
            return True, "郵件發送成功"

        except Exception as e:
            err_msg = f"發送失敗 (嘗試 {attempt}/{max_retries}): {str(e)}"
            logger.warning(err_msg)

            if attempt == max_retries:
                return False, f"經過 {max_retries} 次重試後發送失敗：{str(e)}"

            time.sleep(initial_delay * (2 ** (attempt - 1)))

    return False, "所有重試均失敗"
