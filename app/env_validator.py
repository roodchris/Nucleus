"""
Environment variable validation system
Ensures all required environment variables are properly set
"""

import logging
import os

logger = logging.getLogger(__name__)

def validate_environment_variables():
    """Validate that all required environment variables are properly set"""
    
    required_vars = {
        'DATABASE_URL': 'PostgreSQL database connection string',
        'SECRET_KEY': 'Flask secret key for sessions',
        'MAIL_USERNAME': 'Email service username',
        'MAIL_PASSWORD': 'Email service password',
        'MAIL_DEFAULT_SENDER': 'Default email sender address'
    }
    
    optional_vars = {
        'CORS_ORIGINS': 'CORS allowed origins (defaults to *)'
    }
    
    issues = []
    warnings = []
    
    logger.info("🔍 Validating environment variables...")
    
    # Check required variables
    for var_name, description in required_vars.items():
        value = os.environ.get(var_name)
        if not value:
            issues.append(f"Missing required variable: {var_name} ({description})")
            logger.error(f"❌ Missing: {var_name}")
        else:
            # Validate DATABASE_URL format for PostgreSQL
            if var_name == 'DATABASE_URL' and value:
                if not value.startswith('postgresql://'):
                    issues.append(f"DATABASE_URL should start with 'postgresql://' for PostgreSQL")
                    logger.error(f"❌ Invalid DATABASE_URL format: should start with postgresql://")
                elif 'localhost' in value:
                    warnings.append(f"DATABASE_URL points to localhost - ensure this is correct for production")
                    logger.warning(f"⚠️  DATABASE_URL uses localhost")
            
            logger.info(f"✅ Found: {var_name}")
    
    # Check optional variables
    for var_name, description in optional_vars.items():
        value = os.environ.get(var_name)
        if value:
            logger.info(f"✅ Optional: {var_name} = {value}")
        else:
            logger.info(f"ℹ️  Optional: {var_name} not set ({description})")
    
    # Check for database connection issues that could affect enum migration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Check for potential connection issues
        if 'psycopg' not in database_url and 'postgresql' in database_url:
            warnings.append("DATABASE_URL uses postgresql:// - consider postgresql+psycopg:// for better compatibility")
            logger.warning("⚠️  DATABASE_URL format may affect enum operations")
        
        # Check for SSL requirements
        if 'sslmode' not in database_url and 'render.com' in database_url:
            warnings.append("DATABASE_URL for Render may need sslmode parameter")
            logger.warning("⚠️  DATABASE_URL may need SSL configuration for Render")
    
    # Report results
    if issues:
        logger.error(f"❌ Environment validation failed - {len(issues)} issue(s):")
        for issue in issues:
            logger.error(f"    - {issue}")
        return False
    
    if warnings:
        logger.warning(f"⚠️  Environment validation warnings - {len(warnings)} warning(s):")
        for warning in warnings:
            logger.warning(f"    - {warning}")
    
    if not issues and not warnings:
        logger.info("✅ All environment variables properly configured")
    
    return True

def get_environment_status():
    """Get detailed environment status for monitoring"""
    status = {
        'validation_passed': validate_environment_variables(),
        'database_url_set': bool(os.environ.get('DATABASE_URL')),
        'secret_key_set': bool(os.environ.get('SECRET_KEY')),
        'mail_configured': all([
            os.environ.get('MAIL_USERNAME'),
            os.environ.get('MAIL_PASSWORD'),
            os.environ.get('MAIL_DEFAULT_SENDER')
        ]),
        'detected_typos': []
    }
    
    # Check for database connection format issues
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url:
        if 'psycopg' not in database_url and 'postgresql' in database_url:
            status['detected_typos'].append('DATABASE_URL may need postgresql+psycopg:// format')
        if 'sslmode' not in database_url and 'render.com' in database_url:
            status['detected_typos'].append('DATABASE_URL may need SSL configuration for Render')
    
    return status
