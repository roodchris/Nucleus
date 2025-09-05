from flask import current_app, render_template
from flask_mail import Message
from .models import User, Opportunity, Application
from datetime import datetime


def send_application_notification(application_id):
    """Send email notification to employer when a radiologist applies for a position"""
    try:
        from flask_mail import Mail
        mail = Mail(current_app)
        
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
    """Send email notification to radiologist when application status changes"""
    try:
        from flask_mail import Mail
        mail = Mail(current_app)
        
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
    """Send email notifications to multiple radiologists when their applications are rejected due to position being filled"""
    try:
        from flask_mail import Mail
        mail = Mail(current_app)
        
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
