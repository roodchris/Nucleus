from flask import Flask
from flask_login import LoginManager
from .models import db, User
from config import Config


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    from .auth import auth_bp
    from .opportunities import opp_bp
    from .chat import chat_bp, register_message_routes, get_unread_count
    from .forum import forum_bp
    from .compensation import compensation_bp
    from .program_reviews import program_reviews_bp
    from .knowledge_base import knowledge_base_bp
    from .job_reviews import job_reviews_bp
    from .api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(opp_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(compensation_bp)
    app.register_blueprint(program_reviews_bp)
    app.register_blueprint(knowledge_base_bp)
    app.register_blueprint(job_reviews_bp)
    app.register_blueprint(api_bp)
    
    # Register additional message routes
    register_message_routes(app)
    
    # Make helper functions available in templates
    @app.context_processor
    def utility_processor():
        return dict(get_unread_count=get_unread_count)
    
    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        import os
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        return send_from_directory(uploads_dir, filename)

    with app.app_context():
        db.create_all()

    return app
