// cart.js
const CART_STORAGE_KEY = 'hotel_furniture_cart_2026_v1';

function getCart() {
    const data = localStorage.getItem(CART_STORAGE_KEY);
    return data ? JSON.parse(data) : [];
}

function saveCart(cartItems) {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cartItems));
    // 可在此觸發事件，讓其他頁面知道購物車變更
    window.dispatchEvent(new Event('cartUpdated'));
}

function addToCart(product) {
    let cart = getCart();
    // 檢查是否已存在
    const existing = cart.find(item => item.product_code === product.product_code);
    if (existing) {
        existing.quantity += (product.quantity || 1);
    } else {
        cart.push({
            product_code: product.product_code,
            name: product.name || '',
            quantity: product.quantity || 1,
            added_at: new Date().toISOString()
        });
    }
    saveCart(cart);
}

function clearCart() {
    localStorage.removeItem(CART_STORAGE_KEY);
    window.dispatchEvent(new Event('cartUpdated'));
}
