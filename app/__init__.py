from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from .models import db, User
from config import Config

# Global mail instance
mail = Mail()


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database with error handling and fallback
    try:
        db.init_app(app)
        with app.app_context():
            # Test the database connection using SQLAlchemy 2.0 syntax
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.create_all()
            app.logger.info("Database initialized successfully")
    except Exception as e:
        app.logger.error(f"PostgreSQL database initialization failed: {e}")
        # Fallback to SQLite if PostgreSQL fails
        try:
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
            # Re-initialize the database with the new URI
            with app.app_context():
                db.create_all()
            app.logger.info("Fallback to SQLite database successful")
        except Exception as sqlite_error:
            app.logger.error(f"SQLite fallback also failed: {sqlite_error}")
            # Continue with app creation even if both databases fail
            # This allows the app to start and show a proper error page
    
    mail.init_app(app)
    
    # Initialize CORS with configuration from config file
    CORS(app, 
         origins=app.config.get('CORS_ORIGINS', '*'), 
         supports_credentials=app.config.get('CORS_SUPPORTS_CREDENTIALS', True))

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
    from .wrvu_calculator import wrvu_bp
    from .api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(opp_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(compensation_bp)
    app.register_blueprint(program_reviews_bp)
    app.register_blueprint(knowledge_base_bp)
    app.register_blueprint(job_reviews_bp)
    app.register_blueprint(wrvu_bp)
    app.register_blueprint(api_bp)
    
    # Register additional message routes
    register_message_routes(app)
    
    # Add health check route
    @app.route('/health')
    def health_check():
        """Health check endpoint to diagnose issues"""
        try:
            # Test database connection using SQLAlchemy 2.0 syntax
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db_status = "OK"
            
            # Test if User table exists
            try:
                from .models import User
                user_count = User.query.count()
                tables_status = f"OK - User table exists with {user_count} users"
            except Exception as e:
                tables_status = f"ERROR - Tables issue: {str(e)}"
                
        except Exception as e:
            db_status = f"ERROR: {str(e)}"
            tables_status = "Not tested due to connection error"
        
        return {
            "status": "OK" if db_status == "OK" else "ERROR",
            "database": db_status,
            "tables": tables_status,
            "database_uri": app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set'),
            "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
            "flask_version": __import__('flask').__version__,
            "sqlalchemy_version": __import__('sqlalchemy').__version__
        }
    
    # Add custom Jinja2 filters
    @app.template_filter('from_json')
    def from_json_filter(json_string):
        """Convert JSON string to Python object"""
        import json
        try:
            return json.loads(json_string) if json_string else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    # Make helper functions available in templates
    @app.context_processor
    def utility_processor():
        from .opportunities import get_zip_location
        return dict(get_unread_count=get_unread_count, get_zip_location=get_zip_location)
    
    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        import os
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        return send_from_directory(uploads_dir, filename)

    with app.app_context():
        try:
            db.create_all()
            print(f"✅ Database initialized successfully with URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
            raise

    return app
