from flask import Blueprint, render_template
from app.models import Product, Category

products_bp = Blueprint('products', __name__)

@products_bp.route('/')
def list_products():
    categories = Category.query.all()
    products = Product.query.all()
    return render_template('products/list.html', categories=categories, products=products)

@products_bp.route('/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('products/product_detail.html', product=product)  