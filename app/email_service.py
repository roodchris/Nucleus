from flask import current_app, render_template
from flask_mail import Message
from .models import User, Opportunity, Application, EmailVerification
from datetime import datetime, timedelta
import random
import string


def send_application_notification(application_id):
    """Send email notification to employer when a physician applies for a position"""
    try:
        from . import mail
        
        # Get application details
        application = Application.query.get(application_id)
        if not application:
            return False
            
        opportunity = Opportunity.query.get(application.opportunity_id)
        employer = User.query.get(opportunity.employer_id)
        resident = User.query.get(application.resident_id)
        
        if not all([opportunity, employer, resident]):
            return False
        
        # Create email message
        msg = Message(
            subject=f"New Application for {opportunity.title}",
            recipients=[employer.email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Render HTML template
        with current_app.test_request_context():
            msg.html = render_template(
                'emails/new_application.html',
                employer=employer,
                resident=resident,
                opportunity=opportunity,
                application=application
            )
        
        # Send email
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Error sending application notification: {e}")
        return False


def send_status_notification(application_id, status):
    """Send email notification to physician when application status changes"""
    try:
        from . import mail
        
        # Get application details
        application = Application.query.get(application_id)
        if not application:
            return False
            
        opportunity = Opportunity.query.get(application.opportunity_id)
        employer = User.query.get(opportunity.employer_id)
        resident = User.query.get(application.resident_id)
        
        if not all([opportunity, employer, resident]):
            return False
        
        # Create email message
        status_text = "accepted" if status == "accepted" else "rejected"
        msg = Message(
            subject=f"Application Update: {status_text.title()} for {opportunity.title}",
            recipients=[resident.email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Render HTML template
        with current_app.test_request_context():
            msg.html = render_template(
                'emails/status_update.html',
                employer=employer,
                resident=resident,
                opportunity=opportunity,
                application=application,
                status=status
            )
        
        # Send email
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Error sending status notification: {e}")
        return False


def send_bulk_status_notifications(application_ids, status):
    """Send email notifications to multiple physicians when their applications are rejected due to position being filled"""
    try:
        from . import mail
        
        messages = []
        
        for application_id in application_ids:
            application = Application.query.get(application_id)
            if not application:
                continue
                
            opportunity = Opportunity.query.get(application.opportunity_id)
            employer = User.query.get(opportunity.employer_id)
            resident = User.query.get(application.resident_id)
            
            if not all([opportunity, employer, resident]):
                continue
            
            # Create email message
            msg = Message(
                subject=f"Application Update: Position Filled for {opportunity.title}",
                recipients=[resident.email],
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            
            # Render HTML template
            with current_app.test_request_context():
                msg.html = render_template(
                    'emails/position_filled.html',
                    employer=employer,
                    resident=resident,
                    opportunity=opportunity,
                    application=application
                )
            
            messages.append(msg)
        
        # Send all emails
        if messages:
            mail.send(messages)
        
        return True
        
    except Exception as e:
        print(f"Error sending bulk status notifications: {e}")
        return False


def generate_verification_code():
    """Generate a random 5-digit verification code"""
    return ''.join(random.choices(string.digits, k=5))


def send_verification_email(email, verification_code):
    """Send email verification code to user"""
    try:
        from . import mail
        
        # Check if email sending is suppressed (for development)
        if current_app.config.get('MAIL_SUPPRESS_SEND', False):
            print(f"[DEV MODE] Verification code for {email}: {verification_code}")
            return True
        
        # Create email message
        msg = Message(
            subject="Verify your email address",
            recipients=[email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Render HTML template
        with current_app.test_request_context():
            msg.html = render_template(
                'emails/verification.html',
                verification_code=verification_code,
                email=email
            )
        
        # Send email
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Error sending verification email: {e}")
        # For development, print the code to console as fallback
        print(f"[FALLBACK] Verification code for {email}: {verification_code}")
        return True  # Return True for development purposes


def create_verification_record(email):
    """Create a new email verification record"""
    try:
        from . import db
        
        # Clean up any existing verification records for this email
        EmailVerification.query.filter_by(email=email).delete()
        
        # Generate verification code
        verification_code = generate_verification_code()
        
        # Create new verification record (expires in 15 minutes)
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        verification = EmailVerification(
            email=email,
            verification_code=verification_code,
            expires_at=expires_at
        )
        
        db.session.add(verification)
        db.session.commit()
        
        return verification_code
        
    except Exception as e:
        print(f"Error creating verification record: {e}")
        return None


def verify_email_code(email, code):
    """Verify the email verification code"""
    try:
        verification = EmailVerification.query.filter_by(
            email=email,
            verification_code=code,
            is_used=False
        ).first()
        
        if not verification:
            return False, "Invalid verification code"
        
        if verification.is_expired():
            return False, "Verification code has expired"
        
        # Mark as used
        verification.is_used = True
        from . import db
        db.session.commit()
        
        return True, "Email verified successfully"
        
    except Exception as e:
        print(f"Error verifying email code: {e}")
        return False, "Error verifying code"
