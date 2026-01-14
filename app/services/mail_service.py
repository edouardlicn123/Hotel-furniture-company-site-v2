# app/services/mail_service.py
# 邮件服务层 - 支持模板渲染、附件、统一错误处理（2026-01）

import logging
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail
from app.utils.mail import send_email  # 先保留原有低层发送函数，逐步替换

logger = logging.getLogger(__name__)

class MailService:
    @staticmethod
    def send_inquiry_email(to_addr: str, subject: str, template: str, attachments: list = None, **kwargs):
        """
        发送询价邮件（支持模板渲染 + 附件）
        template: 模板文件名，如 'inquiry_email.html'
        kwargs: 传给模板的变量
        attachments: [{'filename': 'xxx.jpg', 'data': bytes, 'content_type': 'image/jpeg'}]
        """
        try:
            # 渲染 HTML 正文
            html_body = render_template(f'emails/{template}', **kwargs)

            msg = Message(
                subject=subject,
                recipients=[to_addr],
                html=html_body,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )

            # 添加附件（产品图片）
            if attachments:
                for att in attachments:
                    msg.attach(
                        filename=att['filename'],
                        content_type=att.get('content_type', 'application/octet-stream'),
                        data=att['data']
                    )

            mail.send(msg)
            logger.info(f"询价邮件发送成功 → {to_addr} | 主题: {subject}")
            return True, "邮件发送成功"

        except Exception as e:
            logger.error(f"询价邮件发送失败: {str(e)}", exc_info=True)
            return False, str(e)

    @staticmethod
    def send_test_email(test_recipient: str):
        """保留原有测试功能，稍后可统一"""
        # 可复用原有 utils/mail.py 的 test_send_email
        pass
