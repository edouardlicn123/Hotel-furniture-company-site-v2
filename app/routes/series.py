# app/routes/series.py
# 前端专题系列路由 - 列表页 + 详情页

from flask import Blueprint, render_template
from app.models import FeatureSeries, Product

series_bp = Blueprint('series', __name__, url_prefix='/series')

@series_bp.route('/')
def list():
    """系列列表页 - 显示所有专题系列"""
    series_list = FeatureSeries.query.order_by(FeatureSeries.created_at.desc()).all()
    return render_template('series/list.html', series_list=series_list)

@series_bp.route('/<slug>')
def detail(slug):
    series = FeatureSeries.query.filter_by(slug=slug).first_or_404()
    
    # 精确匹配：只包含完整 slug 的产品（支持多系列逗号分隔）
    # 例如 slug="basic" 只匹配 featured_series 包含 ",basic," 或 "^basic," 或 ",basic$" 的记录
    products = Product.query.filter(
        db.or_(
            Product.featured_series == slug,  # 只有一个系列
            Product.featured_series.like(f'{slug},%'),     # 开头
            Product.featured_series.like(f'%,{slug}'),     # 中间
            Product.featured_series.like(f'%,{slug},%'),   # 中间（多于两个）
            Product.featured_series.like(f'{slug},')       # 结尾（兼容旧数据）
        )
    ).order_by(Product.created_at.desc()).all()
    
    return render_template('series/detail.html', series=series, products=products)
