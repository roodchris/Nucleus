from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import ProgramReview, db
from sqlalchemy import func

program_reviews_bp = Blueprint('program_reviews', __name__)

# List of all US radiology residency programs (ACGME-accredited, based on FREIDA data)
RADIOLOGY_PROGRAMS = [
    "Alabama - University of Alabama Medical Center",
    "Alabama - University of South Alabama",
    "Alaska - Alaska Native Medical Center",
    "Arizona - Banner-University Medical Center Phoenix",
    "Arizona - Mayo Clinic College of Medicine and Science (Phoenix)",
    "Arizona - University of Arizona College of Medicine - Tucson",
    "Arizona - University of Arizona College of Medicine - Phoenix",
    "Arkansas - University of Arkansas for Medical Sciences",
    "California - Cedars-Sinai Medical Center",
    "California - Kaiser Permanente Northern California (Oakland)",
    "California - Loma Linda University Health Education Consortium",
    "California - Naval Medical Center San Diego",
    "California - Stanford Health Care-Sponsored Stanford University",
    "California - University of California (Davis) Medical Center",
    "California - University of California (Irvine)",
    "California - University of California (Los Angeles) Medical Center",
    "California - University of California (San Diego) Medical Center",
    "California - University of California (San Francisco)",
    "California - University of Southern California/LAC+USC Medical Center",
    "Colorado - University of Colorado",
    "Connecticut - Bridgeport Hospital/Yale New Haven Health",
    "Connecticut - Yale-New Haven Medical Center",
    "Delaware - Christiana Care Health Services",
    "District of Columbia - George Washington University",
    "District of Columbia - Georgetown University Hospital",
    "District of Columbia - Howard University",
    "District of Columbia - MedStar Georgetown University Hospital",
    "Florida - AdventHealth Orlando",
    "Florida - Jackson Memorial Hospital/Jackson Health System",
    "Florida - Mayo Clinic College of Medicine and Science (Jacksonville)",
    "Florida - Naval Hospital Jacksonville",
    "Florida - University of Florida",
    "Florida - University of Miami/Jackson Memorial Medical Center",
    "Florida - University of South Florida Morsani",
    "Georgia - Emory University School of Medicine",
    "Georgia - Medical College of Georgia at Augusta University",
    "Georgia - Morehouse School of Medicine",
    "Hawaii - University of Hawaii",
    "Idaho - University of Washington (Boise)",
    "Illinois - Advocate Health Care",
    "Illinois - McGaw Medical Center of Northwestern University",
    "Illinois - Rush University Medical Center",
    "Illinois - Southern Illinois University",
    "Illinois - University of Chicago Medical Center",
    "Illinois - University of Illinois College of Medicine at Chicago",
    "Indiana - Indiana University School of Medicine",
    "Iowa - University of Iowa Hospitals and Clinics",
    "Kansas - University of Kansas School of Medicine",
    "Kentucky - University of Kentucky College of Medicine",
    "Kentucky - University of Louisville School of Medicine",
    "Louisiana - Louisiana State University",
    "Louisiana - Ochsner Clinic Foundation",
    "Louisiana - Tulane University",
    "Maine - Maine Medical Center",
    "Maryland - Johns Hopkins University",
    "Maryland - University of Maryland",
    "Maryland - Walter Reed National Military Medical Center",
    "Massachusetts - Beth Israel Deaconess Medical Center",
    "Massachusetts - Boston University Medical Center",
    "Massachusetts - Brigham and Women's Hospital",
    "Massachusetts - Massachusetts General Hospital",
    "Massachusetts - Tufts Medical Center",
    "Massachusetts - University of Massachusetts",
    "Michigan - Beaumont Health (Royal Oak)",
    "Michigan - Henry Ford Hospital",
    "Michigan - Michigan State University",
    "Michigan - University of Michigan",
    "Michigan - Wayne State University School of Medicine",
    "Minnesota - Mayo Clinic College of Medicine and Science (Rochester)",
    "Minnesota - University of Minnesota",
    "Mississippi - University of Mississippi Medical Center",
    "Missouri - Mallinckrodt Institute of Radiology at Washington University",
    "Missouri - Saint Louis University",
    "Missouri - University of Missouri-Columbia",
    "Montana - University of Washington (Missoula)",
    "Nebraska - Creighton University",
    "Nebraska - University of Nebraska Medical Center",
    "Nevada - University of Nevada Las Vegas School of Medicine",
    "New Hampshire - Dartmouth-Hitchcock Medical Center",
    "New Jersey - Atlantic Health System",
    "New Jersey - Rutgers New Jersey Medical School",
    "New Jersey - Rutgers Robert Wood Johnson Medical School",
    "New Mexico - University of New Mexico",
    "New York - Albert Einstein College of Medicine",
    "New York - Albany Medical Center",
    "New York - Icahn School of Medicine at Mount Sinai",
    "New York - New York Presbyterian Hospital (Columbia Campus)",
    "New York - New York Presbyterian Hospital (Cornell Campus)",
    "New York - New York University Grossman School of Medicine",
    "New York - State University of New York at Buffalo",
    "New York - State University of New York Downstate Medical Center",
    "New York - State University of New York Upstate Medical University",
    "New York - University of Rochester",
    "North Carolina - Atrium Health Carolinas Medical Center",
    "North Carolina - Duke University Hospital",
    "North Carolina - East Carolina University",
    "North Carolina - University of North Carolina Hospitals",
    "North Carolina - Wake Forest University School of Medicine",
    "North Dakota - University of North Dakota",
    "Ohio - Case Western Reserve University/University Hospitals Cleveland Medical Center",
    "Ohio - Cleveland Clinic Foundation",
    "Ohio - Ohio State University Hospital",
    "Ohio - University of Cincinnati Medical Center",
    "Ohio - University of Toledo",
    "Oklahoma - University of Oklahoma Health Sciences Center",
    "Oregon - Oregon Health & Science University",
    "Pennsylvania - Allegheny Health Network",
    "Pennsylvania - Drexel University College of Medicine",
    "Pennsylvania - Penn State Milton S Hershey Medical Center",
    "Pennsylvania - Temple University Hospital",
    "Pennsylvania - Thomas Jefferson University",
    "Pennsylvania - University of Pennsylvania",
    "Pennsylvania - University of Pittsburgh Medical Center",
    "Rhode Island - Brown University",
    "South Carolina - Medical University of South Carolina",
    "South Carolina - Prisma Health-Upstate",
    "South Dakota - University of South Dakota",
    "Tennessee - University of Tennessee",
    "Tennessee - Vanderbilt University Medical Center",
    "Texas - Baylor College of Medicine",
    "Texas - Brooke Army Medical Center",
    "Texas - Texas A&M College of Medicine",
    "Texas - Texas Tech University Health Sciences Center",
    "Texas - University of Texas at Austin Dell Medical School",
    "Texas - University of Texas Health Science Center at Houston",
    "Texas - University of Texas Health Science Center at San Antonio",
    "Texas - University of Texas Medical Branch",
    "Texas - University of Texas Southwestern Medical School",
    "Utah - University of Utah",
    "Vermont - University of Vermont Medical Center",
    "Virginia - Eastern Virginia Medical School",
    "Virginia - University of Virginia",
    "Virginia - Virginia Commonwealth University Health System",
    "Washington - Madigan Army Medical Center",
    "Washington - University of Washington",
    "West Virginia - West Virginia University",
    "Wisconsin - Medical College of Wisconsin Affiliated Hospitals",
    "Wisconsin - University of Wisconsin Hospitals and Clinics",
    "Wyoming - University of Washington (Casper)"
]

