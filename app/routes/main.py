# app/routes/main.py
# 前台主路由蓝图

from flask import Blueprint, render_template, request
from app.models import Settings, FeatureSeries  # 导入所需模型
from datetime import datetime

main_bp = Blueprint('main', __name__)

# 全局上下文处理器：注入 SEO + 网站设置到所有模板
def inject_seo_data():
    # 每次请求都实时查询 Settings（避免缓存旧数据）
    settings = Settings.query.first()
    if not settings:
        settings = Settings()  # 安全返回默认空对象

    company_name = settings.company_name or 'Hotel Furniture Manufacturer'

    # 动态替换 {company_name} 并根据模式选择默认 SEO
    return {
        'settings': settings,  # 全局可用：mode、company_name、logo、联系方式等
        'company_name': company_name,
        'current_year': datetime.now().year,

        # Homepage SEO
        'seo_home_title': (
            settings.seo_home_title.format(company_name=company_name)
            if settings.seo_home_title else f'Home - Premium Hotel Furniture | {company_name}'
        ),
        'seo_home_description': (
            settings.seo_home_description.format(company_name=company_name)
            if settings.seo_home_description else
            f'Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.'
        ),
        'seo_home_keywords': settings.seo_home_keywords or 'hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture',

        # Products Page SEO
        'seo_products_title': (
            settings.seo_products_title.format(company_name=company_name)
            if settings.seo_products_title else f'Products - {company_name} | Hotel Furniture Catalog'
        ),
        'seo_products_description': (
            settings.seo_products_description.format(company_name=company_name)
            if settings.seo_products_description else
            f'Browse our complete collection of premium hotel furniture including beds, nightstands, sofas, wardrobes and custom case goods.'
        ),
        'seo_products_keywords': settings.seo_products_keywords or 'hotel furniture products, hotel beds, hotel sofas, hotel wardrobes, luxury hotel furniture',

        # About & Contact SEO（类似处理）
        'seo_about_title': (
            settings.seo_about_title.format(company_name=company_name)
            if settings.seo_about_title else f'About Us - {company_name} | Leading Hotel Furniture Manufacturer'
        ),
        'seo_contact_title': (
            settings.seo_contact_title.format(company_name=company_name)
            if settings.seo_contact_title else f'Contact Us - {company_name} | Hotel Furniture Inquiry'
        ),
    }

# 首页
@main_bp.route('/')
def index():
    # 获取专题系列（可加排序、限制数量）
    featured_series = FeatureSeries.query.order_by(FeatureSeries.created_at.desc()).limit(6).all()
    
    return render_template(
        'index.html',
        featured_series=featured_series  # 传递给首页模板，用于 featured_series.html
    )

# 购物车页面（依赖全局 settings，无需额外传参）
@main_bp.route('/cart')
def cart():
    return render_template('cart.html')

# 关于我们
@main_bp.route('/about')
def about():
    return render_template('about.html')

# 联系我们
@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

# 将上下文处理器注册到蓝图（所有 main_bp 路由都会自动注入）
main_bp.context_processor(inject_seo_data)
