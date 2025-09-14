from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import (
    db, User, Opportunity, ProgramReview, JobReview, CompensationData, 
    ForumPost, ForumComment, Application, CalendarSlot, Message, Conversation
)
from sqlalchemy import desc
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access admin features.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user is admin by email (radnucleus@gmail.com)
        if current_user.email != 'radnucleus@gmail.com':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('opportunities.home'))
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard showing overview of all user-submitted data"""
    try:
        # Get counts of all user-submitted data
        stats = {
            'opportunities': Opportunity.query.count(),
            'program_reviews': ProgramReview.query.count(),
            'job_reviews': JobReview.query.count(),
            'compensation_data': CompensationData.query.filter_by(is_anonymous_submission=True).count(),
            'forum_posts': ForumPost.query.count(),
            'forum_comments': ForumComment.query.count(),
            'total_users': User.query.count()
        }
        
        # Get recent submissions
        recent_opportunities = Opportunity.query.order_by(desc(Opportunity.created_at)).limit(5).all()
        recent_program_reviews = ProgramReview.query.order_by(desc(ProgramReview.created_at)).limit(5).all()
        recent_job_reviews = JobReview.query.order_by(desc(JobReview.created_at)).limit(5).all()
        recent_forum_posts = ForumPost.query.order_by(desc(ForumPost.created_at)).limit(5).all()
        
        return render_template('admin/dashboard.html', 
                             stats=stats,
                             recent_opportunities=recent_opportunities,
                             recent_program_reviews=recent_program_reviews,
                             recent_job_reviews=recent_job_reviews,
                             recent_forum_posts=recent_forum_posts)
    except Exception as e:
        flash(f'Error loading admin dashboard: {str(e)}', 'error')
        return redirect(url_for('opportunities.home'))

@admin_bp.route('/opportunities')
@login_required
@admin_required
def opportunities():
    """List all job opportunities with admin controls"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        opportunities = Opportunity.query.order_by(desc(Opportunity.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/opportunities.html', opportunities=opportunities)
    except Exception as e:
        flash(f'Error loading opportunities: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/program-reviews')
@login_required
@admin_required
def program_reviews():
    """List all program reviews with admin controls"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        reviews = ProgramReview.query.order_by(desc(ProgramReview.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/program_reviews.html', reviews=reviews)
    except Exception as e:
        flash(f'Error loading program reviews: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/job-reviews')
@login_required
@admin_required
def job_reviews():
    """List all job reviews with admin controls"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        reviews = JobReview.query.order_by(desc(JobReview.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/job_reviews.html', reviews=reviews)
    except Exception as e:
        flash(f'Error loading job reviews: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/compensation-data')
