from flask import Blueprint, render_template, request, url_for
from app.models import Settings

main_bp = Blueprint('main', __name__)

# ====================== 全局上下文处理器（已提升到 app 级别） ======================
# 注意：实际代码已移到 __init__.py，但这里保留完整逻辑供参考
def inject_seo_data():
    settings = Settings.query.first()
    if not settings:
        # 数据库为空时的默认值
        company_name = 'XX Hotel Furniture Manufacturer'
        current_title = 'Home - Premium Hotel Furniture | XX Hotel Furniture Manufacturer'
        current_description = 'Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.'
        current_keywords = 'hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture'
        company_logo_url = None
        theme = 'default'  # 默认主题
    else:
        company_name = settings.company_name
        
        # Logo URL
        company_logo_url = url_for('static', filename='uploads/logo/company_logo') if settings.logo else None
        
        # 关键：注入当前主题
        theme = settings.theme or 'default'

        # 根据当前路由选择 SEO 配置
        endpoint = request.endpoint or ''

        if endpoint == 'main.index':
            current_title = (settings.seo_home_title or 'Home - Premium Hotel Furniture | {company_name}').format(company_name=company_name)
            current_description = settings.seo_home_description or 'Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.'
            current_keywords = settings.seo_home_keywords or 'hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture'
        
        elif 'products.product_detail' in endpoint:
            current_title = f'Product Detail - {company_name}'
            current_description = settings.seo_products_description or 'Explore our complete collection of premium hotel furniture...'
            current_keywords = settings.seo_products_keywords or 'hotel furniture products, hotel beds, hotel sofas, hotel wardrobes'
        
        elif 'products.' in endpoint:
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
        theme=theme  # ← 关键：注入 theme 变量供前端使用
    )
# ============================================================================

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')
