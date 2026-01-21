# init_schema.py
# 完整数据库初始化脚本（2026-01-21 最终版 - 只使用本地图片）
# 更新内容：
# - 彻底移除 GitHub 相关逻辑
# - 图片文件名使用 UUID 风格（兼容本地 ImageService 规则）
# - 预置系列增加多张示例图片
# - 产品与系列关联使用 slug 匹配
# - 增加更多调试打印

import os
import uuid
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
    print("开始数据库初始化...")

    # 1. 重置数据库（删表重建） - 开发阶段常用，生产环境请注释掉！
    db.drop_all()
    db.create_all()
    print("所有表已重新创建（包括 smtp_config 表）。")

    # 2. 默认管理员账号
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
        print("管理员账号创建成功：admin / admin123")

    # 3. 默认网站设置（地址英文 + 社交 + SEO）
    if Settings.query.count() == 0:
        default_settings = Settings(
            company_name='XX Hotel Furniture Manufacturer',
            theme='default',
            mode='official',

            basic_info=(
                "We are a professional manufacturer specializing in high-end hotel furniture design, "
                "production, and customization, with over 15 years of industry experience..."
            ),
            company_advantages=(
                "• 15+ years focused on hotel furniture\n"
                "• Full customization support\n"
                "• Eco-friendly materials (CARB P2, FSC)\n"
                "• Mature supply chain & stable lead times"
            ),

            phone1='+86 123-4567-8900',
            phone2='+86 987-6543-2100',
            email1='sales@hotel-furniture.com',
            email2='info@hotel-furniture.com',
            fax='+86 123-4567-8901',
            address=(
                "Furniture Industrial Park, Lecong Town, Shunde District\n"
                "Foshan City, Guangdong Province, China\n"
                "Postal Code: 528315"
            ),

            whatsapp1='+86 123-4567-8900',
            wechat1='+86 123-4567-8900',

            # SEO 字段（保持原样，略去部分内容以节省空间）
            seo_home_title='Home - Premium Hotel Furniture | {company_name}',
            seo_home_description='Professional hotel furniture manufacturer...',
            # ... 其他 SEO 字段保持不变 ...
        )
        db.session.add(default_settings)
        print("默认网站设置创建成功（包含英文地址 & 社交联系方式）")

    # 4. 默认分类
    if Category.query.count() == 0:
        categories_list = [
            "Beds", "Nightstands/Bedside Tables", "Sofas and Armchairs",
            "Coffee Tables/Tea Tables", "Lounge Chairs/Ottomans",
            "Desk Chairs/Writing Chairs", "Dining Chairs",
            "Luggage Racks/Benches", "Side Tables/End Tables", "Accent Chairs",
            "Headboards", "Wardrobes/Closets/Armoires", "Built-in Desks/Writing Tables",
            "TV Cabinets/Entertainment Units", "Dressers/Chests of Drawers",
            "Vanities/Bathroom Cabinets", "Built-in Minibars",
            "Wall Panels/Decorative Paneling", "Fixed Shelving/Storage Units",
            "Console Tables (wall-fixed)"
        ]
        for name in categories_list:
            db.session.add(Category(name=name))
        print(f"已创建 {len(categories_list)} 个默认分类")

    # 5. 预置产品数据（图片文件名使用 UUID 风格，明确为本地路径）
    if Product.query.count() == 0:
        def fake_uuid(prefix=''):
            """生成模拟的本地图片文件名（兼容本地上传规则）"""
            return f"{prefix}{uuid.uuid4().hex[:8]}.jpg"

        products_data = [
            {
                "product_code": "pc897421976",
                "name": "Deluxe King Bed",
                "description": "Luxury king-size bed with premium upholstery and solid wood frame",
                "image": fake_uuid("bed_main_"),
                "photos": f"{fake_uuid('bed_')},{fake_uuid('bed_')},{fake_uuid('bed_')}",
                "length": 2200, "width": 2000, "height": 1200, "seat_height": None,
                "base_material": "Solid Wood", "surface_material": "Velvet",
                "featured_series": "nordic-minimalism",
                "applicable_space": "Guest Room,Suite",
                "category_name": "Beds"
            },
            {
                "product_code": "pc284539245",
                "name": "Modern Sofa Set",
                "description": "Comfortable 3-seater sofa with high-density foam",
                "image": fake_uuid("sofa_main_"),
                "photos": f"{fake_uuid('sofa_')},{fake_uuid('sofa_')}",
                "length": 2400, "width": 950, "height": 850, "seat_height": 450,
                "base_material": "Fabric", "surface_material": "Linen",
                "featured_series": "nordic-minimalism",
                "applicable_space": "Lobby,Lounge",
                "category_name": "Sofas and Armchairs"
            },
            {
                "product_code": "pc567890123",
                "name": "Elegant Nightstand",
                "description": "Minimalist bedside table with marble top",
                "image": fake_uuid("nightstand_main_"),
                "photos": f"{fake_uuid('night_')},{fake_uuid('night_')}",
                "length": 600, "width": 450, "height": 550, "seat_height": None,
                "base_material": "Solid Wood", "surface_material": "Marble",
                "featured_series": "nordic-minimalism",
                "applicable_space": "Guest Room,Suite",
                "category_name": "Nightstands/Bedside Tables"
            },
            {
                "product_code": "pc123456789",
                "name": "Luxury Wardrobe",
                "description": "Spacious wardrobe with sliding doors and LED lighting",
                "image": fake_uuid("wardrobe_main_"),
                "photos": f"{fake_uuid('wardrobe_')},{fake_uuid('wardrobe_')},{fake_uuid('wardrobe_')}",
                "length": 2400, "width": 650, "height": 2400, "seat_height": None,
                "base_material": "MDF", "surface_material": "Wood Veneer",
                "featured_series": "nordic-minimalism",
                "applicable_space": "Guest Room,Suite",
                "category_name": "Wardrobes/Closets/Armoires"
            },
            {
                "product_code": "pc987654321",
                "name": "Coffee Table Set",
                "description": "Modern glass top coffee table with metal base",
                "image": fake_uuid("coffee_main_"),
                "photos": f"{fake_uuid('coffee_')},{fake_uuid('coffee_')}",
                "length": 1200, "width": 700, "height": 450, "seat_height": None,
                "base_material": "Stainless Steel", "surface_material": "Tempered Glass",
                "featured_series": "nordic-minimalism",
                "applicable_space": "Lobby,Lounge",
                "category_name": "Coffee Tables/Tea Tables"
            }
        ]

        for data in products_data:
            category = Category.query.filter_by(name=data["category_name"]).first()
            if category:
                product = Product(
                    product_code=data["product_code"],
                    name=data["name"],
                    description=data.get("description"),
                    image=data["image"],
                    photos=data["photos"],
                    length=data.get("length"),
                    width=data.get("width"),
                    height=data.get("height"),
                    seat_height=data.get("seat_height"),
                    base_material=data.get("base_material"),
                    surface_material=data.get("surface_material"),
                    featured_series=data.get("featured_series"),
                    applicable_space=data.get("applicable_space"),
                    category_id=category.id
                )
                db.session.add(product)
        print("已注入 5 条预置产品数据（图片文件名使用本地 UUID 风格）")

    # 6. 预置测试专题系列（多张图片 + SEO）
    if FeatureSeries.query.count() == 0:
        fake_series_uuid = lambda: f"series_{uuid.uuid4().hex[:8]}.jpg"
        test_series = FeatureSeries(
            name="Nordic Minimalism Collection",
            slug="nordic-minimalism",
            description="Clean lines, natural materials, and functional design for modern luxury hotels.",
            applicable_space="Guest Room,Lobby,Suite",
            photos=f"{fake_series_uuid()},{fake_series_uuid()},{fake_series_uuid()},{fake_series_uuid()}",
            seo_title="Nordic Minimalism Hotel Furniture Series | {company_name}",
            seo_description="Discover our Nordic Minimalism collection featuring clean Scandinavian design, natural wood tones, and timeless elegance.",
            seo_keywords="nordic hotel furniture, minimalist hospitality, scandinavian design, luxury hotel furniture"
        )
        db.session.add(test_series)
        print("已创建 1 个测试专题系列（slug: nordic-minimalism，4 张示例图片）")

    # 7. 默认 SMTP 配置
    if SmtpConfig.query.count() == 0:
        default_smtp = SmtpConfig(
            provider='gmail',
            mail_server='smtp.gmail.com',
            mail_port=587,
            mail_use_tls=True,
            mail_use_ssl=False,
            mail_username='',
            mail_password='',
            test_recipient='your-real-test-email@gmail.com',  # ← 强烈建议改为你自己的邮箱！
            default_sender_name='Hotel Furniture Official Site'
        )
        db.session.add(default_smtp)
        print("默认 SMTP 配置已创建（请尽快到后台填写真实账号密码）")

    db.session.commit()
    print("\n" + "="*70)
    print("数据库初始化完成！（所有图片路径已明确为本地 uploads/ 目录）")
    print("管理员：admin / admin123")
    print("预置数据：5 产品 + 1 专题系列 + 默认设置 + SMTP 配置")
    print("图片文件名：使用 UUID 风格，模拟本地上传")
    print("下一步：运行项目 → 登录后台 /admin → 检查产品/系列图片是否正常显示")
    print("="*70 + "\n")
