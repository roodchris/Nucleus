from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from .models import ProgramReview, db
from .utils import user_has_contributed
from sqlalchemy import func
import json
import os

program_reviews_bp = Blueprint('program_reviews', __name__)

# Note: Programs are now loaded dynamically via JavaScript from program-data.js
# This provides access to all 1389+ medical programs from ERAS data
# No longer needed to maintain a Python list since frontend handles it

# Keep the radiology programs for backward compatibility (but we'll use ALL_PROGRAMS now)
RADIOLOGY_PROGRAMS = [
    "Alabama - Baptist Health Program",
    "Alabama - University of Alabama Hospital (Birmingham) Program",
    "Alabama - USA Health Program",
    "Arizona - Creighton University School of Medicine (Phoenix) Program",
    "Arizona - Mayo Clinic College of Medicine and Science (Arizona) Program",
    "Arizona - University of Arizona College of Medicine-Tucson Program",
    "Arkansas - University of Arkansas for Medical Sciences (UAMS) College of Medicine Program",
    "California - Arrowhead Regional Medical Center Program",
    "California - KPC Health Program",
    "California - Loma Linda University Health Education Consortium Program",
    "California - Cedars-Sinai Medical Center Program",
    "California - Kaiser Permanente Southern California (Los Angeles) Program",
    "California - UCLA David Geffen School of Medicine/UCLA Medical Center Program",
    "California - University of Southern California/Los Angeles General Medical Center (USC/LA General) Program",
    "California - Riverside University Health System Program",
    "California - University of California (Irvine) Program",
    "California - HCA Healthcare Riverside Program",
    "California - University of California Davis Health Program",
    "California - University of California (San Diego) Medical Center Program",
    "California - University of California (San Francisco) Program",
    "California - Santa Clara Valley Medical Center Program",
    "California - Santa Barbara Cottage Hospital Program",
    "California - Stanford Health Care-Sponsored Stanford University Program",
    "California - Los Angeles County-Harbor-UCLA Medical Center Program",
    "Colorado - University of Colorado Program",
    "Connecticut - Bridgeport Hospital/Yale University Program",
    "Connecticut - Quinnipiac University Frank H. Netter MD School of Medicine/St Vincent's Medical Center Program",
    "Connecticut - University of Connecticut Program",
    "Connecticut - Hartford Hospital Program",
    "Connecticut - Yale-New Haven Medical Center Program",
    "Connecticut - Nuvance Health Consortium (Norwalk Hospital) Program",
    "Delaware - Christiana Care Health Services Program",
    "District of Columbia - George Washington University Program",
    "District of Columbia - MedStar Health Georgetown University Program",
    "Florida - HCA Florida Healthcare/Aventura Hospital Program",
    "Florida - University of Florida Program",
    "Florida - Mayo Clinic College of Medicine and Science (Jacksonville) Program",
    "Florida - University of Florida College of Medicine Jacksonville Program",
    "Florida - Florida International University / Baptist Health Program",
    "Florida - University of Miami/Jackson Health System Program",
    "Florida - Mount Sinai Medical Center of Florida Program",
    "Florida - AdventHealth Florida Program",
    "Florida - Larkin Community Hospital Program",
    "Florida - University of South Florida Morsani Program",
    "Florida - HCA Florida Healthcare/USF Morsani College of Medicine GME - Tampa North/Trinity Hospital Program",
    "Georgia - Emory University School of Medicine Program",
    "Georgia - Medical College of Georgia Program",
    "Georgia - HCA Healthcare/Mercer University School of Medicine/Memorial Health University Medical Center Program",
    "Hawaii - Tripler Army Medical Center Program",
    "Illinois - Advocate Health Care/Advocate Illinois Masonic Medical Center Program",
    "Illinois - Cook County Health and Hospitals System Program",
    "Illinois - McGaw Medical Center of Northwestern University Program",
    "Illinois - Rush University Medical Center Program",
    "Illinois - University of Chicago Program",
    "Illinois - University of Illinois College of Medicine at Chicago Program",
    "Illinois - Ascension Illinois/Saint Francis Program",
    "Illinois - Loyola University Medical Center Program",
    "Illinois - Franciscan Health Olympia Fields Program",
    "Illinois - University of Illinois College of Medicine at Peoria Program",
    "Illinois - Southern Illinois University Program",
    "Indiana - Indiana University School of Medicine Program",
    "Iowa - University of Iowa Health Care Medical Center Program",
    "Kansas - University of Kansas School of Medicine Program",
    "Kansas - University of Kansas (Wichita) Program",
    "Kentucky - University of Kentucky College of Medicine Program",
    "Kentucky - University of Louisville School of Medicine Program",
    "Louisiana - Louisiana State University Program",
    "Louisiana - Ochsner Clinic Foundation Program",
    "Louisiana - Tulane University Program",
    "Louisiana - Louisiana State University (Shreveport) Program",
    "Maine - Maine Medical Center Program",
    "Maryland - Johns Hopkins University Program",
    "Maryland - University of Maryland Program",
    "Massachusetts - Beth Israel Deaconess Medical Center Program",
    "Massachusetts - Boston University Medical Center Program",
    "Massachusetts - Mass General Brigham/Brigham and Women's Hospital/Harvard Medical School Program",
    "Massachusetts - Mass General Brigham/Massachusetts General Hospital/Harvard Medical School Program",
    "Massachusetts - Tufts Medical Center Program",
    "Massachusetts - Lahey Clinic Program",
    "Massachusetts - Mount Auburn Hospital Program",
    "Massachusetts - UMass Chan - Baystate Program",
    "Massachusetts - St Vincent Hospital Program",
    "Massachusetts - UMass Chan Medical School Program",
    "Michigan - University of Michigan Health System Program",
    "Michigan - Corewell Health (Dearborn) Program",
    "Michigan - Detroit Medical Center/Wayne State University Program",
    "Michigan - Henry Ford Health/Henry Ford Hospital Program",
    "Michigan - Corewell Health (Farmington Hills) Program",
    "Michigan - Corewell Health – Grand Rapids/Michigan State University Program",
    "Michigan - McLaren Health Care/Oakland/MSU Program",
    "Michigan - Trinity Health Oakland/Wayne State University Program",
    "Michigan - Corewell Health William Beaumont University Hospital Program",
    "Michigan - Henry Ford Providence Hospital Program",
    "Minnesota - University of Minnesota Program",
    "Minnesota - Mayo Clinic College of Medicine and Science (Rochester) Program",
    "Mississippi - University of Mississippi Medical Center Program",
    "Missouri - University of Missouri-Columbia Program",
    "Missouri - University of Missouri-Kansas City School of Medicine Program",
    "Missouri - SSM Health/Saint Louis University School of Medicine Program",
    "Missouri - Washington University/B-JH/SLCH Consortium Program",
    "Nebraska - Creighton University School of Medicine (Omaha) Program",
    "Nebraska - University of Nebraska Medical Center Program",
    "Nevada - University of Nevada Las Vegas School of Medicine Program",
    "New Hampshire - Dartmouth-Hitchcock Medical Center Program",
    "New Jersey - Atlantic Health System Program",
    "New Jersey - Rutgers New Jersey Medical School Program",
    "New Jersey - Rutgers Robert Wood Johnson Medical School Program",
    "New Mexico - University of New Mexico Program",
    "New York - Albert Einstein College of Medicine Program",
    "New York - Albany Medical Center Program",
    "New York - Icahn School of Medicine at Mount Sinai Program",
    "New York - New York Presbyterian Hospital (Columbia Campus) Program",
    "New York - New York Presbyterian Hospital (Cornell Campus) Program",
    "New York - New York University Grossman School of Medicine Program",
    "New York - State University of New York at Buffalo Program",
    "New York - State University of New York Downstate Medical Center Program",
    "New York - State University of New York Upstate Medical University Program",
    "New York - University of Rochester Program",
    "North Carolina - Atrium Health Carolinas Medical Center Program",
    "North Carolina - Duke University Hospital Program",
    "North Carolina - East Carolina University Program",
    "North Carolina - University of North Carolina Hospitals Program",
    "North Carolina - Wake Forest University School of Medicine Program",
    "North Dakota - University of North Dakota Program",
    "Ohio - Case Western Reserve University/University Hospitals Cleveland Medical Center Program",
    "Ohio - Cleveland Clinic Foundation Program",
    "Ohio - Ohio State University Hospital Program",
    "Ohio - University of Cincinnati Medical Center Program",
    "Ohio - University of Toledo Program",
    "Oklahoma - University of Oklahoma Health Sciences Center Program",
    "Oregon - Oregon Health & Science University Program",
    "Pennsylvania - Allegheny Health Network Program",
    "Pennsylvania - Drexel University College of Medicine Program",
    "Pennsylvania - Penn State Milton S Hershey Medical Center Program",
    "Pennsylvania - Temple University Hospital Program",
    "Pennsylvania - Thomas Jefferson University Program",
    "Pennsylvania - University of Pennsylvania Program",
    "Pennsylvania - University of Pittsburgh Medical Center Program",
    "Rhode Island - Brown University Program",
    "South Carolina - Medical University of South Carolina Program",
    "South Carolina - Prisma Health-Upstate Program",
    "South Dakota - University of South Dakota Program",
    "Tennessee - University of Tennessee Program",
    "Tennessee - Vanderbilt University Medical Center Program",
    "Texas - Baylor College of Medicine Program",
    "Texas - Brooke Army Medical Center Program",
    "Texas - Texas A&M College of Medicine Program",
    "Texas - Texas Tech University Health Sciences Center Program",
    "Texas - University of Texas at Austin Dell Medical School Program",
    "Texas - University of Texas Health Science Center at Houston Program",
    "Texas - University of Texas Health Science Center at San Antonio Program",
    "Texas - University of Texas Medical Branch Program",
    "Texas - University of Texas Southwestern Medical School Program",
    "Utah - University of Utah Program",
    "Vermont - University of Vermont Medical Center Program",
    "Virginia - Eastern Virginia Medical School Program",
    "Virginia - University of Virginia Program",
    "Virginia - Virginia Commonwealth University Health System Program",
    "Washington - Madigan Army Medical Center Program",
    "Washington - University of Washington Program",
    "West Virginia - West Virginia University Program",
    "Wisconsin - Medical College of Wisconsin Affiliated Hospitals Program",
    "Wisconsin - University of Wisconsin Hospitals and Clinics Program",
    "Wyoming - University of Washington (Casper) Program"
]

