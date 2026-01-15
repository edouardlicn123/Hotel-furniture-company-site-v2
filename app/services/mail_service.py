# app/services/mail_service.py
# 邮件服务层 - 生产级统一版本（2026-01-15 更新）
# 主要功能：
# - 使用 Flask-Mail 发送，支持 HTML 模板 + 附件
# - 支持重试机制（默认 3 次）
# - 支持多收件人（主 + CC）
# - 统一日志 + 错误处理
# - 与 inquiry_service 完美对接（attachments 格式一致）
# - 提供测试邮件功能

import logging
import time
from typing import List, Dict, Tuple, Optional
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)

# 配置常量
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2  # 秒


class MailService:
    @staticmethod
    def _send_with_retry(msg: Message, retry_count: int = DEFAULT_RETRY_COUNT) -> Tuple[bool, str]:
        """
        带重试的底层发送函数
        返回: (success: bool, message: str)
        """
        last_exception = None

        for attempt in range(1, retry_count + 1):
            try:
                mail.send(msg)
                logger.info(f"邮件发送成功 → {', '.join(msg.recipients)} | 主题: {msg.subject} | 尝试 {attempt}/{retry_count}")
                return True, "Email sent successfully"

            except Exception as e:
                last_exception = e
                logger.warning(f"邮件发送失败（尝试 {attempt}/{retry_count}）：{str(e)}")
                if attempt < retry_count:
                    time.sleep(DEFAULT_RETRY_DELAY * (attempt ** 1.5))  # 指数退避

        error_msg = f"Failed to send email after {retry_count} attempts: {str(last_exception)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

    @classmethod
    def send_email(
        cls,
        to_addr: str | List[str],
        subject: str,
        template: str,
        context: Dict = None,
        cc: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None,
        sender_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        通用邮件发送接口（推荐使用）

        参数:
        - to_addr: 主收件人（字符串或列表）
        - subject: 邮件主题
        - template: 模板文件名（不含路径，如 'inquiry.html'）
        - context: 模板渲染变量（dict）
        - cc: 抄送列表（可选）
        - attachments: [{'filename': str, 'data': bytes, 'content_type': str}, ...]
        - sender_name: 发件人名称（可选，覆盖配置）

        返回: (success: bool, message: str)
        """
        try:
            # 准备收件人
            recipients = [to_addr] if isinstance(to_addr, str) else to_addr
            if not recipients:
                return False, "No recipients provided"

            # 渲染 HTML 正文
            template_path = f"emails/{template}"
            html_body = render_template(template_path, **(context or {}))

            # 创建消息
            msg = Message(
                subject=subject,
                recipients=recipients,
                html=html_body,
                sender=sender_name or current_app.config.get('MAIL_DEFAULT_SENDER')
            )

            # 抄送
            if cc:
                msg.cc = cc

            # 添加附件
            if attachments:
                for att in attachments:
                    filename = att.get('filename')
                    data = att.get('data')
                    content_type = att.get('content_type', 'application/octet-stream')

                    if filename and data:
                        msg.attach(filename=filename, content_type=content_type, data=data)
                    else:
                        logger.warning(f"无效附件跳过: {filename}")

            # 发送（带重试）
            return cls._send_with_retry(msg)

        except Exception as e:
            error_msg = f"邮件准备/发送异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    @classmethod
    def send_inquiry_email(
        cls,
        to_addr: str,
        items: List[Dict],
        customer_info: Dict,
        attachments: List[Dict],
        cc: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """专门用于询价邮件（与 inquiry_service 配合）"""
        subject = f"New Inquiry - {len(items)} Product{'s' if len(items) != 1 else ''} - {time.strftime('%Y-%m-%d')}"

        context = {
            'items': items,
            'customer_info': customer_info,
            'attachment_count': len(attachments),
            'send_time': time.strftime('%Y-%m-%d %H:%M:%S UTC')
        }

        return cls.send_email(
            to_addr=to_addr,
            subject=subject,
            template='inquiry.html',
            context=context,
            attachments=attachments,
            cc=cc
        )

    @classmethod
    def send_contact_email(
        cls,
        to_addr: str,
        customer_info: Dict,
        cc: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """专门用于联系留言邮件"""
        subject = f"Website Contact - {customer_info.get('subject', 'General Inquiry')} - {customer_info.get('name', 'Customer')}"

        context = {
            'customer_info': customer_info,
            'send_time': time.strftime('%Y-%m-%d %H:%M:%S UTC')
        }

        return cls.send_email(
            to_addr=to_addr,
            subject=subject,
            template='contact.html',
            context=context,
            cc=cc
        )

    @staticmethod
    def send_test_email(test_recipient: str, sender_name: Optional[str] = None) -> Tuple[bool, str]:
        """发送测试邮件（用于后台 SMTP 配置测试）"""
        subject = f"SMTP Test - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        context = {
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'recipient': test_recipient
        }

        return MailService.send_email(
            to_addr=test_recipient,
            subject=subject,
            template='test_email.html',
            context=context,
            sender_name=sender_name
        )
