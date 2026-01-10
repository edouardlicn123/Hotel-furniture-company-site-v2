# init_schema_full.py
# 完整数据库初始化脚本（最新版：地址英文 + 系列示例图片 + 社交联系方式范例 + SMTP 配置）

import os
from datetime import datetime
from app import create_app, db
from app.models import (
    User, Settings, Category, Product, FeatureSeries, SmtpConfig
)
from werkzeug.security import generate_password_hash

app = create_app()

# 确保 instance 目录存在
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)

with app.app_context():
    # 删除所有表并重新创建（相当于删库重来）
    db.drop_all()
    db.create_all()
    print("所有表已重新创建（包括新增的 smtp_config 表）。")

    # 1. 默认管理员账号
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
        print("管理员账号创建：admin / admin123")

    # 2. 默认网站设置 + SEO + 新增字段（地址改为英文 + 社交联系方式范例）
    if Settings.query.count() == 0:
        default_settings = Settings(
            company_name='XX Hotel Furniture Manufacturer',
            theme='default',
            mode='official',  # 默认官方网站模式

            # ==================== 企业介绍默认内容 ====================
            basic_info=(
                "We are a professional manufacturer specializing in high-end hotel furniture design, production, and customization, "
                "with over 15 years of industry experience. Our factory is located in China's leading furniture manufacturing hub, "
                "equipped with advanced production facilities and strict quality control systems, "
                "providing one-stop furniture solutions for 5-star hotels, resorts, and premium commercial spaces worldwide."
            ),
            company_advantages=(
                "• 15+ years focused on hotel furniture, familiar with international hotel brand standards\n"
                "• Full customization support from concept to delivery\n"
                "• Eco-friendly premium materials with international certifications (CARB P2, FSC)\n"
                "• 5,000+㎡ showroom and mature supply chain for stable lead times\n"
                "• Complete service: design, prototyping, manufacturing, and installation"
            ),

            # ==================== 联系方式（地址改为英文） ====================
            phone1='+86 123-4567-8900',
            phone2='+86 987-6543-2100',
            phone3='',
            email1='sales@hotel-furniture.com',
            email2='info@hotel-furniture.com',
            email3='',
            fax='+86 123-4567-8901',
            address=(
                "Furniture Industrial Park, Lecong Town, Shunde District\n"
                "Foshan City, Guangdong Province, China\n"
                "Postal Code: 528315"
            ),

            # ==================== 新增：社交联系方式范例 ====================
            whatsapp1='+86 123-4567-8900',   # 与 phone1 相同
            whatsapp2='',
            wechat1='+86 123-4567-8900',     # 与 phone1 相同
            wechat2='',

            # Homepage SEO
            seo_home_title='Home - Premium Hotel Furniture | {company_name}',
            seo_home_description='Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.',
            seo_home_keywords='hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture',

            # Products Page SEO
            seo_products_title='Hotel Furniture Products | Beds, Sofas, Wardrobes - {company_name}',
            seo_products_description='Explore our complete collection of premium hotel furniture including beds, nightstands, sofas, wardrobes and custom case goods for luxury hospitality projects.',
            seo_products_keywords='hotel furniture products, hotel beds, hotel sofas, hotel wardrobes, luxury hotel furniture collection',

            # About Page SEO
            seo_about_title='About Us - {company_name} | Leading Hotel Furniture Manufacturer',
            seo_about_description='Learn about {company_name}, a professional hotel furniture manufacturer with years of experience in custom hospitality furniture design and production.',

            # Contact Page SEO
            seo_contact_title='Contact Us - {company_name} | Hotel Furniture Inquiry',
            seo_contact_description='Contact {company_name} for custom hotel furniture solutions, quotes, and partnership opportunities.'
        )
        db.session.add(default_settings)
        print("默认网站设置已创建（包含社交联系方式范例）。")

    # 3. 默认分类（保持不变）
    if Category.query.count() == 0:
        loose_cats = [
            "Beds", "Nightstands/Bedside Tables", "Sofas and Armchairs",
            "Coffee Tables/Tea Tables", "Lounge Chairs/Ottomans",
            "Desk Chairs/Writing Chairs", "Dining Chairs",
            "Luggage Racks/Benches", "Side Tables/End Tables", "Accent Chairs"
        ]
        fixed_cats = [
            "Headboards", "Wardrobes/Closets/Armoires", "Built-in Desks/Writing Tables",
            "TV Cabinets/Entertainment Units", "Dressers/Chests of Drawers",
            "Vanities/Bathroom Cabinets", "Built-in Minibars",
            "Wall Panels/Decorative Paneling", "Fixed Shelving/Storage Units",
            "Console Tables (wall-fixed)"
        ]
        all_cats = loose_cats + fixed_cats
        for cat_name in all_cats:
            db.session.add(Category(name=cat_name))
        print(f"已创建 {len(all_cats)} 个默认分类。")

    # 4. 预置 5 条产品数据（保持不变）
    if Product.query.count() == 0:
        products_data = [
            {
                "product_code": "pc897421976",
                "name": "Bed",
                "description": "Bed for rooms",
                "image": "product1.png",
                "photos": "product1.png",
                "length": None, "width": None, "height": None, "seat_height": None,
                "base_material": "wood", "surface_material": "cloth",
                "featured_series": "basic1",
                "applicable_space": "room",
                "category_name": "Beds"
            },
            {
                "product_code": "pc678534762",
                "name": "Bed",
                "description": "Bed for rooms",
                "image": "product2.png",
                "photos": "product2.png",
                "length": None, "width": None, "height": None, "seat_height": None,
                "base_material": "wood", "surface_material": "cloth",
                "featured_series": "basic2",
                "applicable_space": "room",
                "category_name": "Beds"
            },
            {
                "product_code": "pc453589563",
                "name": "nightstand",
                "description": "",
                "image": "product3.png",
                "photos": "product3.png",
                "length": 550, "width": 400, "height": 600, "seat_height": None,
                "base_material": "wood", "surface_material": "wood",
                "featured_series": "basic1",
                "applicable_space": "room",
                "category_name": "Nightstands/Bedside Tables"
            },
            {
                "product_code": "pc416738421",
                "name": "luggage rack",
                "description": "",
                "image": "product4.png",
                "photos": "product4.png",
                "length": 1200, "width": 400, "height": 450, "seat_height": None,
                "base_material": "metal and foam", "surface_material": "cloth",
                "featured_series": "",
                "applicable_space": "room",
                "category_name": "Luggage Racks/Benches"
            },
            {
                "product_code": "pc412456345",
                "name": "coffee table",
                "description": "",
                "image": "product5.png",
                "photos": "product5.png",
                "length": 800, "width": 800, "height": 450, "seat_height": None,
                "base_material": "wood", "surface_material": "",
                "featured_series": "",
                "applicable_space": "lounge",
                "category_name": "Coffee Tables/Tea Tables"
            }
        ]

        for data in products_data:
            category = Category.query.filter_by(name=data["category_name"]).first()
            product = Product(
                product_code=data["product_code"],
                name=data["name"],
                description=data["description"] or None,
                image=data["image"],
                photos=data["photos"],
                length=data["length"],
                width=data["width"],
                height=data["height"],
                seat_height=data["seat_height"],
                base_material=data["base_material"] or None,
                surface_material=data["surface_material"] or None,
                featured_series=data["featured_series"] or None,
                applicable_space=data["applicable_space"] or None,
                category_id=category.id if category else None
            )
            db.session.add(product)
        print("已注入 5 条预置产品数据。")

    # 5. 预置一个测试专题系列（保持用户当前设置）
    if FeatureSeries.query.count() == 0:
        test_series = FeatureSeries(
            name="Basic Collection1",
            slug="basic1",
            description="Clean lines, natural materials, and functional design for modern luxury hotels.",
            applicable_space="Guest Room,Lobby,Suite",
            photos="series_sample.jpeg",
            seo_title="Nordic Minimalism Hotel Furniture Series | {company_name}",
            seo_description="Discover our Nordic Minimalism hotel furniture collection featuring premium beds, sofas, and case goods with clean Scandinavian design.",
            seo_keywords="nordic hotel furniture, minimalist hospitality design, scandinavian hotel beds"
        )
        db.session.add(test_series)
        print("已创建 1 个测试专题系列（slug: basic1，图片：series_sample.jpeg）。")

    # 6. 新增：默认 SMTP 配置（gmail 预设，等待后台填写账号密码）
    if SmtpConfig.query.count() == 0:
        default_smtp = SmtpConfig(
            provider='gmail',
            mail_server='smtp.gmail.com',
            mail_port=587,
            mail_use_tls=True,
            mail_use_ssl=False,
            mail_username='',                    # 留空，后台填写
            mail_password='',                    # 留空，后台填写
            test_recipient='your_test_email@example.com',  # ← 请改为你能收到的真实邮箱，用于后续测试
            default_sender_name='酒店家具官网询价系统'
        )
        db.session.add(default_smtp)
        print("默认 SMTP 配置已创建（gmail 预设，等待后台填写账号密码）")

    db.session.commit()
    print("\n数据库初始化完成！")
    print("管理员账号：admin / admin123")
    print("地址已设置为英文版")
    print("社交联系方式范例已设置（WhatsApp1/WeChat1 与 phone1 相同）")
    print("SMTP 默认配置已添加（请登录后台 /admin/smtp 填写 Gmail 账号和应用专用密码）")
    print("可直接启动项目使用。")
