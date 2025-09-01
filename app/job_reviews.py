from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from .models import db, UserRole, JobReview
from .forms import JobReviewForm
from sqlalchemy import desc

job_reviews_bp = Blueprint("job_reviews", __name__, url_prefix="/job-reviews")


@job_reviews_bp.route("/")
@login_required
def index():
    # Get filter parameters
    practice_name = request.args.get('practice_name', '').strip()
    state = request.args.get('state', '').strip()
    practice_type = request.args.get('practice_type', '').strip()
    
    # Build query with filters
    query = JobReview.query
    
    if practice_name:
        query = query.filter(JobReview.practice_name.ilike(f'%{practice_name}%'))
    
    if state:
        query = query.filter(JobReview.location.ilike(f'%{state}%'))
    
    if practice_type:
        query = query.filter(JobReview.practice_type == practice_type)
    
    # Get filtered reviews, ordered by most recent
    reviews = query.order_by(desc(JobReview.created_at)).all()
    
    return render_template("job_reviews/index.html", reviews=reviews)


@job_reviews_bp.route("/submit", methods=["GET", "POST"])
@login_required
def submit_review():
    # Allow both residents and employers to submit reviews
    if current_user.role not in [UserRole.RESIDENT, UserRole.EMPLOYER]:
        flash("Only registered users can submit job reviews.", "warning")
        return redirect(url_for("job_reviews.index"))
    
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
            return render_template("job_reviews/submit.html", form=form)
    
    return render_template("job_reviews/submit.html", form=form)


@job_reviews_bp.route("/<int:review_id>")
@login_required
def view_review(review_id):
    review = JobReview.query.get_or_404(review_id)
    return render_template("job_reviews/view.html", review=review)


@job_reviews_bp.route("/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
def edit_review(review_id):
    review = JobReview.query.get_or_404(review_id)
    
    # Only allow the author to edit their review
    if review.user_id != current_user.id:
        abort(403)
    
    form = JobReviewForm(obj=review)
    if form.validate_on_submit():
        # Handle optional rating fields - convert empty strings to None
        work_life_balance = int(form.work_life_balance.data) if form.work_life_balance.data and form.work_life_balance.data != '' else None
        compensation = int(form.compensation.data) if form.compensation.data and form.compensation.data != '' else None
        culture = int(form.culture.data) if form.culture.data and form.culture.data != '' else None
        growth_opportunities = int(form.growth_opportunities.data) if form.growth_opportunities.data and form.growth_opportunities.data != '' else None
        
        review.practice_name = form.practice_name.data
        review.location = form.location.data
        review.practice_type = form.practice_type.data if form.practice_type.data and form.practice_type.data != '' else None
        review.work_life_balance = work_life_balance
        review.compensation = compensation
        review.culture = culture
        review.growth_opportunities = growth_opportunities
        review.overall_rating = int(form.overall_rating.data)
        review.review_text = form.review_text.data
        review.is_anonymous = form.is_anonymous.data
        
        try:
            db.session.commit()
            flash("Your review has been updated successfully.", "success")
            return redirect(url_for("job_reviews.view_review", review_id=review.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating job review: {str(e)}")
            flash("An error occurred while updating your review. Please try again.", "error")
            return render_template("job_reviews/edit.html", form=form, review=review)
    
    return render_template("job_reviews/edit.html", form=form, review=review)


@job_reviews_bp.route("/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    review = JobReview.query.get_or_404(review_id)
    
    # Only allow the author to delete their review
    if review.user_id != current_user.id:
        abort(403)
    
    db.session.delete(review)
    db.session.commit()
    
    flash("Your review has been deleted successfully.", "success")
    return redirect(url_for("job_reviews.index"))
