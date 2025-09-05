#!/usr/bin/env python3
"""
Test script to verify email configuration and functionality.
Run this to check if emails are properly configured and can be sent.
"""

import os
from app import create_app
from app.models import db, User, Opportunity, Application, UserRole, ApplicationStatus
from datetime import datetime

def test_email_config():
    """Test email configuration"""
    app = create_app()
    
    with app.app_context():
        print("=== Email Configuration Test ===")
        print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
        print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
        print(f"MAIL_PASSWORD: {'***' if app.config.get('MAIL_PASSWORD') else 'None'}")
        print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
        print(f"MAIL_SUPPRESS_SEND: {app.config.get('MAIL_SUPPRESS_SEND')}")
        
        # Check if credentials are missing
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            print("\n❌ ERROR: Missing email credentials!")
            print("Please set the following environment variables:")
            print("export MAIL_USERNAME=your-email@gmail.com")
            print("export MAIL_PASSWORD=your-app-password")
            return False
        
        print("\n✅ Email configuration looks good!")
        return True

def test_email_sending():
    """Test actual email sending"""
    app = create_app()
    
    with app.app_context():
        print("\n=== Email Sending Test ===")
        
        # Check if we have test data
        employer = User.query.filter_by(role=UserRole.EMPLOYER).first()
        resident = User.query.filter_by(role=UserRole.RESIDENT).first()
        opportunity = Opportunity.query.first()
        
        if not all([employer, resident, opportunity]):
            print("❌ No test data found. Please create some users and opportunities first.")
            return False
        
        # Create a test application
        test_application = Application(
            opportunity_id=opportunity.id,
            resident_id=resident.id,
            status=ApplicationStatus.PENDING
        )
        db.session.add(test_application)
        db.session.commit()
        
        print(f"Testing with:")
        print(f"  Employer: {employer.name} ({employer.email})")
        print(f"  Resident: {resident.name} ({resident.email})")
        print(f"  Opportunity: {opportunity.title}")
        
        # Test application notification
        from app.email_service import send_application_notification
        print("\nTesting application notification...")
        result = send_application_notification(test_application.id)
        
        if result:
            print("✅ Application notification sent successfully!")
        else:
            print("❌ Failed to send application notification")
        
        # Test status notification
        from app.email_service import send_status_notification
        print("\nTesting status notification...")
        result = send_status_notification(test_application.id, "accepted")
        
        if result:
            print("✅ Status notification sent successfully!")
        else:
            print("❌ Failed to send status notification")
        
        # Clean up test application
        db.session.delete(test_application)
        db.session.commit()
        
        return True

if __name__ == "__main__":
    print("Radiology Job Board - Email Test")
    print("=" * 40)
    
    # Test configuration first
    if test_email_config():
        # Only test sending if config is good
        test_email_sending()
    else:
        print("\nPlease fix the email configuration before testing email sending.")
