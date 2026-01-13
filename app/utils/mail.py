# app/utils/mail.py
# Unified email sending utility - Final version with language separation (2026-01-13)
# Normal business emails: English logs & messages
# SMTP test (admin): Chinese user-facing messages

import smtplib
import time
import logging
import base64
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from typing import Tuple

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
    Robust email sending for business use (English logs & messages)
    Returns: (success: bool, message: str)
    """
    if not all([smtp_server, smtp_port, username, password, from_addr, to_addr]):
        logger.error("Incomplete SMTP configuration")
        return False, "Incomplete SMTP configuration"

    subtype = 'html' if is_html else 'plain'
    msg = MIMEText(body, subtype, 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), from_addr))
    msg['To'] = to_addr

    for attempt in range(1, max_retries + 1):
        server = None
        try:
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
            return True, "Email sent successfully"

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False, "Authentication failed (username or password incorrect)"

        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipient refused: {str(e)}")
            return False, "Recipient address refused by server"

        except Exception as e:
            err_msg = f"Send failed (attempt {attempt}/{max_retries}): {str(e)}"
            logger.warning(err_msg)

            if attempt == max_retries:
                logger.exception("Email sending ultimately failed")
                return False, "Failed to send email after all retries"

            delay = initial_delay * (2 ** (attempt - 1))
            logger.info(f"Retrying in {delay:.1f} seconds...")
            time.sleep(delay)

        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass

    return False, "All retry attempts failed. Please check network or SMTP settings."


def test_send_email(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    use_ssl: bool = False,
    use_tls: bool = True,
    test_recipient: str = "",
    sender_name: str = "酒店家具官网测试"
) -> Tuple[bool, str]:
    """
    SMTP configuration test function (Chinese user-facing messages for admin)
    Returns: (success: bool, flash_message: str)
    """
    if not all([smtp_server, smtp_port, username, password, test_recipient]):
        return False, "测试参数不完整（缺少服务器/端口/用户名/密码/收件人）"

    test_subject = f"SMTP 配置测试 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
    test_body = (
        "这是一封测试邮件，用于验证您的 SMTP 配置是否正确。\n\n"
        f"发送时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "如果您收到此邮件，说明配置基本正常。\n"
        "请注意检查垃圾箱或促销邮件文件夹。"
    )

    msg = MIMEText(test_body, 'plain', 'utf-8')
    msg['Subject'] = Header(test_subject, 'utf-8')
    msg['From'] = username  # 强制纯邮箱地址，兼容严格服务商
    msg['To'] = test_recipient

    server = None
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=20)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()

        # 手动 AUTH LOGIN（最高兼容性）
        server.docmd("AUTH LOGIN")
        server.docmd(base64.b64encode(username.encode('utf-8')).decode('ascii'))
        server.docmd(base64.b64encode(password.encode('utf-8')).decode('ascii'))

        server.send_message(msg)
        server.quit()

        return True, f"测试邮件已成功发送至 {test_recipient}！请检查收件箱（或垃圾箱/促销邮件）。"

    except Exception as e:
        err_msg = f"测试发送失败：{str(e)}"
        logger.exception("SMTP 测试发送失败")
        return False, err_msg

    finally:
        if server:
            try:
                server.quit()
            except:
                pass
