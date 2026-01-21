document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('add-to-cart');
    if (!btn) return;

    btn.addEventListener('click', function () {
        const product = {
            code: this.dataset.productCode,
            name: this.dataset.productName,
            image: this.dataset.productImage || ''
        };

        let cart = JSON.parse(localStorage.getItem('inquiryCart') || '[]');

        // 防止重复添加（同 product_code）
        if (cart.some(item => item.code === product.code)) {
            alert('This product is already in your cart.');
            return;
        }

        cart.push(product);
        localStorage.setItem('inquiryCart', JSON.stringify(cart));
        alert('Added to cart successfully!');
    });
});