@program_reviews_bp.route('/program-reviews')
def index():
    """Display program reviews dashboard"""
    if not current_user.is_authenticated:
        return render_template("auth/login_required.html")
    
    # Check if user has contributed data
    if not user_has_contributed():
        return render_template("access_denied.html")
        
    program_name = request.args.get('program', '')
    specialty = request.args.get('specialty', '')
    
    if program_name:
        # Get reviews for specific program
        query = ProgramReview.query.filter_by(program_name=program_name)
        
        # Add specialty filter if provided
        if specialty:
            query = query.filter_by(specialty=specialty)
            
        reviews = query.order_by(ProgramReview.created_at.desc()).all()
        
        # Calculate average ratings with individual counts
        avg_query = db.session.query(
            func.avg(ProgramReview.educational_quality).label('avg_educational'),
            func.avg(ProgramReview.work_life_balance).label('avg_work_life'),
            func.avg(ProgramReview.attending_quality).label('avg_attending'),
            func.avg(ProgramReview.facilities_quality).label('avg_facilities'),
            func.avg(ProgramReview.research_opportunities).label('avg_research'),
            func.avg(ProgramReview.culture).label('avg_culture'),
            func.count(ProgramReview.id).label('total_reviews'),
            func.count(ProgramReview.educational_quality).label('educational_count'),
            func.count(ProgramReview.work_life_balance).label('work_life_count'),
            func.count(ProgramReview.attending_quality).label('attending_count'),
            func.count(ProgramReview.facilities_quality).label('facilities_count'),
            func.count(ProgramReview.research_opportunities).label('research_count'),
            func.count(ProgramReview.culture).label('culture_count')
        ).filter_by(program_name=program_name)
        
        # Add specialty filter to average calculation if provided
        if specialty:
            avg_query = avg_query.filter_by(specialty=specialty)
            
        avg_ratings = avg_query.first()
        
        return render_template('program_reviews/program.html',
                             program_name=program_name,
                             reviews=reviews,
                             avg_ratings=avg_ratings,
                             current_specialty=specialty)
    else:
        # Get all individual reviews, similar to job reviews page
        query = ProgramReview.query
        
        # Add specialty filter if provided
        if specialty:
            query = query.filter_by(specialty=specialty)
        
        # Get all individual reviews, ordered by most recent
        reviews = query.order_by(ProgramReview.created_at.desc()).all()
        
    return render_template('program_reviews/index.html',
                         reviews=reviews,
                         all_programs=RADIOLOGY_PROGRAMS,  # For backward compatibility
                         current_specialty=specialty)

