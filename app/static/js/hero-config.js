// app/static/js/hero-config.js - 全局统一 Hero 内容配置脚本
// 所有 Hero 内容（标题、子标题、背景图、按钮）集中在此文件管理
// 根据当前页面 URL 自动加载对应配置

// ============ Hero 内容配置表 ============
// 在这里添加或修改页面配置，新增页面只需加一条即可
const HERO_CONFIG = {
    // 首页
    '/': {
        title: window.COMPANY_NAME || 'Our company', // 使用注入的公司名，兜底默认。需配合head的js。
        subtitle: 'Professional Hotel Furniture Design & Manufacturing',
        background: '{{ url_for("static", filename="uploads/furniture_hero.jpg") }}',
        buttons: [
            { text: 'View Products', href: '/products', class: 'btn-primary' },
            { text: 'Contact Us', href: '/contact', class: 'btn-outline-dark' }
        ]
    },

    // 产品列表页
    '/products': {
        title: 'Our Products',
        subtitle: 'Premium Hotel Furniture Collection',
        background: '{{ url_for("static", filename="uploads/products_hero.jpg") }}'
        // 无 buttons（小 Hero 不显示按钮）
    },

    // 精选系列页（如果有）
    '/featured': {
        title: 'Featured Series',
        subtitle: 'Curated Luxury Collections for Modern Hospitality',
        background: '{{ url_for("static", filename="uploads/featured_hero.jpg") }}'
    },

    // 关于我们页
    '/about': {
        title: 'About Us',
        subtitle: 'Dedicated to Excellence in Hotel Furniture Manufacturing',
        background: '{{ url_for("static", filename="uploads/about_hero.jpg") }}'
    },

    // 联系我们页
    '/contact': {
        title: 'Contact Us',
        subtitle: 'Welcome to inquire about custom furniture solutions',
        background: '{{ url_for("static", filename="uploads/contact_hero.jpg") }}'
    }

    // ====== 新增页面请在这里添加配置 ======
    // 示例：
    // '/news': {
    //     title: 'Latest News',
    //     subtitle: 'Industry Insights & Company Updates',
    //     background: '{{ url_for("static", filename="uploads/news_hero.jpg") }}'
    // }
};

// ============ 自动加载逻辑 ============
document.addEventListener('DOMContentLoaded', function() {
    // 获取当前页面路径（去掉查询参数和哈希）
    let currentPath = window.location.pathname;

    // 处理末尾斜杠不一致（如 /products 和 /products/）
    if (currentPath.endsWith('/') && currentPath !== '/') {
        currentPath = currentPath.slice(0, -1);
    }

    // 查找匹配的配置（支持精确匹配）
    let config = HERO_CONFIG[currentPath] || HERO_CONFIG['/']; // 默认 fallback 到首页配置

    const titleEl = document.getElementById('hero-title');
    const subtitleEl = document.getElementById('hero-subtitle');
    const heroSection = document.getElementById('page-hero');
    const buttonsContainer = document.getElementById('hero-buttons');

    // 设置标题和副标题
    if (titleEl) titleEl.textContent = config.title || 'Welcome';
    if (subtitleEl) subtitleEl.textContent = config.subtitle || 'Explore Our Collections';

    // 设置背景图
    if (config.background && heroSection) {
        heroSection.style.backgroundImage = `url('${config.background}')`;
    }

    // 设置按钮（仅大 Hero 有 buttons 配置时生效）
    if (buttonsContainer && config.buttons && config.buttons.length > 0) {
        buttonsContainer.innerHTML = ''; // 清空占位
        config.buttons.forEach(btn => {
            const a = document.createElement('a');
            a.href = btn.href || '#';
            a.textContent = btn.text || 'Button';
            a.className = `btn ${btn.class || 'btn-primary'} me-3`;
            buttonsContainer.appendChild(a);
        });
    } else if (buttonsContainer) {
        buttonsContainer.innerHTML = ''; // 小 Hero 清空按钮区
    }
});
