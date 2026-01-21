# app/error_handlers.py
from flask import render_template, jsonify, request, current_app
from werkzeug.exceptions import RequestEntityTooLarge


def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        current_app.logger.error(f"500 Internal Server Error: {str(e)}")
        return render_template('errors/500.html'), 500

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(error):
        if request.path.startswith('/admin'):
            return jsonify({
                'success': False,
                'message': 'File or request too large! Maximum allowed is 16MB.'
            }), 413

        return render_template(
            'errors/413.html',
            message='The uploaded content exceeds the maximum allowed size (16MB).'
        ), 413
