from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import CompensationData, db
from .forms import CompensationSubmissionForm
from sqlalchemy import func

compensation_bp = Blueprint('compensation', __name__)

@compensation_bp.route('/compensation')
def index():
    """Display compensation data dashboard"""
    if not current_user.is_authenticated:
        return render_template("auth/login_required.html")
        
    # Get filter parameters
    year = request.args.get('year', type=int)
    region = request.args.get('region', '')
    specialty = request.args.get('specialty', '')
    practice_type = request.args.get('practice_type', '')
    
    # Build query
    query = CompensationData.query
    
    if year:
        query = query.filter(CompensationData.year == year)
    if region:
        query = query.filter(CompensationData.region.ilike(f'%{region}%'))
    if specialty:
        query = query.filter(CompensationData.specialty.ilike(f'%{specialty}%'))
    if practice_type:
        query = query.filter(CompensationData.practice_type == practice_type)
    
    # Get available filter options
    years = db.session.query(CompensationData.year).distinct().order_by(CompensationData.year.desc()).all()
    regions = db.session.query(CompensationData.region).distinct().order_by(CompensationData.region).all()
    specialties = db.session.query(CompensationData.specialty).distinct().order_by(CompensationData.specialty).all()
    
    # Get all possible practice types from the form definition
    all_practice_types = [
        'Private Practice', 'Academic', 'Hospital Employed', 'Government', 
        'Teleradiology', '1099 Contractor', 'Other'
    ]
    
    # Get summary statistics based on filtered data - only include non-null values for averages
    filtered_summary_stats = db.session.query(
        func.avg(CompensationData.total_compensation).label('avg_total_comp'),
        func.avg(CompensationData.base_salary).label('avg_base_salary'),
        func.avg(CompensationData.bonus).label('avg_bonus'),
        func.avg(CompensationData.rvu_per_work_rvu).label('avg_rvu_rate'),
        func.avg(CompensationData.hours_per_week).label('avg_hours'),
        func.count(CompensationData.id).label('total_records')
    ).filter(query.whereclause).first()
    
    # Get overall summary statistics (all data) for comparison
    overall_summary_stats = db.session.query(
        func.avg(CompensationData.total_compensation).label('avg_total_comp'),
        func.avg(CompensationData.base_salary).label('avg_base_salary'),
        func.avg(CompensationData.bonus).label('avg_bonus'),
        func.avg(CompensationData.rvu_per_work_rvu).label('avg_rvu_rate'),
        func.avg(CompensationData.hours_per_week).label('avg_hours'),
        func.count(CompensationData.id).label('total_records')
    ).first()
    
    # Use filtered stats if filters are applied, otherwise use overall stats
    summary_stats = filtered_summary_stats if any([year, region, specialty, practice_type]) else overall_summary_stats
    
    # Get compensation data
    compensation_data = query.order_by(CompensationData.year.desc(), CompensationData.total_compensation.desc()).limit(100).all()
    
    return render_template('compensation/index.html',
                         compensation_data=compensation_data,
                         years=[y[0] for y in years],
                         regions=[r[0] for r in regions],
                         specialties=[s[0] for s in specialties],
                         practice_types=all_practice_types,
                         summary_stats=summary_stats,
                         current_filters={'year': year, 'region': region, 'specialty': specialty, 'practice_type': practice_type})

@compensation_bp.route('/compensation/api/data')
def api_data():
    """API endpoint for compensation data"""
    year = request.args.get('year', type=int)
    region = request.args.get('region', '')
    specialty = request.args.get('specialty', '')
    
    query = CompensationData.query
    
    if year:
        query = query.filter(CompensationData.year == year)
    if region:
        query = query.filter(CompensationData.region.ilike(f'%{region}%'))
    if specialty:
        query = query.filter(CompensationData.specialty.ilike(f'%{specialty}%'))
    
    data = query.order_by(CompensationData.year.desc()).all()
    
    return jsonify([{
        'id': item.id,
        'year': item.year,
        'region': item.region,
        'specialty': item.specialty,
        'total_compensation': item.total_compensation,
        'base_salary': item.base_salary,
        'bonus': item.bonus,
        'rvu_total': item.rvu_total,
        'rvu_per_work_rvu': item.rvu_per_work_rvu,
        'work_rvus': item.work_rvus,
        'total_rvus': item.total_rvus,
        'hours_per_week': item.hours_per_week,
        'weeks_per_year': item.weeks_per_year,
        'source': item.source,
        'is_anonymous_submission': item.is_anonymous_submission,
        'practice_type': item.practice_type,
        'experience_years': item.experience_years
    } for item in data])


@compensation_bp.route('/compensation/submit', methods=['GET', 'POST'])
@login_required
def submit_compensation():
    """Submit anonymous compensation data"""
    form = CompensationSubmissionForm()
    
    if form.validate_on_submit():
        # Create new compensation data entry
        compensation_data = CompensationData(
            year=form.year.data,
            region=form.region.data,
            specialty=form.specialty.data,
            total_compensation=form.total_compensation.data,  # Already converted to int by validator
            base_salary=form.total_compensation.data,  # Set to total compensation for compatibility
            bonus=0,  # Set to 0 for compatibility
            rvu_total=int(form.total_yearly_rvu.data) if form.total_yearly_rvu.data else None,
            rvu_per_work_rvu=float(form.compensation_per_rvu.data) if form.compensation_per_rvu.data else None,
            work_rvus=int(form.total_yearly_rvu.data) if form.total_yearly_rvu.data else None,
            total_rvus=int(form.total_yearly_rvu.data) if form.total_yearly_rvu.data else None,
            hours_per_week=form.hours_per_week.data,
            weeks_per_year=48.0,  # Default to 48 weeks per year
            practice_type=form.practice_type.data,
            experience_years=None,  # No longer collected
            source='Community Submission',
            is_anonymous_submission=True
        )
        
        try:
            db.session.add(compensation_data)
            db.session.commit()
            flash('Thank you! Your anonymous compensation data has been submitted successfully.', 'success')
            return redirect(url_for('compensation.index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your data. Please try again.', 'error')
            print(f"Error submitting compensation data: {e}")
    
    return render_template('compensation/submit.html', form=form)