@login_required
@admin_required
def compensation_data():
    """List all user-submitted compensation data with admin controls"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Only show user-submitted compensation data
        data = CompensationData.query.filter_by(is_anonymous_submission=True).order_by(
            desc(CompensationData.created_at)
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('admin/compensation_data.html', data=data)
    except Exception as e:
        flash(f'Error loading compensation data: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/forum-posts')
@login_required
@admin_required
def forum_posts():
    """List all forum posts with admin controls"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        posts = ForumPost.query.order_by(desc(ForumPost.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/forum_posts.html', posts=posts)
    except Exception as e:
        flash(f'Error loading forum posts: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

# API routes for deletion actions
@admin_bp.route('/api/delete/opportunity/<int:opportunity_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_opportunity(opportunity_id):
    """Delete a job opportunity"""
    try:
        opportunity = Opportunity.query.get_or_404(opportunity_id)
        
        # Delete related calendar slots first (cascade should handle this, but being explicit)
        CalendarSlot.query.filter_by(opportunity_id=opportunity_id).delete()
        
        # Delete related applications
        Application.query.filter_by(opportunity_id=opportunity_id).delete()
        
        # Delete related conversations and messages
        conversations = Conversation.query.filter_by(opportunity_id=opportunity_id).all()
        for conv in conversations:
            Message.query.filter_by(conversation_id=conv.id).delete()
            db.session.delete(conv)
        
        # Delete the opportunity
        db.session.delete(opportunity)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Opportunity deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete opportunity: {str(e)}'}), 500

@admin_bp.route('/api/delete/program-review/<int:review_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_program_review(review_id):
    """Delete a program review"""
    try:
        review = ProgramReview.query.get_or_404(review_id)
        db.session.delete(review)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Program review deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete program review: {str(e)}'}), 500

@admin_bp.route('/api/delete/job-review/<int:review_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_job_review(review_id):
    """Delete a job review"""
    try:
        review = JobReview.query.get_or_404(review_id)
        db.session.delete(review)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Job review deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete job review: {str(e)}'}), 500

@admin_bp.route('/api/delete/compensation-data/<int:data_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_compensation_data(data_id):
    """Delete compensation data"""
    try:
        data = CompensationData.query.get_or_404(data_id)
        
        # Only allow deletion of user-submitted data
        if not data.is_anonymous_submission:
            return jsonify({'error': 'Cannot delete MGMA survey data'}), 403
        
        db.session.delete(data)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Compensation data deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete compensation data: {str(e)}'}), 500

@admin_bp.route('/api/delete/forum-post/<int:post_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_forum_post(post_id):
    """Delete a forum post and all its comments"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        # Delete all comments first (cascade should handle this, but being explicit)
        ForumComment.query.filter_by(post_id=post_id).delete()
        
        # Delete the post
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Forum post deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete forum post: {str(e)}'}), 500

@admin_bp.route('/api/delete/forum-comment/<int:comment_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_forum_comment(comment_id):
    """Delete a forum comment"""
    try:
        comment = ForumComment.query.get_or_404(comment_id)
        
        # If this comment has replies, we should handle them appropriately
        # For now, we'll delete them too (cascade should handle this)
        replies = ForumComment.query.filter_by(parent_comment_id=comment_id).all()
        for reply in replies:
            db.session.delete(reply)
        
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Forum comment deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete forum comment: {str(e)}'}), 500

@admin_bp.route('/api/delete/user/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user and all their associated data"""
    try:
        # Prevent admin from deleting themselves
        if user_id == current_user.id:
            return jsonify({'error': 'Cannot delete your own admin account'}), 403
        
        user = User.query.get_or_404(user_id)
        
        # Delete all user's data in the correct order to avoid foreign key issues
        # 1. Delete messages in conversations
        user_conversations = Conversation.query.filter(
            (Conversation.resident_id == user_id) | (Conversation.employer_id == user_id)
        ).all()
        
        for conv in user_conversations:
            Message.query.filter_by(conversation_id=conv.id).delete()
            db.session.delete(conv)
        
        # 2. Delete applications
        Application.query.filter_by(resident_id=user_id).delete()
        
        # 3. Delete opportunities and related data
        user_opportunities = Opportunity.query.filter_by(employer_id=user_id).all()
        for opp in user_opportunities:
            CalendarSlot.query.filter_by(opportunity_id=opp.id).delete()
            Application.query.filter_by(opportunity_id=opp.id).delete()
            db.session.delete(opp)
        
        # 4. Delete forum-related data
        ForumComment.query.filter_by(author_id=user_id).delete()
        ForumPost.query.filter_by(author_id=user_id).delete()
        
        # 5. Delete reviews
        ProgramReview.query.filter_by(user_id=user_id).delete()
        JobReview.query.filter_by(user_id=user_id).delete()
        
        # 6. Delete profiles
        if user.role.value == 'resident':
            from app.models import ResidentProfile
            ResidentProfile.query.filter_by(user_id=user_id).delete()
        elif user.role.value == 'employer':
            from app.models import EmployerProfile
            EmployerProfile.query.filter_by(user_id=user_id).delete()
        
        # 7. Delete user sessions
        from app.models import UserSession
        UserSession.query.filter_by(user_id=user_id).delete()
        
        # 8. Finally delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User and all associated data deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete user: {str(e)}'}), 500
