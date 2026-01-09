# app/routes/main.py - 完整最新版

from flask import Blueprint, render_template, request, url_for
from app.models import Settings, FeatureSeries, Product
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import random
from datetime import datetime  # 用于获取当前年份

db = SQLAlchemy()  # 实际已在 __init__.py 中全局定义，可保留

main_bp = Blueprint('main', __name__)

# ====================== 全局上下文处理器 ======================
def inject_seo_data():
    settings = Settings.query.first()
    if not settings:
        # 数据库为空时的默认值
        company_name = 'XX Hotel Furniture Manufacturer'
        current_title = 'Home - Premium Hotel Furniture | XX Hotel Furniture Manufacturer'
        current_description = 'Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.'
        current_keywords = 'hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture'
        company_logo_url = None
        theme = 'default'
        page_og_image = None

        # 新增字段默认值
        mode = 'official'
        basic_info = None
        company_advantages = None
        phone1 = phone2 = phone3 = None
        email1 = email2 = email3 = None
        fax = None
        address = None
        whatsapp1 = whatsapp2 = None
        wechat1 = wechat2 = None
    else:
        company_name = settings.company_name
        company_logo_url = url_for('static', filename='uploads/logo/company_logo') if settings.logo else None
        theme = settings.theme or 'default'
        page_og_image = None  # 默认无专用 OG 图片

        # ==================== 新增：注入所有后台设置字段 ====================
        mode = settings.mode or 'official'
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
        # ===================================================================

        endpoint = request.endpoint or ''

        # 首页
        if endpoint == 'main.index':
            current_title = (settings.seo_home_title or 'Home - Premium Hotel Furniture | {company_name}').format(company_name=company_name)
            current_description = settings.seo_home_description or 'Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.'
            current_keywords = settings.seo_home_keywords or 'hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture'

        # 产品详情页
        elif 'products.product_detail' in endpoint:
            current_title = f'Product Detail - {company_name}'
            current_description = settings.seo_products_description or 'Explore our complete collection of premium hotel furniture...'
            current_keywords = settings.seo_products_keywords or 'hotel furniture products, hotel beds, hotel sofas, hotel wardrobes'

        # 产品相关页面
        elif 'products.' in endpoint:
            current_title = (settings.seo_products_title or 'Products | {company_name}').format(company_name=company_name)
            current_description = settings.seo_products_description or 'Explore our complete collection of premium hotel furniture including beds, nightstands, sofas, wardrobes and custom case goods for luxury hospitality projects.'
            current_keywords = settings.seo_products_keywords or 'hotel furniture products, hotel beds, hotel sofas, hotel wardrobes, luxury hotel furniture collection'

        # 关于页
        elif endpoint == 'main.about':
            current_title = (settings.seo_about_title or 'About Us - {company_name} | Leading Hotel Furniture Manufacturer').format(company_name=company_name)
            current_description = settings.seo_about_description or 'Learn about {company_name}, a professional hotel furniture manufacturer with years of experience in custom hospitality furniture design and production.'
            current_keywords = 'about hotel furniture manufacturer, hospitality furniture company, custom hotel furniture supplier'

        # 联系页
        elif endpoint == 'main.contact':
            current_title = (settings.seo_contact_title or 'Contact Us - {company_name} | Hotel Furniture Inquiry').format(company_name=company_name)
            current_description = settings.seo_contact_description or 'Contact {company_name} for custom hotel furniture solutions, quotes, and partnership opportunities.'
            current_keywords = 'contact hotel furniture manufacturer, hotel furniture quote, hospitality furniture supplier'

        # ==================== 专题系列页面 SEO 支持 ====================
        elif endpoint == 'series.list':
            current_title = f"Hotel Furniture Series & Collections - {company_name}"
            current_description = f"Explore our curated hotel furniture series and collections designed for luxury hospitality projects at {company_name}."
            current_keywords = "hotel furniture series, luxury hotel collections, hospitality design series, custom hotel furniture sets, themed hotel furniture"

        elif endpoint == 'series.detail':
            slug = request.view_args.get('slug') if request.view_args else None
            series = FeatureSeries.query.filter_by(slug=slug).first() if slug else None

            if series:
                current_title = series.seo_title or f"{series.name} - Premium Hotel Furniture Series | {company_name}"
                current_description = series.seo_description or (
                    series.description[:157] + "..." if series.description and len(series.description) > 160
                    else f"Discover the {series.name} hotel furniture series by {company_name}, featuring premium beds, sofas, wardrobes and custom designs for luxury hospitality spaces."
                )
                current_keywords = series.seo_keywords or "hotel furniture series, luxury hospitality design, custom hotel furniture collection, themed hotel interiors"

                # OG 图片支持：使用系列第一张图片
                if series.photos:
                    first_photo = series.photos.split(',')[0].strip()
                    page_og_image = url_for('static', filename='uploads/series/' + first_photo, _external=True)
            else:
                current_title = f"Furniture Series - {company_name}"
                current_description = f"View our premium hotel furniture series at {company_name}."
                current_keywords = "hotel furniture, luxury collections"
        # ====================================================================

        # ==================== 新增：Inquiry Cart 页面 SEO 支持 ====================
        elif endpoint == 'main.cart':
            current_title = f"My Inquiry Cart - {company_name}"
            current_description = f"View your temporarily selected hotel furniture products for quotation at {company_name}."
            current_keywords = "hotel furniture inquiry cart, quotation list, custom hotel furniture quote, product selection"
        # ====================================================================

        else:
            current_title = f'{company_name} | Professional Hotel Furniture Manufacturer'
            current_description = 'Premium hotel furniture solutions for luxury hospitality.'
            current_keywords = 'hotel furniture, custom hotel furniture'

    return dict(
        company_name=company_name,
        page_title=current_title,
        page_description=current_description,
        page_keywords=current_keywords,
        company_logo_url=company_logo_url,
        theme=theme,
        page_og_image=page_og_image,

        # ==================== 新增：注入所有后台设置字段 ====================
        mode=mode,
        basic_info=basic_info,
        company_advantages=company_advantages,
        phone1=phone1,
        phone2=phone2,
        phone3=phone3,
        email1=email1,
        email2=email2,
        email3=email3,
        fax=fax,
        address=address,
        whatsapp1=whatsapp1,
        whatsapp2=whatsapp2,
        wechat1=wechat1,
        wechat2=wechat2,

        # ==================== 当前年份（用于页脚版权） ====================
        current_year=datetime.now().strftime('%Y')
        # ==================================================================
    )
# ============================================================================

@main_bp.route('/')
def index():
    # 获取所有专题系列
    all_series = FeatureSeries.query.order_by(FeatureSeries.created_at.desc()).all()
    
    # 过滤出至少有一个关联产品的系列（精确匹配）
    valid_series = []
    for series in all_series:
        has_product = Product.query.filter(
            or_(
                Product.featured_series == series.slug,
                Product.featured_series.like(f'{series.slug},%'),
                Product.featured_series.like(f'%,{series.slug}'),
                Product.featured_series.like(f'%,{series.slug},%'),
                Product.featured_series.like(f'{series.slug},')
            )
        ).count() > 0
        if has_product:
            valid_series.append(series)
    
    # 随机选取最多 3 个
    featured_series_list = random.sample(valid_series, k=min(3, len(valid_series))) if valid_series else []
    random.shuffle(featured_series_list)  # 再次随机顺序
    
    return render_template(
        'index.html',
        featured_series_list=featured_series_list
    )

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/cart')
def cart():
    return render_template('cart.html')
