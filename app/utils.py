"""Utility functions for the application"""
from flask_login import current_user
from .models import ProgramReview, JobReview, CompensationData, db


def user_has_contributed():
    """Check if the current user has submitted at least one of: program review, job review, or compensation data"""
    if not current_user.is_authenticated:
        return False
    
    # Check if user has submitted a program review
    has_program_review = db.session.query(ProgramReview).filter_by(user_id=current_user.id).first() is not None
    
    # Check if user has submitted a job review
    has_job_review = db.session.query(JobReview).filter_by(user_id=current_user.id).first() is not None
    
    # Check if user has submitted compensation data
    has_compensation = db.session.query(CompensationData).filter_by(
        user_id=current_user.id, 
        is_anonymous_submission=True
    ).first() is not None
    
    return has_program_review or has_job_review or has_compensation

