# app/utils/mail.py
# 统一邮件发送工具 - 当前稳定版（2026-01-13 更新）
# 支持 Gmail/QQ/163/Outlook 等常见 SMTP，支持重试、指数退避、详细日志
# 已兼容所有调用场景（cart.py, contact.py, admin/smtp.py）

import smtplib
import time
import logging
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
    use_ssl: bool = False,          # True → SMTP_SSL (常见 465 端口)
    use_tls: bool = True,           # True → 在 SMTP 后调用 starttls() (常见 587 端口)
    sender_name: str = "酒店家具官网",
    max_retries: int = 3,
    initial_delay: float = 2.0
) -> Tuple[bool, str]:
    """
    健壮版邮件发送函数
    返回: (success: bool, message: str)
    
    使用示例（兼容项目所有发送场景）：
    success, msg = send_email(
        smtp_server=smtp.mail_server,
        smtp_port=smtp.mail_port,
        username=smtp.mail_username,
        password=smtp.mail_password,
        from_addr=smtp.mail_username,
        to_addr=recipient,
        subject=mail_subject,
        body=mail_body,
        is_html=False,
        use_ssl=smtp.mail_use_ssl,
        use_tls=smtp.mail_use_tls,
        sender_name=sender_name
    )
    """
    if not all([smtp_server, smtp_port, username, password, from_addr, to_addr]):
        logger.error("SMTP 配置不完整，无法发送邮件")
        return False, "SMTP 配置不完整（缺少服务器/端口/用户名/密码/发件人/收件人）"

    # 准备邮件内容（支持中文主题/名称）
    if is_html:
        msg = MIMEText(body, 'html', 'utf-8')
    else:
        msg = MIMEText(body, 'plain', 'utf-8')

    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), from_addr))
    msg['To'] = to_addr

    server = None
    for attempt in range(1, max_retries + 1):
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
                server.ehlo()
                if use_tls:  # 根据 use_tls 参数决定是否升级 TLS
                    server.starttls()
                    server.ehlo()

            # 登录（标准方式，兼容绝大多数 SMTP 服务）
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
            if server is not None:
                try:
                    server.quit()
                except:
                    pass

    return False, "所有重试均失败，请检查网络或 SMTP 配置"
