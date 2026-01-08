# init_schema.py

import os
import random
import string
from app import create_app, db
from app.models import User, Settings, Category, Product
from werkzeug.security import generate_password_hash

app = create_app()

instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)

with app.app_context():
    db.create_all()

    # 默认管理员账号
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin123')
        )
        db.session.add(admin_user)

    # 默认网站设置 + SEO 配置（保持不变）
    if Settings.query.count() == 0:
        default_settings = Settings(
            company_name='XX Hotel Furniture Manufacturer',
            theme='default',  # 确保与 themes/default.css 匹配

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

    # 酒店家具英文分类（保持完整）
    if Category.query.count() == 0:
        loose_cats = [
            "Beds",
            "Nightstands/Bedside Tables",
            "Sofas and Armchairs",
            "Coffee Tables/Tea Tables",
            "Lounge Chairs/Ottomans",
            "Desk Chairs/Writing Chairs",
            "Dining Chairs",
            "Luggage Racks/Benches",
            "Side Tables/End Tables",
            "Accent Chairs"
        ]

        fixed_cats = [
            "Headboards",
            "Wardrobes/Closets/Armoires",
            "Built-in Desks/Writing Tables",
            "TV Cabinets/Entertainment Units",
            "Dressers/Chests of Drawers",
            "Vanities/Bathroom Cabinets",
            "Built-in Minibars",
            "Wall Panels/Decorative Paneling",
            "Fixed Shelving/Storage Units",
            "Console Tables (wall-fixed)"
        ]

        all_cats = loose_cats + fixed_cats
        for cat_name in all_cats:
            db.session.add(Category(name=cat_name))

    # ==================== 注入你指定的5条真实预产品数据 ====================
    if Product.query.count() == 0:
        products_data = [
            {
                "product_code": "pc897421976",
                "name": "Bed",
                "description": "Bed for rooms",
                "image": "product1.png",
                "photos": "product1.png",
                "length": None,
                "width": None,
                "height": None,
                "seat_height": None,
                "base_material": "wood",
                "surface_material": "cloth",
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
                "length": None,
                "width": None,
                "height": None,
                "seat_height": None,
                "base_material": "wood",
                "surface_material": "cloth",
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
                "length": 550,
                "width": 400,
                "height": 600,
                "seat_height": None,
                "base_material": "wood",
                "surface_material": "wood",
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
                "length": 1200,
                "width": 400,
                "height": 450,
                "seat_height": None,
                "base_material": "metal and foam",
                "surface_material": "cloth",
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
                "length": 800,
                "width": 800,
                "height": 450,
                "seat_height": None,
                "base_material": "wood",
                "surface_material": "",
                "featured_series": "",
                "applicable_space": "lounge",
                "category_name": "Coffee Tables/Tea Tables"
            }
        ]

        for data in products_data:
            category = Category.query.filter_by(name=data["category_name"]).first()
            if not category:
                # 如果分类不存在（理论上不会），创建它
                category = Category(name=data["category_name"])
                db.session.add(category)
                db.session.flush()

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
                category_id=category.id
            )
            db.session.add(product)

    db.session.commit()
    print("Database initialization complete!")
    print("Admin account: admin / admin123")
    print("5 real products with specified codes and images have been injected.")
    print("Theme set to 'default' for correct CSS loading.")