@program_reviews_bp.route('/program-reviews')
def index():
    """Display program reviews dashboard"""
    if not current_user.is_authenticated:
        return render_template("auth/login_required.html")
        
    program_name = request.args.get('program', '')
    
    if program_name:
        # Get reviews for specific program
        reviews = ProgramReview.query.filter_by(program_name=program_name).order_by(ProgramReview.created_at.desc()).all()
        
        # Calculate average ratings
        avg_ratings = db.session.query(
            func.avg(ProgramReview.educational_quality).label('avg_educational'),
            func.avg(ProgramReview.work_life_balance).label('avg_work_life'),
            func.avg(ProgramReview.attending_quality).label('avg_attending'),
            func.avg(ProgramReview.facilities_quality).label('avg_facilities'),
            func.avg(ProgramReview.research_opportunities).label('avg_research'),
            func.avg(ProgramReview.culture).label('avg_culture'),
            func.count(ProgramReview.id).label('total_reviews')
        ).filter_by(program_name=program_name).first()
        
        return render_template('program_reviews/program.html',
                             program_name=program_name,
                             reviews=reviews,
                             avg_ratings=avg_ratings)
    else:
        # Get all programs with review counts and average ratings
        programs_data = []
        for program in RADIOLOGY_PROGRAMS:
            stats = db.session.query(
                func.count(ProgramReview.id).label('review_count'),
                func.avg(ProgramReview.educational_quality).label('avg_educational'),
                func.avg(ProgramReview.work_life_balance).label('avg_work_life'),
                func.avg(ProgramReview.attending_quality).label('avg_attending'),
                func.avg(ProgramReview.facilities_quality).label('avg_facilities'),
                func.avg(ProgramReview.research_opportunities).label('avg_research'),
                func.avg(ProgramReview.culture).label('avg_culture')
            ).filter_by(program_name=program).first()
            
            if stats.review_count > 0:
                programs_data.append({
                    'name': program,
                    'review_count': stats.review_count,
                    'avg_educational': round(stats.avg_educational, 1) if stats.avg_educational else 0,
                    'avg_work_life': round(stats.avg_work_life, 1) if stats.avg_work_life else 0,
                    'avg_attending': round(stats.avg_attending, 1) if stats.avg_attending else 0,
                    'avg_facilities': round(stats.avg_facilities, 1) if stats.avg_facilities else 0,
                    'avg_research': round(stats.avg_research, 1) if stats.avg_research else 0,
                    'avg_culture': round(stats.avg_culture, 1) if stats.avg_culture else 0,
                    'overall_avg': round((stats.avg_educational + stats.avg_work_life + stats.avg_attending + 
                                        stats.avg_facilities + stats.avg_research + stats.avg_culture) / 6, 1) if all([stats.avg_educational, stats.avg_work_life, stats.avg_attending, stats.avg_facilities, stats.avg_research, stats.avg_culture]) else 0
                })
        
        # Sort by overall average rating
        programs_data.sort(key=lambda x: x['overall_avg'], reverse=True)
        
        return render_template('program_reviews/index.html',
                             programs=programs_data,
                             all_programs=RADIOLOGY_PROGRAMS)

