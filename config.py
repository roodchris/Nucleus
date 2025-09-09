import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    
    # Database configuration with environment variable support
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Debug: Print environment variables (remove in production)
    # print(f"DEBUG: DATABASE_URL from env: {DATABASE_URL}")
    # print(f"DEBUG: All env vars with DATABASE: {[k for k in os.environ.keys() if 'DATABASE' in k]}")
    
    # If DATABASE_URL is not set, try to construct it from individual components
    if not DATABASE_URL:
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT", "5432")
        DB_NAME = os.getenv("DB_NAME")
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        
        if all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
            DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            # print(f"DEBUG: Constructed DATABASE_URL from components: {DATABASE_URL}")
    
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        # Convert postgres:// to postgresql:// for newer versions of SQLAlchemy
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Use psycopg3 driver for PostgreSQL connections (compatible with Python 3.13+)
    if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
        # Replace postgresql:// with postgresql+psycopg:// to use psycopg3 driver
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    
    # Fallback to SQLite if DATABASE_URL is not available or invalid
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///app.db"
    
    # Ensure SQLALCHEMY_DATABASE_URI is always set
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    
    # Debug: Print final database URI
    # print(f"DEBUG: Final SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    WTF_CSRF_TIME_LIMIT = None
    TEMPLATES_AUTO_RELOAD = True
    
    # Session configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    
    # Email configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "radnucleus@gmail.com")
    MAIL_SUPPRESS_SEND = os.getenv("MAIL_SUPPRESS_SEND", "false").lower() in ["true", "on", "1"]
    
    # CORS configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_SUPPORTS_CREDENTIALS = True


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
