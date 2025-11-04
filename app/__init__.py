# # app/__init__.py
# from flask import Flask
# import logging
# from logging.handlers import RotatingFileHandler
# import os

# def create_app(config_name=None):
#     # Create and configure the app
#     app = Flask(__name__)
    
#     # Configure logging
#     if not app.debug:
#         if not os.path.exists('logs'):
#             os.mkdir('logs')
#         file_handler = RotatingFileHandler('logs/health_tracker.log', maxBytes=10240, backupCount=10)
#         file_handler.setFormatter(logging.Formatter(
#             '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
#         ))
#         file_handler.setLevel(logging.INFO)
#         app.logger.addHandler(file_handler)
#         app.logger.setLevel(logging.INFO)
#         app.logger.info('Health Tracker startup')
    
#     # Register blueprints
#     from app.routers.reports import report_bp
#     app.register_blueprint(report_bp, url_prefix='/api')
    
#     # Add other blueprints here as needed
#     # from app.routes.user_routes import user_bp
#     # app.register_blueprint(user_bp, url_prefix='/api/users')
    
#     return app