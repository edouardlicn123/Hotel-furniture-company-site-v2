from flask import Blueprint, render_template
from app.models import Product

featured_bp = Blueprint('featured', __name__)

@featured_bp.route('/')
def featured_index():
    # 显示所有产品（或后续过滤有 featured_series 的产品）
    products = Product.query.all()
    return render_template('featured/index.html', products=products)

# 可添加具体系列页面（基于字符串匹配）
@featured_bp.route('/<series_name>')
def series_detail(series_name):
    # 过滤包含该系列名的产品（逗号分隔）
    products = Product.query.filter(Product.featured_series.like(f'%{series_name}%')).all()
    return render_template('featured/series.html', products=products, series_name=series_name)