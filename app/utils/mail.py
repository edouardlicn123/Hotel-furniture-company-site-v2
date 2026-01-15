# app/utils/mail.py - 还原纯 smtplib 版本（无 multipart，兼容性最高）

import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from typing import Tuple

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
    max_retries: int = 3,
    initial_delay: float = 2.0
) -> Tuple[bool, str]:
    """
    还原版：纯 MIMEText 发送，兼容性最高（无 multipart）
    支持后端冷却、重试、日志
    """
    # 后端冷却（保持不变）
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
                logger.warning(f"邮件发送被冷却限制 | IP: {request.remote_addr} | 剩余约 {remaining_min} 分钟")
                return False, f"Please wait approximately {remaining_min} minute(s) before sending another message."
        except Exception:
            logger.warning("冷却时间解析失败，已忽略")
            pass

    # 配置校验
    if not all([smtp_server, smtp_port, username, password, from_addr, to_addr]):
        logger.error("SMTP 配置不完整")
        return False, "Incomplete SMTP configuration"

    subtype = 'html' if is_html else 'plain'
    msg = MIMEText(body, subtype, 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), from_addr))
    msg['To'] = to_addr

    for attempt in range(1, max_retries + 1):
        server = None
        try:
            logger.info(f"尝试连接 SMTP: {smtp_server}:{smtp_port} | SSL: {use_ssl} | TLS: {use_tls}")

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

            logger.info(f"邮件发送成功 → {to_addr} | 主题: {subject}")

            session[LAST_SEND_KEY] = now.isoformat()
            session.modified = True

            return True, "Email sent successfully"

        except Exception as e:
            err_msg = f"发送失败 (尝试 {attempt}/{max_retries}): {str(e)}"
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
