from app import db
from datetime import datetime
from flask_login import UserMixin

# 用户表（后台登录用）
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # 存储哈希密码


# 网站设置表（单行记录，包含 SEO 配置）
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), default='XX Hotel Furniture Manufacturer')
    theme = db.Column(db.String(20), default='light')
    logo = db.Column(db.String(200))  # 公司 Logo 文件名（固定为 company_logo）

    # Homepage SEO
    seo_home_title = db.Column(db.String(200), default='Home - Premium Hotel Furniture | {company_name}')
    seo_home_description = db.Column(db.Text, default='Professional hotel furniture manufacturer specializing in luxury beds, sofas, wardrobes and custom solutions for 5-star hotels worldwide.')
    seo_home_keywords = db.Column(db.Text, default='hotel furniture, luxury hotel beds, hotel sofas, custom hospitality furniture, hotel room furniture')

    # Products Page SEO
    seo_products_title = db.Column(db.String(200), default='Hotel Furniture Products | Beds, Sofas, Wardrobes - {company_name}')
    seo_products_description = db.Column(db.Text, default='Explore our complete collection of premium hotel furniture including beds, nightstands, sofas, wardrobes and custom case goods for luxury hospitality projects.')
    seo_products_keywords = db.Column(db.Text, default='hotel furniture products, hotel beds, hotel sofas, hotel wardrobes, luxury hotel furniture collection')

    # About Page SEO
    seo_about_title = db.Column(db.String(200), default='About Us - {company_name} | Leading Hotel Furniture Manufacturer')
    seo_about_description = db.Column(db.Text, default='Learn about {company_name}, a professional hotel furniture manufacturer with years of experience in custom hospitality furniture design and production.')

    # Contact Page SEO
    seo_contact_title = db.Column(db.String(200), default='Contact Us - {company_name} | Hotel Furniture Inquiry')
    seo_contact_description = db.Column(db.Text, default='Contact {company_name} for custom hotel furniture solutions, quotes, and partnership opportunities.')


# 主分类（酒店家具英文分类）
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # 新增：产品编号，格式 pc + 9位数字（如 pc284539245），唯一且必填
    product_code = db.Column(db.String(12), unique=True, nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # 主图（兼容旧数据）
    image = db.Column(db.String(200))
    
    # 多图（逗号分隔，最多10张）
    photos = db.Column(db.String(1000))
    
    # 规格字段
    length = db.Column(db.Integer)  # Length (mm)
    width = db.Column(db.Integer)   # Width (mm)
    height = db.Column(db.Integer)  # Height (mm)
    seat_height = db.Column(db.Integer)  # Seat Height (mm)
    
    # 材质
    base_material = db.Column(db.String(100))
    surface_material = db.Column(db.String(100))
    
    # 精选系列（逗号分隔字符串）
    featured_series = db.Column(db.String(200))
    
    # 适用空间（逗号分隔字符串）
    applicable_space = db.Column(db.String(200))
    
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('Category', backref='products')
