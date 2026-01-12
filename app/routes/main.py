# app/routes/main.py - 完整最新版（2026-01-12 更新）
# 包含：SEO 统一注入、模式切换、全局联系信息注入、专题系列首页随机展示
# 新增：联系页表单邮件发送路由 /contact/send（使用 smtplib，与 cart.py 一致）
# 修复：确保 import random；移除错误的 app.context_processor 注册

from flask import Blueprint, render_template, request, url_for, jsonify, current_app
from app.models import Settings, FeatureSeries, Product, SmtpConfig
from sqlalchemy import or_
from datetime import datetime
import random  # 确保导入 random
import smtplib
from email.mime.text import MIMEText
import base64
import traceback

main_bp = Blueprint('main', __name__)

# ====================== 全局上下文处理器（注入所有模板需要的变量） ======================
def inject_seo_data():
    settings = Settings.query.first()
    
    # 数据库为空时的安全默认值
    if not settings:
        company_name = 'XX Hotel Furniture Manufacturer'
        theme = 'default'
        mode = 'official'
        company_logo_url = None
        page_og_image = None
        
        basic_info = company_advantages = address = None
        phone1 = phone2 = phone3 = email1 = email2 = email3 = fax = None
        whatsapp1 = whatsapp2 = wechat1 = wechat2 = None
        
        current_title = f'Home - Premium Hotel Furniture | {company_name}'
        current_description = 'Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.'
        current_keywords = 'hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture'
    else:
        company_name = settings.company_name or 'XX Hotel Furniture Manufacturer'
        theme = settings.theme or 'default'
        mode = settings.mode or 'official'
        company_logo_url = url_for('static', filename='uploads/logo/company_logo') if settings.logo else None
        page_og_image = None

        # 动态内容注入
        basic_info = settings.basic_info
        company_advantages = settings.company_advantages
        phone1 = settings.phone1
        phone2 = settings.phone2
        phone3 = settings.phone3
        email1 = settings.email1
        email2 = settings.email2
        email3 = settings.email3
        fax = settings.fax
        address = settings.address
        whatsapp1 = settings.whatsapp1
        whatsapp2 = settings.whatsapp2
        wechat1 = settings.wechat1
        wechat2 = settings.wechat2

        # 页面特定 SEO
        endpoint = request.endpoint or ''

        if endpoint == 'main.index':
            current_title = (settings.seo_home_title or 'Home - Premium Hotel Furniture | {company_name}').format(company_name=company_name)
            current_description = settings.seo_home_description or 'Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.'
            current_keywords = settings.seo_home_keywords or 'hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture'

        elif endpoint.startswith('products.'):
            current_title = (settings.seo_products_title or 'Products | {company_name}').format(company_name=company_name)
            current_description = settings.seo_products_description or 'Explore our complete collection of premium hotel furniture including beds, nightstands, sofas, wardrobes and custom case goods for luxury hospitality projects.'
            current_keywords = settings.seo_products_keywords or 'hotel furniture products, hotel beds, hotel sofas, hotel wardrobes, luxury hotel furniture collection'

        elif endpoint == 'main.about':
            current_title = (settings.seo_about_title or 'About Us - {company_name} | Leading Hotel Furniture Manufacturer').format(company_name=company_name)
            current_description = settings.seo_about_description or 'Learn about {company_name}, a professional hotel furniture manufacturer with years of experience in custom hospitality furniture design and production.'
            current_keywords = 'about hotel furniture manufacturer, hospitality furniture company, custom hotel furniture supplier'

        elif endpoint == 'main.contact':
            current_title = (settings.seo_contact_title or 'Contact Us - {company_name} | Hotel Furniture Inquiry').format(company_name=company_name)
            current_description = settings.seo_contact_description or 'Contact {company_name} for custom hotel furniture solutions, quotes, and partnership opportunities.'
            current_keywords = 'contact hotel furniture manufacturer, hotel furniture quote, hospitality furniture supplier'

        elif endpoint == 'series.list':
            current_title = f"Hotel Furniture Series & Collections - {company_name}"
            current_description = f"Explore our curated hotel furniture series and collections designed for luxury hospitality projects at {company_name}."
            current_keywords = "hotel furniture series, luxury hotel collections, hospitality design series, custom hotel furniture sets"

        elif endpoint == 'series.detail':
            slug = request.view_args.get('slug')
            series = FeatureSeries.query.filter_by(slug=slug).first() if slug else None
            if series:
                current_title = series.seo_title or f"{series.name} - Premium Hotel Furniture Series | {company_name}"
                current_description = series.seo_description or (series.description[:157] + "..." if series.description and len(series.description) > 160 else f"Discover the {series.name} series by {company_name}.")
                current_keywords = series.seo_keywords or "hotel furniture series, luxury hospitality design, custom hotel furniture collection"
                if series.photos:
                    first_photo = series.photos.split(',')[0].strip()
                    page_og_image = url_for('static', filename=f'uploads/series/{first_photo}', _external=True)
            else:
                current_title = f"Series - {company_name}"
                current_description = "View our premium hotel furniture collections."
                current_keywords = "hotel furniture series"

        elif endpoint == 'main.cart':
            current_title = f"My Inquiry Cart - {company_name}"
            current_description = f"Review your selected hotel furniture products for quotation at {company_name}."
            current_keywords = "hotel furniture inquiry cart, quotation list, product selection, custom furniture quote"

        else:
            current_title = f'{company_name} | Professional Hotel Furniture Manufacturer'
            current_description = 'Premium hotel furniture solutions for luxury hospitality projects worldwide.'
            current_keywords = 'hotel furniture, custom hotel furniture, luxury hospitality furniture'

    return dict(
        company_name=company_name,
        page_title=current_title,
        page_description=current_description,
        page_keywords=current_keywords,
        company_logo_url=company_logo_url,
        theme=theme,
        page_og_image=page_og_image,
        mode=mode,
        basic_info=basic_info,
        company_advantages=company_advantages,
        phone1=phone1, phone2=phone2, phone3=phone3,
        email1=email1, email2=email2, email3=email3,
        fax=fax,
        address=address,
        whatsapp1=whatsapp1, whatsapp2=whatsapp2,
        wechat1=wechat1, wechat2=wechat2,
        current_year=datetime.now().strftime('%Y')
    )

