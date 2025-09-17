#!/usr/bin/env python3
"""
Startup script for production deployment
Runs automatic migrations and starts the application
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main startup function"""
    logger.info("🚀 Starting application with automatic migrations...")
    
    try:
        # Import and create the app (this will trigger auto-migrations)
        from app import create_app
        app = create_app()
        
        # Log feature status
        with app.app_context():
            from app.enable_specialty_features import log_feature_status
            log_feature_status()
        
        logger.info("✅ Application startup completed successfully!")
        
        # Start the application
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
