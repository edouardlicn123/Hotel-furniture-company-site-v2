# app/services/inquiry_service.py
# 询价与联系核心服务层 - 统一完整版（2026-01-15）
# 更新内容：
# - 新增 send_contact 方法（纯联系留言，无购物车/附件）
# - 完全共享冷却、配置校验、日志、发送逻辑（最大复用）
# - 询价与联系正文更专业（区分场景，包含 IP、网站模式）
# - 修复：添加 import logging
# - 附件准备独立方法（仅询价使用）
# - 未来升级路径保留（Flask-Mail + HTML 模板）
# - 所有客户消息提交（询价/联系）统一服务化，后续扩展极易

import os
import logging
from datetime import datetime, timedelta
from flask import current_app, session, request
from app.models import Settings, SmtpConfig
from app.utils.mail import send_email  # 当前低层发送（支持附件 + 重试）

logger = logging.getLogger(__name__)

# 冷却配置（询价与联系共享，防止刷）
COOLDOWN_SECONDS = 120
LAST_INQUIRY_KEY = 'last_inquiry_time'


class InquiryService:
    @staticmethod
    def _check_cooldown() -> tuple[bool, str | None]:
        """统一后端冷却检查"""
        last_time_str = session.get(LAST_INQUIRY_KEY)
        if last_time_str:
            try:
                last_time = datetime.fromisoformat(last_time_str)
                if datetime.utcnow() - last_time < timedelta(seconds=COOLDOWN_SECONDS):
                    remaining = int(COOLDOWN_SECONDS - (datetime.utcnow() - last_time).total_seconds())
                    mins = (remaining // 60) + 1 if remaining % 60 else remaining // 60
                    return False, f"Please wait about {mins} minute(s) before sending another message (server protection)."
            except Exception:
                pass
        return True, None

    @staticmethod
    def _update_cooldown():
        """成功发送后更新冷却"""
        session[LAST_INQUIRY_KEY] = datetime.utcnow().isoformat()
        session.modified = True

    @staticmethod
    def _get_common_config() -> tuple[Settings | None, SmtpConfig | None, str | None]:
        """统一获取并校验配置"""
        settings = Settings.query.first()
        if not settings or not settings.email1:
            logger.error("Settings 或收件人邮箱未配置")
            return None, None, "Server configuration error (contact admin)"

        smtp = SmtpConfig.query.first()
        if not smtp or not smtp.mail_username or not smtp.mail_password:
            logger.error("SMTP 配置不完整")
            return None, None, "SMTP not configured"

        return settings, smtp, None

    @staticmethod
    def _prepare_attachments(items: list[dict]) -> list[dict]:
        """准备产品主图附件（仅询价使用）"""
        attachments = []
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'products')

        for item in items:
            image_filename = item.get('image')
            if not image_filename:
                continue
            file_path = os.path.join(upload_folder, image_filename.strip())
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        attachments.append({
                            'filename': image_filename,
                            'data': f.read(),
                            'content_type': 'image/jpeg'
                        })
                except Exception as e:
                    logger.warning(f"附件读取失败 {image_filename}: {e}")
            else:
                logger.warning(f"附件文件不存在: {file_path}")

        return attachments

    @staticmethod
    def _build_inquiry_body(items: list[dict], customer_info: dict, settings) -> str:
        """构建询价邮件正文"""
        send_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attachment_count = sum(1 for i in items if i.get('image'))

        body = f"""尊敬的销售团队，

有新的客户询价提交（共 {len(items)} 款产品）：

"""
        for idx, item in enumerate(items, 1):
            name = item.get('name', '未命名产品')
            code = item.get('code', 'N/A')
            qty = item.get('quantity', 1)
            body += f"{idx}. {name} (编号: {code})\n"
            if qty > 1:
                body += f"   数量: {qty}\n"
            body += "\n"

        body += f"""客户联系信息：
- 姓名：{customer_info.get('name', '未提供')}
- 邮箱：{customer_info.get('email', '未提供')}
- 电话：{customer_info.get('phone', '未提供')}
- 公司：{customer_info.get('company', '未提供')}

客户留言：
{customer_info.get('message') or '无'}

发送时间：{send_time}
来源IP：{request.remote_addr}
网站模式：{getattr(settings, 'mode', 'official').title()}
附件：产品主图（共 {attachment_count} 张）

请尽快联系客户跟进，谢谢！
"""
        return body

    @staticmethod
    def _build_contact_body(customer_info: dict, settings) -> str:
        """构建纯联系邮件正文"""
        send_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        body = f"""尊敬的销售团队，

收到新的网站联系留言：

----------------------------------------
客户姓名:   {customer_info.get('name', '未提供')}
邮箱地址:   {customer_info.get('email', '未提供')}
WhatsApp/电话: {customer_info.get('whatsapp') or '未提供'}
主题:       {customer_info.get('subject', 'General Inquiry')}
----------------------------------------
留言内容:
{customer_info.get('message', '无')}
----------------------------------------
提交时间:   {send_time}
来源IP:     {request.remote_addr}
网站模式：  {getattr(settings, 'mode', 'official').title()}
----------------------------------------
请尽快回复客户，谢谢！
"""
        return body

    @staticmethod
    def send_inquiry(items: list[dict], customer_info: dict) -> tuple[bool, str]:
        """发送购物车询价"""
        # 冷却 + 配置
        allowed, msg = InquiryService._check_cooldown()
        if not allowed:
            return False, msg

        settings, smtp, err = InquiryService._get_common_config()
        if err:
            return False, err

        recipient = settings.email1
        sender_name = settings.company_name or "Hotel Furniture Website"

        # 附件 + 正文
        attachments = InquiryService._prepare_attachments(items)
        subject = f"新的询价 - {len(items)} 款产品 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        body = InquiryService._build_inquiry_body(items, customer_info, settings)

        # 发送
        success, msg = send_email(
            smtp_server=smtp.mail_server,
            smtp_port=smtp.mail_port,
            username=smtp.mail_username,
            password=smtp.mail_password,
            from_addr=smtp.mail_username,
            to_addr=recipient,
            subject=subject,
            body=body,
            is_html=False,
            use_ssl=smtp.mail_use_ssl,
            use_tls=smtp.mail_use_tls,
            sender_name=sender_name
        )

        if success:
            InquiryService._update_cooldown()
            logger.info(f"询价邮件发送成功 → {recipient} | 产品数: {len(items)} | IP: {request.remote_addr}")
            return True, "Inquiry sent successfully!"

        logger.error(f"询价邮件发送失败: {msg}")
        return False, "Failed to send email. Please try again later or contact us directly."

    @staticmethod
    def send_contact(customer_info: dict) -> tuple[bool, str]:
        """发送纯联系留言"""
        # 冷却 + 配置（完全复用）
        allowed, msg = InquiryService._check_cooldown()
        if not allowed:
            return False, msg

        settings, smtp, err = InquiryService._get_common_config()
        if err:
            return False, err

        recipient = settings.email1
        sender_name = settings.company_name or "Hotel Furniture Website"

        # 无附件
        attachments = []

        # 正文
        subject = f"网站新留言 - {customer_info.get('subject', 'General Inquiry')} - {customer_info.get('name', 'Customer')}"
        body = InquiryService._build_contact_body(customer_info, settings)

        # 发送（复用同一工具）
        success, msg = send_email(
            smtp_server=smtp.mail_server,
            smtp_port=smtp.mail_port,
            username=smtp.mail_username,
            password=smtp.mail_password,
            from_addr=smtp.mail_username,
            to_addr=recipient,
            subject=subject,
            body=body,
            is_html=False,
            use_ssl=smtp.mail_use_ssl,
            use_tls=smtp.mail_use_tls,
            sender_name=sender_name
        )

        if success:
            InquiryService._update_cooldown()
            logger.info(f"联系留言发送成功 → {recipient} | From: {customer_info.get('name')} <{customer_info.get('email')}>")
            return True, "Message sent successfully!"

        logger.error(f"联系留言发送失败: {msg}")
        return False, "Failed to send message. Please try again later or contact us directly."
