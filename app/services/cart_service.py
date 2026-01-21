# app/services/cart_service.py
from flask import session, current_app
from app.models import Product
from app.utils.image_helper import get_image_url  # 重要！使用完整图片URL

class CartService:
    """购物车服务层 - 基于 session 实现（适合中小型网站）"""
    
    CART_KEY = 'cart_items'
    MAX_ITEMS = 50          # 防止 session 过大，可在后台设置
    MAX_QTY_PER_ITEM = 999  # 单品最大数量限制

    @staticmethod
    def get_cart():
        """
        获取当前用户的购物车内容
        返回: list of dicts
        """
        items = session.get(CartService.CART_KEY, [])
        # 增强：为每项添加完整图片URL（兼容 GitHub 模式）
        for item in items:
            if 'image' in item and item['image']:
                item['image_url'] = get_image_url('products', item['image'])
            else:
                item['image_url'] = current_app.url_for('static', filename='img/placeholder.jpg')
        return items

    @staticmethod
    def add_to_cart(product_id: int, qty: int = 1) -> tuple[bool, str]:
        """
        添加产品到购物车
        返回: (success: bool, message: str)
        """
        if qty < 1:
            return False, "数量必须大于 0"

        product = Product.query.get(product_id)
        if not product:
            return False, f"产品 ID {product_id} 不存在"

        items = CartService.get_cart()

        # 检查购物车是否已满
        if len(items) >= CartService.MAX_ITEMS and not any(i['id'] == product_id for i in items):
            return False, f"购物车已满（最多 {CartService.MAX_ITEMS} 种商品）"

        # 查找是否已存在
        for item in items:
            if item['id'] == product_id:
                new_qty = item['qty'] + qty
                if new_qty > CartService.MAX_QTY_PER_ITEM:
                    return False, f"单品数量不能超过 {CartService.MAX_QTY_PER_ITEM}"
                item['qty'] = new_qty
                break
        else:
            # 新增
            items.append({
                'id': product.id,
                'name': product.name,
                'code': product.product_code,
                'image': product.image,           # 原始文件名（用于后台管理）
                'image_url': get_image_url('products', product.image),
                'qty': qty,
                # 建议添加的关键展示信息（询价时有用）
                'length': product.length,
                'width': product.width,
                'height': product.height,
                'series': product.featured_series or "常规产品",
                'category': product.category.name if product.category else "未分类"
            })

        session[CartService.CART_KEY] = items
        session.modified = True
        return True, f"已将「{product.name}」加入购物车（数量：{qty}）"

    @staticmethod
    def update_quantity(product_id: int, qty: int) -> tuple[bool, str]:
        """更新指定商品数量"""
        if qty < 1:
            return CartService.remove_from_cart(product_id)

        items = CartService.get_cart()
        for item in items:
            if item['id'] == product_id:
                if qty > CartService.MAX_QTY_PER_ITEM:
                    return False, f"单品数量不能超过 {CartService.MAX_QTY_PER_ITEM}"
                item['qty'] = qty
                session[CartService.CART_KEY] = items
                session.modified = True
                return True, f"「{item['name']}」数量已更新为 {qty}"
        return False, f"购物车中未找到产品 ID {product_id}"

    @staticmethod
    def remove_from_cart(product_id: int) -> tuple[bool, str]:
        """移除指定商品"""
        items = CartService.get_cart()
        original_len = len(items)
        items = [i for i in items if i['id'] != product_id]
        
        if len(items) == original_len:
            return False, f"购物车中未找到产品 ID {product_id}"
            
        session[CartService.CART_KEY] = items
        session.modified = True
        return True, "商品已从购物车移除"

    @staticmethod
    def clear_cart() -> None:
        """清空购物车"""
        session.pop(CartService.CART_KEY, None)
        session.modified = True

    @staticmethod
    def get_cart_summary():
        """获取购物车统计信息（前端常用）"""
        items = CartService.get_cart()
        total_items = sum(item['qty'] for item in items)
        unique_items = len(items)
        
        return {
            'total_items': total_items,
            'unique_items': unique_items,
            'is_empty': unique_items == 0
        }

    @staticmethod
    def get_cart_for_email():
        """为邮件准备的格式化购物车内容"""
        items = CartService.get_cart()
        if not items:
            return "购物车为空"
            
        lines = ["选购产品清单："]
        for i, item in enumerate(items, 1):
            lines.append(
                f"{i}. {item['name']}（编号：{item['code']}）"
                f" × {item['qty']}"
                f"  尺寸：{item.get('length','?')}×{item.get('width','?')}×{item.get('height','?')}mm"
            )
        return "\n".join(lines)
