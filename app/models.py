from app import db
from datetime import datetime
from flask_login import UserMixin
from datetime import datetime


# 用户表（后台登录用）
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # 存储哈希密码


# 网站设置表（单行记录，包含 SEO 配置、主题、模式、企业信息、联系方式等）
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), default='XX Hotel Furniture Manufacturer')
    theme = db.Column(db.String(20), default='default')
    logo = db.Column(db.String(200))  # 公司 Logo 文件名（固定为 company_logo）

    # ==================== 新增：网站模式 ====================
    mode = db.Column(db.String(20), default='official')  # 'official' 或 'catalog'

    # ==================== 新增：企业介绍 ====================
    basic_info = db.Column(db.Text)               # 基本情况（用于关于我们页面）
    company_advantages = db.Column(db.Text)        # 企业优势（用于关于我们页面）

    # ==================== 新增：联系方式 ====================
    phone1 = db.Column(db.String(50))
    phone2 = db.Column(db.String(50))
    phone3 = db.Column(db.String(50))
    email1 = db.Column(db.String(100))
    email2 = db.Column(db.String(100))
    email3 = db.Column(db.String(100))
    fax = db.Column(db.String(50))
    address = db.Column(db.Text)

    # ==================== 新增：社交联系方式 ====================
    whatsapp1 = db.Column(db.String(50))
    whatsapp2 = db.Column(db.String(50))
    wechat1 = db.Column(db.String(50))
    wechat2 = db.Column(db.String(50))

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


class FeatureSeries(db.Model):
    __tablename__ = 'feature_series'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 显示名称（前台展示，必填，唯一）
    name = db.Column(db.String(200), nullable=False, unique=True)
    
    # URL 标识符（用于路由和匹配产品 featured_series，必填，唯一）
    slug = db.Column(db.String(100), nullable=False, unique=True)
    
    # 系列描述（可选，支持后续富文本）
    description = db.Column(db.Text)
    
    # 适用空间（逗号分隔字符串，例如：Guest Room,Lobby,Restaurant）
    applicable_space = db.Column(db.String(200))
    
    # 系列图片（最多5张，逗号分隔文件名，路径：uploads/series/）
    photos = db.Column(db.String(1000))
    
    # SEO 字段（后台可自定义）
    seo_title = db.Column(db.String(200))
    seo_description = db.Column(db.Text)
    seo_keywords = db.Column(db.Text)
    
    # 创建时间（用于排序）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FeatureSeries {self.name}>'


class SmtpConfig(db.Model):
    __tablename__ = 'smtp_config'  # 故意用独立表名，避免与现有表冲突
    
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), default='gmail', nullable=False)  # gmail / qq / custom 等
    mail_server = db.Column(db.String(100))
    mail_port = db.Column(db.Integer, default=587)
    mail_use_tls = db.Column(db.Boolean, default=True)
    mail_use_ssl = db.Column(db.Boolean, default=False)
    mail_username = db.Column(db.String(120))
    mail_password = db.Column(db.String(255))  # 暂时明文，生产环境可后续加密
    test_recipient = db.Column(db.String(120), default='')  # 用于一键测试的邮箱
    default_sender_name = db.Column(db.String(100), default='酒店家具官网')
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SmtpConfig {self.provider} - {self.mail_username}>'