@program_reviews_bp.route('/program-reviews/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    """Edit an existing program review - DISABLED: Users cannot edit their reviews"""
    abort(404)  # Return 404 to hide that the route exists


@program_reviews_bp.route('/program-reviews/new', methods=['GET', 'POST'])
@login_required
def new_review():
    """Create a new program review"""
    if request.method == 'POST':
        program_name = request.form.get('program_name')
        specialty = request.form.get('specialty', '')
        educational_quality = int(request.form.get('educational_quality'))
        work_life_balance = int(request.form.get('work_life_balance'))
        attending_quality = int(request.form.get('attending_quality'))
        facilities_quality = int(request.form.get('facilities_quality'))
        research_opportunities = int(request.form.get('research_opportunities'))
        culture = int(request.form.get('culture'))
        comments = request.form.get('comments')
        anonymous = bool(request.form.get('anonymous'))  # Checkbox value
        
        # Validate ratings
        if not all(1 <= rating <= 5 for rating in [educational_quality, work_life_balance, attending_quality, 
                                                   facilities_quality, research_opportunities, culture]):
            flash('All ratings must be between 1 and 5', 'error')
            return redirect(request.url)
        
        # Create review
        review = ProgramReview(
            program_name=program_name,
            user_id=current_user.id,
            specialty=specialty if specialty else None,
            educational_quality=educational_quality,
            work_life_balance=work_life_balance,
            attending_quality=attending_quality,
            facilities_quality=facilities_quality,
            research_opportunities=research_opportunities,
            culture=culture,
            comments=comments,
            anonymous=anonymous
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('program_reviews.index', program=program_name))
    
    return render_template('program_reviews/new.html')
