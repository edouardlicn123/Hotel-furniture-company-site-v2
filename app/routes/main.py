# app/routes/main.py - 完整最新版（2026-01-12 更新）
# 包含：SEO 统一注入、模式切换、全局联系信息注入、专题系列首页随机展示、购物车页面路由

from flask import Blueprint, render_template, request, url_for
from app.models import Settings, FeatureSeries, Product
from sqlalchemy import or_
import random
from datetime import datetime

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
        
        # 联系方式默认空
        basic_info = company_advantages = address = None
        phone1 = phone2 = phone3 = email1 = email2 = email3 = fax = None
        whatsapp1 = whatsapp2 = wechat1 = wechat2 = None
        
        # 默认 SEO
        current_title = f'Home - Premium Hotel Furniture | {company_name}'
        current_description = 'Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.'
        current_keywords = 'hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture'
    else:
        company_name = settings.company_name or 'XX Hotel Furniture Manufacturer'
        theme = settings.theme or 'default'
        mode = settings.mode or 'official'
        company_logo_url = url_for('static', filename='uploads/logo/company_logo') if settings.logo else None
        page_og_image = None  # 可由具体页面覆盖

        # 企业介绍 & 联系方式
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

        # 根据当前页面动态生成 SEO
        endpoint = request.endpoint or ''

        # 首页
        if endpoint == 'main.index':
            current_title = (settings.seo_home_title or 'Home - Premium Hotel Furniture | {company_name}').format(company_name=company_name)
            current_description = settings.seo_home_description or 'Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.'
            current_keywords = settings.seo_home_keywords or 'hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture'

        # 产品列表 & 相关页面
        elif endpoint.startswith('products.'):
            current_title = (settings.seo_products_title or 'Products | {company_name}').format(company_name=company_name)
            current_description = settings.seo_products_description or 'Explore our complete collection of premium hotel furniture including beds, nightstands, sofas, wardrobes and custom case goods for luxury hospitality projects.'
            current_keywords = settings.seo_products_keywords or 'hotel furniture products, hotel beds, hotel sofas, hotel wardrobes, luxury hotel furniture collection'

            # 产品详情页可进一步个性化（可选扩展）
            if endpoint == 'products.product_detail':
                current_title = f'Product Detail - {company_name}'

        # 关于我们
        elif endpoint == 'main.about':
            current_title = (settings.seo_about_title or 'About Us - {company_name} | Leading Hotel Furniture Manufacturer').format(company_name=company_name)
            current_description = settings.seo_about_description or 'Learn about {company_name}, a professional hotel furniture manufacturer with years of experience in custom hospitality furniture design and production.'
            current_keywords = 'about hotel furniture manufacturer, hospitality furniture company, custom hotel furniture supplier'

        # 联系我们
        elif endpoint == 'main.contact':
            current_title = (settings.seo_contact_title or 'Contact Us - {company_name} | Hotel Furniture Inquiry').format(company_name=company_name)
            current_description = settings.seo_contact_description or 'Contact {company_name} for custom hotel furniture solutions, quotes, and partnership opportunities.'
            current_keywords = 'contact hotel furniture manufacturer, hotel furniture quote, hospitality furniture supplier'

        # 专题系列列表
        elif endpoint == 'series.list':
            current_title = f"Hotel Furniture Series & Collections - {company_name}"
            current_description = f"Explore our curated hotel furniture series and collections designed for luxury hospitality projects at {company_name}."
            current_keywords = "hotel furniture series, luxury hotel collections, hospitality design series, custom hotel furniture sets"

        # 专题系列详情页（动态读取系列自定义 SEO）
        elif endpoint == 'series.detail':
            slug = request.view_args.get('slug')
            series = FeatureSeries.query.filter_by(slug=slug).first() if slug else None
            if series:
                current_title = series.seo_title or f"{series.name} - Premium Hotel Furniture Series | {company_name}"
                current_description = series.seo_description or (
                    series.description[:157] + "..." if series.description and len(series.description) > 160
                    else f"Discover the {series.name} hotel furniture series by {company_name}."
                )
                current_keywords = series.seo_keywords or "hotel furniture series, luxury hospitality design, custom hotel furniture collection"
                
                # 支持系列首图作为 OG 图片
                if series.photos:
                    first_photo = series.photos.split(',')[0].strip()
                    page_og_image = url_for('static', filename=f'uploads/series/{first_photo}', _external=True)
            else:
                current_title = f"Series Not Found - {company_name}"
                current_description = "View our premium hotel furniture collections."
                current_keywords = "hotel furniture series"

        # 购物车页面（新增）
        elif endpoint == 'main.cart':
            current_title = f"My Inquiry Cart - {company_name}"
            current_description = f"Review your selected hotel furniture products for quotation at {company_name}."
            current_keywords = "hotel furniture inquiry cart, quotation list, product selection, custom furniture quote"

        # 默认兜底
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
        
        # 网站模式 & 所有动态内容
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
        
        # 页脚常用变量
        current_year=datetime.now().strftime('%Y')
    )


# ====================== 路由定义 ======================

@main_bp.route('/')
def index():
    """首页 - 随机展示 3 个有产品的专题系列"""
    all_series = FeatureSeries.query.order_by(FeatureSeries.created_at.desc()).all()
    
    # 只保留至少有一个匹配产品的系列
    valid_series = []
    for series in all_series:
        has_product = Product.query.filter(
            or_(
                Product.featured_series == series.slug,
                Product.featured_series.like(f'{series.slug},%'),
                Product.featured_series.like(f'%,{series.slug}'),
                Product.featured_series.like(f'%,{series.slug},%'),
                Product.featured_series.like(f'{series.slug},%')
            )
        ).count() > 0
        if has_product:
            valid_series.append(series)
    
    # 随机选最多 3 个并打乱顺序
    featured_series_list = random.sample(valid_series, k=min(3, len(valid_series))) if valid_series else []
    random.shuffle(featured_series_list)
    
    return render_template(
        'index.html',
        featured_series_list=featured_series_list
    )


@main_bp.route('/about')
def about():
    """关于我们页面"""
    return render_template('about.html')


@main_bp.route('/contact')
def contact():
    """联系我们页面"""
    return render_template('contact.html')


@main_bp.route('/cart')
def cart():
    """询价购物车页面"""
    return render_template('cart.html')


# 可选扩展：未来可添加其他页面路由
# @main_bp.route('/privacy')
# def privacy():
#     return render_template('privacy.html')
