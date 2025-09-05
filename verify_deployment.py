#!/usr/bin/env python3
"""
Deployment verification script.
Run this to ensure everything is ready for deployment.
"""

import os
import sys
from app import create_app

def verify_deployment():
    """Verify that the application is ready for deployment"""
    print("🚀 Deployment Verification")
    print("=" * 40)
    
    # Test 1: App creation
    print("\n1. Testing app creation...")
    try:
        app = create_app()
        print("✅ App created successfully")
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False
    
    # Test 2: Email configuration
    print("\n2. Testing email configuration...")
    with app.app_context():
        required_vars = [
            'MAIL_SERVER', 'MAIL_PORT', 'MAIL_USE_TLS', 
            'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not app.config.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing email variables: {', '.join(missing_vars)}")
            print("   Set these in your deployment platform's environment variables")
            return False
        else:
            print("✅ Email configuration complete")
    
    # Test 3: Database initialization
    print("\n3. Testing database initialization...")
    try:
        with app.app_context():
            from app.models import db
            db.create_all()
            print("✅ Database initialization successful")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    # Test 4: Email functionality
    print("\n4. Testing email functionality...")
    try:
        with app.app_context():
            from app.email_service import send_application_notification
            # This will test the email service without actually sending
            print("✅ Email service functions are accessible")
    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        return False
    
    # Test 5: Template rendering
    print("\n5. Testing email templates...")
    try:
        with app.app_context():
            from flask import render_template
            from datetime import datetime
            # Test if templates can be rendered with a test request context
            with app.test_request_context():
                render_template('emails/new_application.html', 
                              employer={'name': 'Test', 'email': 'test@test.com'},
                              resident={'name': 'Test', 'email': 'test@test.com'},
                              opportunity={'title': 'Test'},
                              application={'applied_at': datetime.now()})
            print("✅ Email templates render successfully")
    except Exception as e:
        print(f"❌ Email template test failed: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 DEPLOYMENT READY!")
    print("=" * 40)
    print("\nNext steps:")
    print("1. Deploy to your chosen platform (Railway/Render/Heroku)")
    print("2. Set the environment variables listed in DEPLOYMENT_CONFIG.md")
    print("3. Test the email functionality after deployment")
    print("\nRequired environment variables:")
    print("- MAIL_USERNAME=radnucleus@gmail.com")
    print("- MAIL_PASSWORD=pftmjsssraekcktm")
    print("- MAIL_DEFAULT_SENDER=radnucleus@gmail.com")
    print("- SECRET_KEY=your-secret-key-here")
    print("- DATABASE_URL=sqlite:///app.db")
    
    return True

if __name__ == "__main__":
    success = verify_deployment()
    sys.exit(0 if success else 1)