# 注意：上下文处理器应在 __init__.py 的 create_app() 中注册：
# app.context_processor(inject_seo_data)

# ====================== 路由定义 ======================

@main_bp.route('/')
def index():
    """首页 - 随机展示最多 3 个有产品的专题系列"""
    all_series = FeatureSeries.query.order_by(FeatureSeries.created_at.desc()).all()
    
    valid_series = [
        series for series in all_series
        if Product.query.filter(
            or_(
                Product.featured_series == series.slug,
                Product.featured_series.like(f'{series.slug},%'),
                Product.featured_series.like(f'%,{series.slug}'),
                Product.featured_series.like(f'%,{series.slug},%')
            )
        ).count() > 0
    ]
    
    featured_series_list = random.sample(valid_series, k=min(3, len(valid_series))) if valid_series else []
    random.shuffle(featured_series_list)
    
    return render_template('index.html', featured_series_list=featured_series_list)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/cart')
def cart():
    return render_template('cart.html')

# ====================== 新增：联系页表单邮件发送 ======================
@main_bp.route('/contact/send', methods=['POST'])
def contact_send():
    """
    处理联系页表单提交，使用 smtplib 发送邮件（与 cart.py 风格一致）
    """
    try:
        data = request.get_json()
        required_fields = ['name', 'email', 'subject', 'message']
        if not all(data.get(field) for field in required_fields):
            return jsonify({'error': 'Please fill in all required fields'}), 400

        settings = Settings.query.first()
        if not settings or not settings.email1:
            return jsonify({'error': 'Recipient email not configured'}), 500

        smtp = SmtpConfig.query.first()
        if not smtp or not smtp.mail_username or not smtp.mail_password:
            return jsonify({'error': 'SMTP configuration incomplete'}), 500

        # 邮件内容（中文）
        subject = f"网站联系表单新消息 - {data['subject']} ({data['email']})"

        body = f"""您好，收到新的联系消息：

客户信息：
- 姓名：{data['name']}
- 邮箱：{data['email']}
- WhatsApp：{data.get('whatsapp', '未提供')}
- 主题：{data['subject']}

消息内容：
{data['message']}

发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (香港时间)
备注：此为网站联系表单自动提交，请尽快回复客户。
"""

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = smtp.mail_username
        msg['To'] = settings.email1

        # 发送（与 cart.py 完全一致）
        if smtp.mail_use_ssl:
            server = smtplib.SMTP_SSL(smtp.mail_server, smtp.mail_port, timeout=20)
        else:
            server = smtplib.SMTP(smtp.mail_server, smtp.mail_port, timeout=20)
            if smtp.mail_use_tls:
                server.starttls()

        server.ehlo()
        server.docmd("AUTH LOGIN")
        server.docmd(base64.b64encode(smtp.mail_username.encode('utf-8')).decode('ascii'))
        server.docmd(base64.b64encode(smtp.mail_password.encode('utf-8')).decode('ascii'))

        server.send_message(msg)
        server.quit()

        current_app.logger.info(f"Contact form message sent to {settings.email1} from {data['email']}")

        return jsonify({
            'success': True,
            'message': 'Message sent successfully! We will contact you soon.'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Contact form send failed: {traceback.format_exc()}")
        return jsonify({
            'error': 'Failed to send message. Please try again later.'
        }), 500
