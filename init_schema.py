# init_schema_full.py
# 完整数据库初始化脚本（包含 FeatureSeries 模型，适用于删库后重建）

import os
from datetime import datetime
from app import create_app, db
from app.models import (
    User, Settings, Category, Product, FeatureSeries
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
    print("所有表已重新创建。")

    # 1. 默认管理员账号
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
        print("管理员账号创建：admin / admin123")

    # 2. 默认网站设置 + SEO
    if Settings.query.count() == 0:
        default_settings = Settings(
            company_name='XX Hotel Furniture Manufacturer',
            theme='default',

            seo_home_title='Home - Premium Hotel Furniture | {company_name}',
            seo_home_description='Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.',
            seo_home_keywords='hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture',

            seo_products_title='Hotel Furniture Products | Beds, Sofas, Wardrobes - {company_name}',
            seo_products_description='Explore our complete collection of premium hotel furniture including beds, nightstands, sofas, wardrobes and custom case goods for luxury hospitality projects.',
            seo_products_keywords='hotel furniture products, hotel beds, hotel sofas, hotel wardrobes, luxury hotel furniture collection',

            seo_about_title='About Us - {company_name} | Leading Hotel Furniture Manufacturer',
            seo_about_description='Learn about {company_name}, a professional hotel furniture manufacturer with years of experience in custom hospitality furniture design and production.',

            seo_contact_title='Contact Us - {company_name} | Hotel Furniture Inquiry',
            seo_contact_description='Contact {company_name} for custom hotel furniture solutions, quotes, and partnership opportunities.'
        )
        db.session.add(default_settings)
        print("默认网站设置已创建。")

    # 3. 默认分类（酒店家具完整英文分类）
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

    # 4. 预置 5 条真实产品数据（您之前指定的）
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

    # 5. （可选）预置一个测试专题系列
    if FeatureSeries.query.count() == 0:
        test_series = FeatureSeries(
            name="Nordic Minimalism Collection",
            slug="nordic-minimal-2025",
            description="Clean lines, natural materials, and functional design for modern luxury hotels.",
            applicable_space="Guest Room,Lobby,Suite",
            photos="",  # 可后续上传
            seo_title="Nordic Minimalism Hotel Furniture Series | {company_name}",
            seo_description="Discover our Nordic Minimalism hotel furniture collection featuring premium beds, sofas, and case goods with clean Scandinavian design.",
            seo_keywords="nordic hotel furniture, minimalist hospitality design, scandinavian hotel beds"
        )
        db.session.add(test_series)
        print("已创建 1 个测试专题系列（Nordic Minimalism Collection）。")

    db.session.commit()
    print("\n数据库初始化完成！")
    print("管理员账号：admin / admin123")
    print("可直接启动项目使用。")
