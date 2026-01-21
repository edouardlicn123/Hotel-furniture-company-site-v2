# app/routes/cart.py
# Shopping Cart Inquiry Routes - Ultra-thin Route Layer (Final Enhanced Version 2026-01-16)
# Responsibilities: Only handle request reception, basic validation, call service layer, return standard JSON
# All business logic (email sending, cooldown, formatting, etc.) has been moved to inquiry_service.py

from flask import Blueprint, request, jsonify, render_template, current_app, session
from flask_login import current_user
from app.services.cart_service import CartService
from app.services.inquiry_service import InquiryService
from app.models import Settings

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


@cart_bp.route('/send-inquiry', methods=['POST'])
def send_inquiry():
    """
    Handle shopping cart inquiry request (supports both session-based and manual submission modes)
    
    Priority:
    1. For authenticated users with session cart → Force use session data (more secure)
    2. Otherwise use items submitted from frontend (supports offline/anonymous inquiries)
    """
    try:
        data = request.get_json(force=True) or {}
        
        # 1. Determine which items to use
        use_session_cart = current_user.is_authenticated and CartService.get_cart()
        
        if use_session_cart:
            # Authenticated users prioritize session cart (prevents frontend tampering)
            items = CartService.get_cart()
            current_app.logger.info(f"Using session cart to send inquiry, user: {current_user.username}")
        else:
            # Anonymous or offline mode, use frontend submitted data
            items = data.get('items', [])
            if not items:
                return jsonify({
                    'success': False,
                    'message': 'No products available for inquiry (items is empty)'
                }), 400

        # 2. Basic validation of items structure
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({
                'success': False,
                'message': 'Inquiry list cannot be empty'
            }), 400

        # 3. Get customer information (must be provided by frontend)
        customer_info = data.get('customer_info', {})
        if not isinstance(customer_info, dict):
            return jsonify({
                'success': False,
                'message': 'customer_info must be an object'
            }), 400

        required = ['name', 'email']
        missing = [f for f in required if not customer_info.get(f)]
        if missing:
            return jsonify({
                'success': False,
                'message': f'Please fill in required fields: {", ".join(missing)}'
            }), 400

        # Set default values for optional fields
        customer_info.setdefault('phone', '')
        customer_info.setdefault('company', '')
        customer_info.setdefault('message', '')

        # 4. Call core service layer
        success, message = InquiryService.send_inquiry(
            items=items,
            customer_info=customer_info,
            from_session=use_session_cart  # Pass info to service layer for logging distinction
        )

        if success:
            # Optional: Clear session cart after successful submission (depending on business needs)
            # CartService.clear_cart()
            return jsonify({
                'success': True,
                'message': message or 'Your inquiry has been successfully sent. We will reply within 24 hours!'
            })

        else:
            status_code = 429 if 'cooldown' in message.lower() or 'wait' in message.lower() else 400
            return jsonify({
                'success': False,
                'message': message
            }), status_code

    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid request format, please check JSON data'
        }), 400

    except Exception as e:
        current_app.logger.exception("Unexpected error occurred in inquiry route")
        return jsonify({
            'success': False,
            'message': 'System is busy, please try again later or contact support'
        }), 500


@cart_bp.route('/onlinecart')
def online_cart():
    """Display online inquiry cart page (shows content from session cart)"""
    settings = Settings.query.first() or Settings()
    cart_items = CartService.get_cart() if current_user.is_authenticated else []
    
    cart_summary = CartService.get_cart_summary()
    
    return render_template(
        'cart/onlinecart.html',
        settings=settings,
        cart_items=cart_items,
        cart_summary=cart_summary,
        is_authenticated=current_user.is_authenticated
    )


@cart_bp.route('/offlinecart')
def offline_cart():
    """Display offline product selection list page (for catalog/print mode)"""
    settings = Settings.query.first() or Settings()
    
    return render_template(
        'cart/offlinecart.html',
        settings=settings,
        # Optional: Add print optimization parameter in future
        print_mode=request.args.get('print') == '1'
    )


# Optional: API endpoint - Get current cart summary (commonly used by frontend AJAX)
@cart_bp.route('/summary', methods=['GET'])
def cart_summary():
    summary = CartService.get_cart_summary()
    return jsonify(summary)
