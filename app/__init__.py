from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from .models import db, User
from config import Config
from sqlalchemy import text

# Global mail instance
mail = Mail()


def migrate_database_columns():
    """Automatically migrate missing database columns (runs only once)"""
    try:
        from flask import current_app
        db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        # Create migrations table if it doesn't exist
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) UNIQUE NOT NULL,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.session.commit()
        except:
            # For SQLite, use different syntax
            try:
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        migration_name VARCHAR(255) UNIQUE NOT NULL,
                        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.session.commit()
            except:
                pass  # Table might already exist
        
        # Check if timezone migration has already been completed
        result = db.session.execute(text("""
            SELECT migration_name FROM migrations 
            WHERE migration_name = 'add_timezone_column'
        """))
        timezone_migration_exists = result.fetchone() is not None
        
        # Check if forum photos migration has already been completed
        result = db.session.execute(text("""
            SELECT migration_name FROM migrations 
            WHERE migration_name = 'add_forum_photos_column'
        """))
        forum_photos_migration_exists = result.fetchone() is not None
        
        # Check if forum comment photos migration has already been completed
        result = db.session.execute(text("""
            SELECT migration_name FROM migrations 
            WHERE migration_name = 'add_forum_comment_photos_column'
        """))
        forum_comment_photos_migration_exists = result.fetchone() is not None
        
        # Check if interventional radiology enum migration has already been completed
        result = db.session.execute(text("""
            SELECT migration_name FROM migrations 
            WHERE migration_name = 'add_interventional_radiology_enum'
        """))
        interventional_radiology_migration_exists = result.fetchone() is not None
        
        if timezone_migration_exists and forum_photos_migration_exists and forum_comment_photos_migration_exists and interventional_radiology_migration_exists:
            current_app.logger.info("✅ All migrations already completed, skipping")
            return True
        
        # Migrate timezone column if needed
        if not timezone_migration_exists:
            if 'postgresql' in db_url.lower():
                # PostgreSQL
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user' AND column_name = 'timezone'
                """))
                timezone_exists = result.fetchone() is not None
                
                if not timezone_exists:
                    current_app.logger.info("Adding timezone column to user table...")
                    db.session.execute(text("""
                        ALTER TABLE "user" 
                        ADD COLUMN timezone VARCHAR(50)
                    """))
                    db.session.commit()
                    current_app.logger.info("✅ timezone column added successfully")
                else:
                    current_app.logger.info("✅ timezone column already exists")
                    
            elif 'sqlite' in db_url.lower():
                # SQLite
                result = db.session.execute(text("""
                    PRAGMA table_info(user)
                """))
                columns = [row[1] for row in result.fetchall()]
                timezone_exists = 'timezone' in columns
                
                if not timezone_exists:
                    current_app.logger.info("Adding timezone column to user table...")
                    db.session.execute(text("""
                        ALTER TABLE user 
                        ADD COLUMN timezone VARCHAR(50)
                    """))
                    db.session.commit()
                    current_app.logger.info("✅ timezone column added successfully")
                else:
                    current_app.logger.info("✅ timezone column already exists")
            else:
                current_app.logger.warning("Unsupported database type for migration")
                return False
            
            # Record timezone migration as completed
            db.session.execute(text("""
                INSERT INTO migrations (migration_name) 
                VALUES ('add_timezone_column')
                ON CONFLICT (migration_name) DO NOTHING
            """))
            db.session.commit()
        
        # Migrate forum photos column if needed
        if not forum_photos_migration_exists:
            if 'postgresql' in db_url.lower():
                # PostgreSQL
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'forum_post' AND column_name = 'photos'
                """))
                photos_exists = result.fetchone() is not None
                
                if not photos_exists:
                    current_app.logger.info("Adding photos column to forum_post table...")
                    db.session.execute(text("""
                        ALTER TABLE "forum_post" 
                        ADD COLUMN photos TEXT
                    """))
                    db.session.commit()
                    current_app.logger.info("✅ photos column added successfully")
                else:
                    current_app.logger.info("✅ photos column already exists")
                    
            elif 'sqlite' in db_url.lower():
                # SQLite
                result = db.session.execute(text("""
                    PRAGMA table_info(forum_post)
                """))
                columns = [row[1] for row in result.fetchall()]
                photos_exists = 'photos' in columns
                
                if not photos_exists:
                    current_app.logger.info("Adding photos column to forum_post table...")
                    db.session.execute(text("""
                        ALTER TABLE forum_post 
                        ADD COLUMN photos TEXT
                    """))
                    db.session.commit()
                    current_app.logger.info("✅ photos column added successfully")
                else:
                    current_app.logger.info("✅ photos column already exists")
            
            # Record forum photos migration as completed
            db.session.execute(text("""
                INSERT INTO migrations (migration_name) 
                VALUES ('add_forum_photos_column')
                ON CONFLICT (migration_name) DO NOTHING
            """))
            db.session.commit()
        
        # Migrate forum comment photos column if needed
        if not forum_comment_photos_migration_exists:
            if 'postgresql' in db_url.lower():
                # PostgreSQL
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'forum_comment' AND column_name = 'photos'
                """))
                comment_photos_exists = result.fetchone() is not None
                
                if not comment_photos_exists:
                    current_app.logger.info("Adding photos column to forum_comment table...")
                    db.session.execute(text("""
                        ALTER TABLE "forum_comment" 
                        ADD COLUMN photos TEXT
                    """))
                    db.session.commit()
                    current_app.logger.info("✅ forum_comment photos column added successfully")
                else:
                    current_app.logger.info("✅ forum_comment photos column already exists")
                    
            elif 'sqlite' in db_url.lower():
                # SQLite
                result = db.session.execute(text("""
                    PRAGMA table_info(forum_comment)
                """))
                columns = [row[1] for row in result.fetchall()]
                comment_photos_exists = 'photos' in columns
                
                if not comment_photos_exists:
                    current_app.logger.info("Adding photos column to forum_comment table...")
                    db.session.execute(text("""
                        ALTER TABLE forum_comment 
                        ADD COLUMN photos TEXT
                    """))
                    db.session.commit()
                    current_app.logger.info("✅ forum_comment photos column added successfully")
                else:
                    current_app.logger.info("✅ forum_comment photos column already exists")
            
            # Record forum comment photos migration as completed
            db.session.execute(text("""
                INSERT INTO migrations (migration_name) 
                VALUES ('add_forum_comment_photos_column')
                ON CONFLICT (migration_name) DO NOTHING
            """))
            db.session.commit()
        
        # ALWAYS attempt to migrate preferred_start_date column (critical for new feature)
        current_app.logger.info("🔄 Checking preferred_start_date column migration...")
        
        # Check if column exists directly, regardless of migration table
        column_exists = False
        try:
            if 'postgresql' in db_url.lower():
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'opportunity' AND column_name = 'preferred_start_date'
                """))
                column_exists = result.fetchone() is not None
            elif 'sqlite' in db_url.lower():
                result = db.session.execute(text("""
                    PRAGMA table_info(opportunity)
                """))
                columns = [row[1] for row in result.fetchall()]
                column_exists = 'preferred_start_date' in columns
        except Exception as e:
            current_app.logger.error(f"Error checking column existence: {e}")
            column_exists = False
        
        if not column_exists:
            current_app.logger.info("➕ Adding preferred_start_date column to opportunity table...")
            
            if 'postgresql' in db_url.lower():
                # PostgreSQL
                db.session.execute(text("""
                    ALTER TABLE opportunity 
                    ADD COLUMN preferred_start_date DATE
                """))
                db.session.commit()
                current_app.logger.info("✅ preferred_start_date column added successfully (PostgreSQL)")
                    
            elif 'sqlite' in db_url.lower():
                # SQLite
                db.session.execute(text("""
                    ALTER TABLE opportunity 
                    ADD COLUMN preferred_start_date DATE
                """))
                db.session.commit()
                current_app.logger.info("✅ preferred_start_date column added successfully (SQLite)")
            else:
                current_app.logger.warning("Unsupported database type for migration")
                return False
        else:
            current_app.logger.info("✅ preferred_start_date column already exists")
            
            # Record preferred_start_date migration as completed
            db.session.execute(text("""
                INSERT INTO migrations (migration_name) 
                VALUES ('add_preferred_start_date_column')
                ON CONFLICT (migration_name) DO NOTHING
            """))
            db.session.commit()
        
            
    except Exception as e:
        current_app.logger.error(f"Migration failed: {e}")
        db.session.rollback()
        return False
    
    return True


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database with error handling
    try:
        db.init_app(app)
        with app.app_context():
            # Test the database connection using SQLAlchemy 2.0 syntax
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.create_all()
            
            # Run automatic migration for missing columns
            try:
                migrate_database_columns()
            except Exception as migration_error:
                app.logger.warning(f"Migration failed (non-critical): {migration_error}")
            
            app.logger.info(f"Database initialized successfully with URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")
        # Set a flag to indicate database issues
        app.config['DATABASE_ERROR'] = str(e)
        # Continue with app creation even if database fails
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
    from .admin import admin_bp

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
    app.register_blueprint(admin_bp)
    
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

    # Database initialization is already handled above with proper error handling
    # This section is redundant and can cause issues if the database connection fails

    return app
