# app/routes/main.py
# 前台主路由蓝图 - 完整版（已修复 SEO 占位符替换问题）

from flask import Blueprint, render_template, request
from app.models import Settings, FeatureSeries
from datetime import datetime

main_bp = Blueprint('main', __name__)

# 全局上下文处理器：注入 SEO + 网站设置到所有模板
# 重点修复：自动替换 {company_name} 占位符
def inject_seo_data():
    # 每次请求都实时查询 Settings（避免缓存旧数据）
    settings = Settings.query.first()
    if not settings:
        settings = Settings()  # 安全返回默认空对象

    # 基础公司名称（兜底）
    company_name = settings.company_name or 'Hotel Furniture Manufacturer'

    # 辅助函数：安全替换占位符
    def safe_format(text, **kwargs):
        if not text:
            return ''
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            # 如果格式化失败（占位符写错等），返回原始文本 + 公司名兜底
            return f"{text} | {company_name}"

    # 动态替换 {company_name} 并根据模式选择默认值
    return {
        'settings': settings,  # 全局可用：mode、company_name、logo、联系方式等
        'company_name': company_name,
        'current_year': datetime.now().year,

        # Homepage SEO
        'seo_home_title': safe_format(
            settings.seo_home_title,
            company_name=company_name
        ) or f'Home - Premium Hotel Furniture | {company_name}',

        'seo_home_description': safe_format(
            settings.seo_home_description,
            company_name=company_name
        ) or (
            'Professional hotel furniture manufacturer specializing in luxury beds, '
            f'sofas, wardrobes and custom solutions for 5-star hotels worldwide. - {company_name}'
        ),

        'seo_home_keywords': (
            settings.seo_home_keywords
            or f'hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, {company_name}'
        ),

        # Products Page SEO
        'seo_products_title': safe_format(
            settings.seo_products_title,
            company_name=company_name
        ) or f'Products - Hotel Furniture Catalog | {company_name}',

        'seo_products_description': safe_format(
            settings.seo_products_description,
            company_name=company_name
        ) or (
            f'Browse our complete collection of premium hotel furniture including beds, '
            f'nightstands, sofas, wardrobes and custom case goods. - {company_name}'
        ),

        'seo_products_keywords': (
            settings.seo_products_keywords
            or f'hotel furniture products, hotel beds, hotel sofas, hotel wardrobes, luxury hotel furniture, {company_name}'
        ),

        # About Page SEO
        'seo_about_title': safe_format(
            settings.seo_about_title,
            company_name=company_name
        ) or f'About Us - {company_name} | Leading Hotel Furniture Manufacturer',

        # Contact Page SEO
        'seo_contact_title': safe_format(
            settings.seo_contact_title,
            company_name=company_name
        ) or f'Contact Us - {company_name} | Hotel Furniture Inquiry',
    }

# 首页
@main_bp.route('/')
def index():
    # 获取专题系列（最新6个，可根据需要调整排序/数量）
    featured_series = FeatureSeries.query.order_by(FeatureSeries.created_at.desc()).limit(6).all()
    
    return render_template(
        'index.html',
        featured_series=featured_series,  # 传递给首页模板，用于 featured_series.html partial
    )

# 购物车页面（依赖全局 settings，无需额外传参）
@main_bp.route('/cart')
def cart():
    return render_template('cart.html')

# 关于我们页面
@main_bp.route('/about')
def about():
    return render_template('about.html')

# 联系我们页面
@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

# 错误页面示例（可选，根据需要添加）
@main_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

# 注册上下文处理器到蓝图（所有 main_bp 路由都会自动注入变量）
main_bp.context_processor(inject_seo_data)
