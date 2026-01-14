# app/services/cart_service.py
from flask import session, current_app
import json

class CartService:
    CART_KEY = 'cart_items'  # session key

    @staticmethod
    def get_cart():
        """获取当前购物车（返回产品列表）"""
        items = session.get(CartService.CART_KEY, [])
        return items  # [{id, name, code, image, qty}, ...]

    @staticmethod
    def add_to_cart(product_id: int, qty: int = 1):
        """添加产品到购物车"""
        from app.models import Product
        product = Product.query.get_or_404(product_id)

        items = CartService.get_cart()
        for item in items:
            if item['id'] == product_id:
                item['qty'] += qty
                break
        else:
            items.append({
                'id': product_id,
                'name': product.name,
                'code': product.product_code,
                'image': product.image,
                'qty': qty
            })
        session[CartService.CART_KEY] = items
        session.modified = True
        return len(items)

    @staticmethod
    def remove_from_cart(product_id: int):
        items = CartService.get_cart()
        items = [i for i in items if i['id'] != product_id]
        session[CartService.CART_KEY] = items
        session.modified = True

    @staticmethod
    def clear_cart():
        session.pop(CartService.CART_KEY, None)
        session.modified = True
