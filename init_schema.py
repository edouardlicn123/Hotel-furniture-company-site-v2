# init_schema.py
# 完整数据库初始化脚本（2026-01-21 最终更新版 - 只使用本地图片）
# 更新内容：
# - 删除产品的 image 字段（已废弃，所有图片统一使用 photos 字段）
# - 删除原有默认产品和系列数据
# - 插入新的默认系列（Basic1）和 5 个产品（使用 photos 字段，第一张作为主图）
# - 图片文件名已由后台上传生成，保持原样
# - 增加调试打印，便于检查

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

    # 4. 默认分类（保持原有分类列表）
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

    # 5. 预置新的专题系列（只插入 Basic1）
    if FeatureSeries.query.count() == 0:
        series_basic1 = FeatureSeries(
            id=2,  # 保持你指定的 ID
            name='Basic1',
            slug='basic1',
            description='basic for studio',
            applicable_space='',
            photos='series_basic1_6f61a4ba4e79662d.png',
            seo_title='',
            seo_description='',
            seo_keywords='',
            created_at=datetime.fromisoformat('2026-01-21 08:14:12.355711')
        )
        db.session.add(series_basic1)
        print("已创建专题系列：Basic1")

    # 6. 预置新的产品数据（5 个产品，使用 photos 字段，无 image 字段）
    if Product.query.count() == 0:
        products_data = [
            {
                "id": 1,
                "product_code": "pc362187539",
                "name": "Bed",
                "description": "Bed for room",
                "photos": "pc362187539_0e94cd6bb83bd214.png",
                "featured_series": "basic1",
                "applicable_space": "room,studio",
                "category_id": 1,
                "created_at": datetime.fromisoformat('2026-01-21 08:15:36.208459')
            },
            {
                "id": 2,
                "product_code": "pc037754335",
                "name": "Bed",
                "description": "Bed for room",
                "photos": "pc037754335_4590901c54c4a37c.png",
                "featured_series": "basic2",
                "applicable_space": "room,studio",
                "category_id": 1,
                "created_at": datetime.fromisoformat('2026-01-21 08:16:48.999012')
            },
            {
                "id": 3,
                "product_code": "pc360929806",
                "name": "Nightstand",
                "description": "Simple nightstand",
                "photos": "pc360929806_b3292d8c3433e0a0.png",
                "length": 550,
                "width": 400,
                "height": 600,
                "base_material": "wood",
                "featured_series": "basic1",
                "applicable_space": "room,studio",
                "category_id": 2,
                "created_at": datetime.fromisoformat('2026-01-21 08:20:21.653064')
            },
            {
                "id": 4,
                "product_code": "pc085902095",
                "name": "Luggage rack",
                "description": "Luggage rack,suggest for simple hotel use.",
                "photos": "pc085902095_5dafa7e9730935f3.png",
                "length": 1200,
                "width": 400,
                "height": 450,
                "base_material": "metal,sponge",
                "surface_material": "cloth",
                "applicable_space": "room",
                "category_id": 8,
                "created_at": datetime.fromisoformat('2026-01-21 08:24:48.800293')
            },
            {
                "id": 5,
                "product_code": "pc719779063",
                "name": "Coffee table",
                "description": "Simple coffee table",
                "photos": "pc719779063_3c73f5f12c3e9cd5.png",
                "length": 800,
                "width": 800,
                "height": 450,
                "base_material": "wood",
                "featured_series": "basic1",
                "applicable_space": "studio",
                "category_id": 4,
                "created_at": datetime.fromisoformat('2026-01-21 08:29:53.393556')
            }
        ]

        for data in products_data:
            product = Product(
                id=data.get("id"),
                product_code=data["product_code"],
                name=data["name"],
                description=data.get("description"),
                # image 字段已删除，不再设置
                photos=data["photos"],
                length=data.get("length"),
                width=data.get("width"),
                height=data.get("height"),
                seat_height=data.get("seat_height"),
                base_material=data.get("base_material"),
                surface_material=data.get("surface_material"),
                featured_series=data.get("featured_series"),
                applicable_space=data.get("applicable_space"),
                category_id=data["category_id"],
                created_at=data["created_at"]
            )
            db.session.add(product)
        print("已注入 5 条新预置产品数据（使用 photos 字段，无 image 字段）")

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
    print("数据库初始化完成！")
    print("管理员：admin / admin123")
    print("预置数据：5 产品 + 1 专题系列（Basic1） + 默认设置 + SMTP 配置")
    print("图片文件名：使用后台上传生成的文件名")
    print("下一步：运行项目 → 登录后台 /admin → 检查产品/系列图片是否正常显示")
    print("="*70 + "\n")
