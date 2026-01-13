# app/utils/mail.py
import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from typing import Optional

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
    use_ssl: bool = False,          # True → SMTP_SSL (465端口常见), False → SMTP + starttls (587端口常见)
    sender_name: str = "酒店家具官网",
    max_retries: int = 3,
    initial_delay: float = 2.0
) -> tuple[bool, str]:
    """
    健壮版邮件发送函数
    返回: (success: bool, message: str)
    """
    if not all([smtp_server, smtp_port, username, password, from_addr, to_addr]):
        return False, "SMTP 配置不完整"

    # 准备邮件内容
    if is_html:
        msg = MIMEText(body, 'html', 'utf-8')
    else:
        msg = MIMEText(body, 'plain', 'utf-8')

    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), from_addr))
    msg['To'] = to_addr

    for attempt in range(1, max_retries + 1):
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
                server.ehlo()
                if not use_ssl:  # starttls 仅在非 SSL 模式下调用
                    server.starttls()
                    server.ehlo()

            # 登录（现代服务基本都支持这个标准方式）
            server.login(username, password)
            logger.info(f"SMTP 登录成功: {smtp_server}:{smtp_port} (尝试 {attempt})")

            server.send_message(msg)
            server.quit()

            logger.info(f"邮件发送成功 → {to_addr} | 主题: {subject}")
            return True, "发送成功"

        except smtplib.SMTPAuthenticationError as e:
            err_msg = f"认证失败（用户名/密码/授权码错误）: {str(e)}"
            logger.error(err_msg)
            return False, err_msg

        except smtplib.SMTPRecipientsRefused as e:
            err_msg = f"收件人被拒绝: {str(e)}"
            logger.error(err_msg)
            return False, err_msg

        except (smtplib.SMTPConnectError, OSError, ConnectionError) as e:
            err_msg = f"连接失败 (尝试 {attempt}/{max_retries}): {str(e)}"
            logger.warning(err_msg)
            if attempt < max_retries:
                delay = initial_delay * (2 ** (attempt - 1))  # 指数退避：2s → 4s → 8s
                logger.info(f"将在 {delay}s 后重试...")
                time.sleep(delay)
                continue
            return False, f"连接超时或网络问题（已重试 {max_retries} 次）"

        except Exception as e:
            err_msg = f"未知错误 (尝试 {attempt}): {str(e)}"
            logger.exception(err_msg)
            if attempt < max_retries:
                time.sleep(initial_delay * attempt)
                continue
            return False, err_msg

        finally:
            try:
                server.quit()
            except:
                pass
