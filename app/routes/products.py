# app/routes/products.py
from flask import Blueprint, render_template, request, current_app
from sqlalchemy import desc
from app.models import Product, Category
from app import db

products_bp = Blueprint('products', __name__, url_prefix='/products')


@products_bp.route('/')
def list_products():
    """
    产品列表页 - 支持分页、按创建时间降序、分类筛选（可选）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('PRODUCTS_PER_PAGE', 12)  # 可在 config.py 中配置
    category_id = request.args.get('category', type=int)  # 可选：按分类筛选

    # 基础查询 - 按创建时间最新在前
    query = Product.query.order_by(desc(Product.created_at))

    # 如果有分类筛选
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # 分页
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    # 获取所有分类（用于左侧筛选菜单）
    categories = Category.query.order_by(Category.name).all()

    return render_template(
        'products/list.html',
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        current_category_id=category_id
    )


@products_bp.route('/<int:product_id>')
@products_bp.route('/<int:product_id>-<slug>')  # 兼容友好URL（可选）
def product_detail(product_id, slug=None):
    """
    产品详情页
    支持数字ID访问，也兼容带slug的友好URL（SEO更好）
    """
    # 只通过ID查找，忽略slug（防止有人手动改slug）
    product = Product.query.get_or_404(product_id)

    # 可选：加载相关产品（同系列或同分类）
    related_products = []
    if product.category_id:
        related_products = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id
        ).order_by(desc(Product.created_at)).limit(4).all()

    return render_template(
        'products/product_detail.html',
        product=product,
        related_products=related_products
    )
