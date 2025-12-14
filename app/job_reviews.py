from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from .models import db, UserRole, JobReview
from .forms import JobReviewForm
from .utils import user_has_contributed
from sqlalchemy import desc, distinct
from datetime import datetime

job_reviews_bp = Blueprint("job_reviews", __name__, url_prefix="/job-reviews")


@job_reviews_bp.route("/")
@login_required
def index():
    # Check if user has contributed data
    if not user_has_contributed():
        return render_template("access_denied.html")
    
    # Get filter parameters
    practice_name = request.args.get('practice_name', '').strip()
    state = request.args.get('state', '').strip()
    practice_type = request.args.get('practice_type', '').strip()
    specialty = request.args.get('specialty', '').strip()
    
    # Build query with filters
    query = JobReview.query
    
    if practice_name:
        query = query.filter(JobReview.practice_name.ilike(f'%{practice_name}%'))
    
    if state:
        query = query.filter(JobReview.location.ilike(f'%{state}%'))
    
    if practice_type:
        query = query.filter(JobReview.practice_type == practice_type)
    
    if specialty:
        query = query.filter(JobReview.specialty == specialty)
    
    # Get filtered reviews, ordered by most recent
    reviews = query.order_by(desc(JobReview.created_at)).all()
    
    # Calculate average statistics only if a specific practice is filtered and has multiple reviews
    practice_stats = {}
    if reviews and practice_name:
        # Check if the filtered practice has multiple reviews
        practice_reviews = [review for review in reviews if review.practice_name == practice_name]
        
        if len(practice_reviews) > 1:
            # Calculate averages for numeric ratings
            overall_ratings = [r.overall_rating for r in practice_reviews if r.overall_rating is not None]
            work_life_ratings = [r.work_life_balance for r in practice_reviews if r.work_life_balance is not None]
            compensation_ratings = [r.compensation for r in practice_reviews if r.compensation is not None]
            culture_ratings = [r.culture for r in practice_reviews if r.culture is not None]
            growth_ratings = [r.growth_opportunities for r in practice_reviews if r.growth_opportunities is not None]
            
            practice_stats[practice_name] = {
                'review_count': len(practice_reviews),
                'overall_avg': round(sum(overall_ratings) / len(overall_ratings), 1) if overall_ratings else None,
                'work_life_avg': round(sum(work_life_ratings) / len(work_life_ratings), 1) if work_life_ratings else None,
                'compensation_avg': round(sum(compensation_ratings) / len(compensation_ratings), 1) if compensation_ratings else None,
                'culture_avg': round(sum(culture_ratings) / len(culture_ratings), 1) if culture_ratings else None,
                'growth_avg': round(sum(growth_ratings) / len(growth_ratings), 1) if growth_ratings else None,
                'overall_count': len(overall_ratings),
                'work_life_count': len(work_life_ratings),
                'compensation_count': len(compensation_ratings),
                'culture_count': len(culture_ratings),
                'growth_count': len(growth_ratings)
            }
    
    # Get all distinct practice names for dropdown
    practice_names = db.session.query(distinct(JobReview.practice_name))\
        .filter(JobReview.practice_name.isnot(None))\
        .filter(JobReview.practice_name != '')\
        .order_by(JobReview.practice_name)\
        .all()
    
    practice_names_list = [name[0] for name in practice_names if name[0]]
    
    return render_template("job_reviews/index.html", reviews=reviews, practice_names=practice_names_list, practice_stats=practice_stats)


@job_reviews_bp.route("/submit", methods=["GET", "POST"])
@login_required
def submit_review():
    # Allow both residents and employers to submit reviews
    if current_user.role not in [UserRole.RESIDENT, UserRole.EMPLOYER]:
        flash("Only registered users can submit job reviews.", "warning")
        return redirect(url_for("job_reviews.index"))
    
    # Get all distinct practice names for dropdown
    practice_names = db.session.query(distinct(JobReview.practice_name))\
        .filter(JobReview.practice_name.isnot(None))\
        .filter(JobReview.practice_name != '')\
        .order_by(JobReview.practice_name)\
        .all()
    
    practice_names_list = [name[0] for name in practice_names if name[0]]
    
    form = JobReviewForm()
    if form.validate_on_submit():
        # Handle optional rating fields - convert empty strings to None
        work_life_balance = int(form.work_life_balance.data) if form.work_life_balance.data and form.work_life_balance.data != '' else None
        compensation = int(form.compensation.data) if form.compensation.data and form.compensation.data != '' else None
        culture = int(form.culture.data) if form.culture.data and form.culture.data != '' else None
        growth_opportunities = int(form.growth_opportunities.data) if form.growth_opportunities.data and form.growth_opportunities.data != '' else None
        
        review = JobReview(
            user_id=current_user.id,
            practice_name=form.practice_name.data,
            location=form.location.data,
            practice_type=form.practice_type.data if form.practice_type.data and form.practice_type.data != '' else None,
            specialty=form.specialty.data if form.specialty.data and form.specialty.data != '' else None,
            work_life_balance=work_life_balance,
            compensation=compensation,
            culture=culture,
            growth_opportunities=growth_opportunities,
            overall_rating=int(form.overall_rating.data),
            review_text=form.review_text.data,
            is_anonymous=form.is_anonymous.data
        )
        
        db.session.add(review)
        try:
            db.session.commit()
            flash("Thank you for your review! It has been submitted successfully.", "success")
            return redirect(url_for("job_reviews.index"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error submitting job review: {str(e)}")
            flash("An error occurred while submitting your review. Please try again.", "error")
            return render_template("job_reviews/submit.html", form=form, practice_names=practice_names_list)
    else:
        # Form validation failed - show errors
        if request.method == 'POST':
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{form[field].label.text}: {error}", "error")
    
    return render_template("job_reviews/submit.html", form=form, practice_names=practice_names_list)


@job_reviews_bp.route("/<int:review_id>")
@login_required
def view_review(review_id):
    review = JobReview.query.get_or_404(review_id)
    return render_template("job_reviews/view.html", review=review)


@job_reviews_bp.route("/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
def edit_review(review_id):
    """Edit an existing job review - DISABLED: Users cannot edit their reviews"""
    abort(404)  # Return 404 to hide that the route exists


@job_reviews_bp.route("/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    """Delete a job review - DISABLED: Users cannot delete their reviews"""
    abort(404)  # Return 404 to hide that the route exists


@job_reviews_bp.route("/api/practice-names")
@login_required
def get_practice_names():
    """API endpoint to get practice names for autocomplete"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify([])
        
        # Get distinct practice names that contain the query string
        practice_names = db.session.query(distinct(JobReview.practice_name))\
            .filter(JobReview.practice_name.ilike(f'%{query}%'))\
            .limit(10)\
            .all()
        
        # Convert to list of strings
        names = [name[0] for name in practice_names if name[0]]
        
        return jsonify(names)
        
    except Exception as e:
        print(f"Error in get_practice_names: {e}")
        return jsonify({"error": "Failed to fetch practice names"}), 500


@job_reviews_bp.route("/api/test")
@login_required
def test_api():
    """Test endpoint to verify API connectivity"""
    return jsonify({
        "status": "success",
        "message": "API is working",
        "user_id": current_user.id,
        "timestamp": datetime.utcnow().isoformat()
    })
