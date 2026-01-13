# app/routes/cart.py
# Cart inquiry email sending - 使用标准 smtplib + 重试机制（2026-01-13 更新版）
# 已移除手动 AUTH LOGIN base64 方式，改用标准 login 方法
# 支持 SSL(465) 和 starttls(587)，邮件正文保持中文

from flask import Blueprint, request, jsonify, current_app
from app.models import Settings, SmtpConfig
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import traceback
import time

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/send-inquiry', methods=['POST'])
def send_inquiry():
    """
    处理购物车询价请求并通过 smtplib 发送邮件
    - 使用 /admin/smtp 中的配置
    - 不保存到数据库
    - 邮件正文为中文，无产品图片链接
    """
    try:
        data = request.get_json()
        if not data or not data.get('items'):
            return jsonify({'success': False, 'error': '购物车中没有商品'}), 400

        # 获取网站设置（收件邮箱 + 公司名称）
        settings = Settings.query.first()
        if not settings:
            return jsonify({'success': False, 'error': '网站设置未找到'}), 500

        recipient = settings.email1
        if not recipient:
            return jsonify({'success': False, 'error': '未配置收件邮箱，请在后台设置 email1'}), 500

        # 获取 SMTP 配置
        smtp = SmtpConfig.query.first()
        if not smtp:
            return jsonify({'success': False, 'error': 'SMTP 配置未找到，请在 /admin/smtp 设置'}), 500

        if not smtp.mail_username or not smtp.mail_password:
            return jsonify({'success': False, 'error': 'SMTP 配置缺少用户名或密码'}), 500

        # 构建邮件主题和正文（保持中文）
        subject = f"新的酒店家具询价 - {len(data['items'])} 件商品 ({data.get('email', '匿名用户')})"

        body = f"""您好，收到新的询价请求：

客户联系方式：
- 邮箱：{data.get('email', '未提供')}
- WhatsApp：{data.get('whatsapp', '未提供')}

请求商品列表：
"""
        for i, item in enumerate(data['items'], 1):
            body += f"{i}. {item['name']}（编号：{item['code']}）\n"

        body += f"""
发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (东八区)
备注：此为网站购物车自动提交的询价，请尽快联系客户跟进。
"""

        # 准备邮件对象
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        # 建议使用公司名称作为显示名，邮箱地址作为实际发件人
        msg['From'] = formataddr((str(Header(settings.company_name or "酒店家具官网", 'utf-8')), smtp.mail_username))
        msg['To'] = recipient

        # 发送参数
        server_config = {
            'host': smtp.mail_server,
            'port': smtp.mail_port,
            'use_ssl': smtp.mail_use_ssl,
            'use_tls': smtp.mail_use_tls,
            'username': smtp.mail_username,
            'password': smtp.mail_password,
        }

        print(f"\n★ [CART INQUIRY] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始发送...")
        print(f"★ 配置: Server={server_config['host']}, Port={server_config['port']}, "
              f"SSL={server_config['use_ssl']}, TLS={server_config['use_tls']}")
        print(f"★ 用户名: {server_config['username']}")
        print(f"★ 收件人: {recipient}")

        # 重试机制
        max_retries = 3
        success = False
        error_message = ""

        for attempt in range(1, max_retries + 1):
            server = None
            try:
                if server_config['use_ssl']:
                    server = smtplib.SMTP_SSL(server_config['host'], server_config['port'], timeout=20)
                else:
                    server = smtplib.SMTP(server_config['host'], server_config['port'], timeout=20)
                    server.ehlo()
                    if server_config['use_tls']:
                        server.starttls()
                        server.ehlo()

                print(f"★ 连接成功，正在登录 (尝试 {attempt}/{max_retries})...")
                server.login(server_config['username'], server_config['password'])
                print("★ 登录成功！")

                server.send_message(msg)
                server.quit()

                print("★ [CART INQUIRY] 发送成功！")
                current_app.logger.info(
                    f"询价邮件发送成功 → {recipient} ({len(data['items'])} 件商品)"
                )
                success = True
                break

            except smtplib.SMTPAuthenticationError:
                error_message = "SMTP 认证失败：用户名或密码（授权码）错误"
                print(f"★ {error_message}")
                break  # 认证错误无需重试

            except (smtplib.SMTPConnectError, ConnectionError, OSError) as e:
                error_message = f"连接失败: {str(e)}"
                print(f"★ {error_message} (尝试 {attempt})")
                if attempt < max_retries:
                    delay = 3 * attempt  # 3s → 6s → 9s
                    print(f"★ 等待 {delay} 秒后重试...")
                    time.sleep(delay)
                    continue

            except Exception as e:
                error_message = str(e)
                full_trace = traceback.format_exc()
                print(f"★ 发送失败 (尝试 {attempt}): {error_message}")
                print(f"★ 完整 traceback:\n{full_trace}")
                if attempt < max_retries:
                    time.sleep(3)
                    continue

            finally:
                if server:
                    try:
                        server.quit()
                    except:
                        pass

        if success:
            return jsonify({
                'success': True,
                'message': '询价已成功发送！我们会尽快与您联系。'
            }), 200
        else:
            current_app.logger.error(f"询价邮件发送失败: {error_message}\n{traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': error_message or '邮件发送失败，请稍后再试或直接联系我们。'
            }), 500

    except Exception as e:
        # 最外层兜底异常
        error_msg = str(e)
        full_trace = traceback.format_exc()
        current_app.logger.error(f"询价请求处理异常: {error_msg}\n{full_trace}")
        return jsonify({
            'success': False,
            'error': '系统错误，请稍后重试或直接联系我们'
        }), 500
