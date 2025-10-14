from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import CompensationData, db
from .forms import CompensationSubmissionForm
from sqlalchemy import func

compensation_bp = Blueprint('compensation', __name__)

# Specialty code to readable name mapping
SPECIALTY_DISPLAY_NAMES = {
    'non_clinical_other': 'Non-clinical/Other',
    'aerospace_medicine': 'Aerospace Medicine',
    'anesthesiology': 'Anesthesiology',
    'child_neurology': 'Child Neurology',
    'dermatology': 'Dermatology',
    'emergency_medicine': 'Emergency Medicine',
    'family_medicine': 'Family Medicine',
    'internal_medicine': 'Internal Medicine',
    'medical_genetics': 'Medical Genetics',
    'interventional_radiology': 'Interventional Radiology',
    'neurological_surgery': 'Neurological Surgery',
    'neurology': 'Neurology',
    'nuclear_medicine': 'Nuclear Medicine',
    'obstetrics_gynecology': 'Obstetrics and Gynecology',
    'occupational_environmental_medicine': 'Occupational and Environmental Medicine',
    'orthopaedic_surgery': 'Orthopaedic Surgery',
    'otolaryngology': 'Otolaryngology - Head and Neck Surgery',
    'pathology': 'Pathology-Anatomic and Clinical',
    'pediatrics': 'Pediatrics',
    'physical_medicine_rehabilitation': 'Physical Medicine and Rehabilitation',
    'plastic_surgery': 'Plastic Surgery',
    'psychiatry': 'Psychiatry',
    'radiation_oncology': 'Radiation Oncology',
    'radiology_diagnostic': 'Radiology-Diagnostic',
    'general_surgery': 'General Surgery',
    'thoracic_surgery': 'Thoracic Surgery',
    'urology': 'Urology',
    'vascular_surgery': 'Vascular Surgery'
}

def get_specialty_display_name(specialty_code):
    """Convert specialty code to readable display name"""
    if not specialty_code:
        return 'N/A'
    return SPECIALTY_DISPLAY_NAMES.get(specialty_code, specialty_code.replace('_', ' ').title())

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
    
    # Get all possible practice types from the form definition (matching job reviews form)
    all_practice_types = [
        'Private Practice', 'Academic', 'Hospital Employed', 'Government', 
        'Telemedicine', '1099 Contractor', 'Other'
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
    
    # Create list of specialties with both codes and display names for the filter dropdown
    specialty_options = [{'code': s[0], 'name': get_specialty_display_name(s[0])} for s in specialties]
    specialty_options.sort(key=lambda x: x['name'])  # Sort by display name
    
    return render_template('compensation/index.html',
                         compensation_data=compensation_data,
                         years=[y[0] for y in years],
                         regions=[r[0] for r in regions],
                         specialties=[s[0] for s in specialties],
                         specialty_options=specialty_options,
                         practice_types=all_practice_types,
                         summary_stats=summary_stats,
                         current_filters={'year': year, 'region': region, 'specialty': specialty, 'practice_type': practice_type},
                         get_specialty_display_name=get_specialty_display_name)

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
        # Calculate weeks per year based on vacation weeks (52 - vacation weeks)
        weeks_per_year = 52.0 - (form.weeks_vacation.data if form.weeks_vacation.data else 0)
        
        compensation_data = CompensationData(
            year=form.year.data,
            region=form.region.data,
            specialty=form.specialty.data,
            total_compensation=form.total_compensation.data,  # Already converted to int by validator
            base_salary=form.total_compensation.data,  # Set to total compensation for compatibility
            bonus=0,  # Set to 0 for compatibility
            rvu_total=form.total_yearly_rvu.data if form.total_yearly_rvu.data else None,
            rvu_per_work_rvu=form.compensation_per_rvu.data if form.compensation_per_rvu.data else None,
            work_rvus=form.total_yearly_rvu.data if form.total_yearly_rvu.data else None,
            total_rvus=form.total_yearly_rvu.data if form.total_yearly_rvu.data else None,
            hours_per_week=form.hours_per_week.data if form.hours_per_week.data else None,
            weeks_per_year=weeks_per_year,
            practice_type=form.practice_type.data,
            experience_years=None,  # No longer collected
            additional_notes=form.additional_notes.data,
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
            # Error submitting compensation data
    
    return render_template('compensation/submit.html', form=form)