@program_reviews_bp.route('/program-reviews/new', methods=['GET', 'POST'])
@login_required
def new_review():
    """Create a new program review"""
    if request.method == 'POST':
        program_name = request.form.get('program_name')
        educational_quality = int(request.form.get('educational_quality'))
        work_life_balance = int(request.form.get('work_life_balance'))
        attending_quality = int(request.form.get('attending_quality'))
        facilities_quality = int(request.form.get('facilities_quality'))
        research_opportunities = int(request.form.get('research_opportunities'))
        culture = int(request.form.get('culture'))
        comments = request.form.get('comments')
        
        # Validate ratings
        if not all(1 <= rating <= 5 for rating in [educational_quality, work_life_balance, attending_quality, 
                                                   facilities_quality, research_opportunities, culture]):
            flash('All ratings must be between 1 and 5', 'error')
            return redirect(request.url)
        
        # Create review
        review = ProgramReview(
            program_name=program_name,
            user_id=current_user.id,
            educational_quality=educational_quality,
            work_life_balance=work_life_balance,
            attending_quality=attending_quality,
            facilities_quality=facilities_quality,
            research_opportunities=research_opportunities,
            culture=culture,
            comments=comments
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('program_reviews.index', program=program_name))
    
    return render_template('program_reviews/new.html', programs=RADIOLOGY_PROGRAMS)
