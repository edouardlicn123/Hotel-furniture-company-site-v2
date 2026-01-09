# app/routes/series.py
# 前端专题系列路由 - 列表页 + 详情页

from flask import Blueprint, render_template
from app.models import FeatureSeries, Product
from app import db  # 关键：导入 db
from sqlalchemy import or_  # 推荐显式导入 or_

series_bp = Blueprint('series', __name__, url_prefix='/series')

@series_bp.route('/')
def list():
    """系列列表页 - 显示所有专题系列"""
    series_list = FeatureSeries.query.order_by(FeatureSeries.created_at.desc()).all()
    return render_template('series/list.html', series_list=series_list)

@series_bp.route('/<slug>')
def detail(slug):
    series = FeatureSeries.query.filter_by(slug=slug).first_or_404()
    
    # 精确匹配：查找 featured_series 字段中包含完整 slug 的产品
    # 支持多系列逗号分隔，如 "modern,basic,luxury"
    products = Product.query.filter(
        or_(
            Product.featured_series == slug,                    # 只有一个系列
            Product.featured_series.like(f'{slug},%'),          # 开头：slug,
            Product.featured_series.like(f'%,{slug}'),          # 结尾：,slug
            Product.featured_series.like(f'%,{slug},%'),        # 中间：,slug,
            Product.featured_series.like(f'{slug},')            # 兼容旧数据结尾无逗号
        )
    ).order_by(Product.created_at.desc()).all()
    
    return render_template('series/detail.html', series=series, products=products)
