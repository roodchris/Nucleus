from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import and_
from .models import db, Opportunity, OpportunityType, UserRole, CalendarSlot, User, Application, ApplicationStatus, TrainingLevel
from .forms import OpportunityForm, FilterForm
from datetime import date, datetime, timedelta
import math
from pyzipcode import ZipCodeDatabase

opp_bp = Blueprint("opportunities", __name__)


def calculate_distance_between_zip_codes(zip1, zip2):
    """
    Calculate distance between two zip codes using comprehensive US zip code database.
    This works for ANY US zip code, not just pre-mapped ones.
    """
    try:
        # Initialize zip code database
        zcdb = ZipCodeDatabase()
        
        # Get coordinates for both zip codes
        result1 = zcdb.get(zip1)
        result2 = zcdb.get(zip2)
        
        if result1 and result2:
            # Calculate distance using Haversine formula
            lat1, lon1 = math.radians(result1.latitude), math.radians(result1.longitude)
            lat2, lon2 = math.radians(result2.latitude), math.radians(result2.longitude)
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth's radius in miles
            R = 3959
            
            return R * c
        else:
            # If zip code lookup fails, return a large distance
            return 9999
            
    except Exception as e:
        # If any error occurs, return large distance
        print(f"Error calculating distance between {zip1} and {zip2}: {e}")
        return 9999


@opp_bp.route("/")
def home():
    return render_template("home.html")


@opp_bp.route("/healthz")
def healthz():
    return "ok", 200


@opp_bp.route("/opportunities")
def list_opportunities():
    if not current_user.is_authenticated:
        return render_template("auth/login_required.html")
        
    form = FilterForm(request.args)
    query = Opportunity.query.filter_by(is_active=True)

    if form.opportunity_type.data:
        try:
            query = query.filter(Opportunity.opportunity_type == OpportunityType(form.opportunity_type.data))
        except Exception:
            pass
    # Store zip code and radius for later distance filtering
    search_zip = None
    radius_miles = None
    if form.zip_code.data and form.radius_miles.data:
        search_zip = form.zip_code.data
        radius_miles = form.radius_miles.data
    elif form.zip_code.data:
        query = query.filter(Opportunity.zip_code.ilike(f"%{form.zip_code.data}%"))
    
    if form.pgy_year.data and form.pgy_year.data != "":
        training_level = form.pgy_year.data
        # Convert string to TrainingLevel enum for comparison
        try:
            user_level = TrainingLevel(training_level)
            # Use the is_training_level_eligible method for proper comparison
            opportunities = query.all()
            filtered_opportunities = [opp for opp in opportunities if opp.is_training_level_eligible(user_level)]
            opportunities = filtered_opportunities
        except ValueError:
            # Invalid training level, return empty results
            opportunities = []
    if form.pay_min.data is not None:
        query = query.filter(Opportunity.pay_per_hour >= float(form.pay_min.data))
    if form.shift_min.data is not None:
        query = query.filter(Opportunity.shift_length_hours >= float(form.shift_min.data))
    if form.shift_max.data is not None:
        query = query.filter(Opportunity.shift_length_hours <= float(form.shift_max.data))
    if form.hpw_min.data is not None:
        query = query.filter(Opportunity.hours_per_week >= float(form.hpw_min.data))
    if form.hpw_max.data is not None:
        query = query.filter(Opportunity.hours_per_week <= float(form.hpw_max.data))

    opportunities = query.order_by(Opportunity.created_at.desc()).all()
    
    # Apply distance filtering if zip code and radius are specified
    if search_zip and radius_miles:
        filtered_opportunities = []
        for opp in opportunities:
            distance = calculate_distance_between_zip_codes(search_zip, opp.zip_code)
            if distance <= radius_miles:
                # Add distance information to the opportunity object for display
                opp.distance = round(distance, 1)
                filtered_opportunities.append(opp)
        opportunities = filtered_opportunities
    
    return render_template("opportunities/list.html", form=form, opportunities=opportunities, OpportunityType=OpportunityType)


@opp_bp.route("/opportunities/new", methods=["GET", "POST"])
@login_required
def create_opportunity():
    if current_user.role != UserRole.EMPLOYER:
        abort(403)
    form = OpportunityForm()
    if form.validate_on_submit():
        opp = Opportunity(
            employer_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            opportunity_type=OpportunityType(form.opportunity_type.data),
            zip_code=form.zip_code.data,
            pgy_min=TrainingLevel(form.pgy_min.data),
            pgy_max=TrainingLevel(form.pgy_max.data),
            pay_per_hour=float(form.pay_per_hour.data),
            shift_length_hours=float(form.shift_length_hours.data),
            hours_per_week=float(form.hours_per_week.data),
        )
        db.session.add(opp)
        db.session.commit()
        
        # Handle calendar slots from the form
        slot_count = 0
        while True:
            date_key = f"slot_date_{slot_count}"
            start_key = f"slot_start_{slot_count}"
            end_key = f"slot_end_{slot_count}"
            
            if date_key not in request.form or not request.form[date_key]:
                break
                
            try:
                slot_date = datetime.strptime(request.form[date_key], "%Y-%m-%d").date()
                start_time = datetime.strptime(request.form[start_key], "%H:%M").time()
                end_time = datetime.strptime(request.form[end_key], "%H:%M").time()
                
                # Validate time range
                if start_time >= end_time:
                    flash(f"Time slot {slot_count + 1}: End time must be after start time.", "error")
                else:
                    slot = CalendarSlot(
                        opportunity_id=opp.id,
                        date=slot_date,
                        start_time=start_time,
                        end_time=end_time
                    )
                    db.session.add(slot)
                    
            except ValueError:
                flash(f"Time slot {slot_count + 1}: Invalid date or time format.", "error")
            
            slot_count += 1
        
        if slot_count > 0:
            db.session.commit()
            flash(f"Opportunity posted successfully with {slot_count} time slot(s).", "success")
        else:
            flash("Opportunity posted successfully. You can add time slots later from the calendar view.", "success")
            
        return redirect(url_for("opportunities.list_opportunities"))
    
    # Pass today's date for the date input min attribute
    from datetime import date
    return render_template("opportunities/create.html", form=form, today=date.today())


@opp_bp.route("/opportunities/<int:opportunity_id>")
def show_opportunity(opportunity_id: int):
    from .models import Opportunity
    opp = Opportunity.query.get_or_404(opportunity_id)
    return render_template("opportunities/detail.html", opp=opp)


@opp_bp.route("/opportunities/<int:opportunity_id>/calendar")
def opportunity_calendar(opportunity_id: int):
    opp = Opportunity.query.get_or_404(opportunity_id)
    
    # Get month parameter for navigation
    month_param = request.args.get("month")
    if month_param:
        try:
            start_date = datetime.strptime(month_param, "%Y-%m").date()
        except ValueError:
            start_date = date.today()
    else:
        start_date = date.today()
    
    # Get calendar slots for the month
    end_date = (start_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    calendar_slots = CalendarSlot.query.filter(
        CalendarSlot.opportunity_id == opportunity_id,
        CalendarSlot.date >= start_date.replace(day=1),
        CalendarSlot.date <= end_date,
        CalendarSlot.is_available == True
    ).order_by(CalendarSlot.date, CalendarSlot.start_time).all()
    
    return render_template("opportunities/calendar.html", opp=opp, calendar_slots=calendar_slots, today=start_date, timedelta=timedelta)


@opp_bp.route("/opportunities/<int:opportunity_id>/calendar/add", methods=["POST"])
@login_required
def add_calendar_slot(opportunity_id: int):
    opp = Opportunity.query.get_or_404(opportunity_id)
    
    # Only employers can add calendar slots to their own opportunities
    if current_user.role != UserRole.EMPLOYER or current_user.id != opp.employer_id:
        abort(403)
    
    # Debug: Print all form data
    print(f"DEBUG: Form data received: {dict(request.form)}")
    
    # Get form data
    date_str = request.form.get("date")
    start_time_str = request.form.get("start_time")
    end_time_str = request.form.get("end_time")
    
    print(f"DEBUG: Parsed values - Date: {date_str}, Start: {start_time_str}, End: {end_time_str}")
    
    # Check if all required fields are present
    if not date_str or not start_time_str or not end_time_str:
        flash(f"All fields (date, start time, end time) are required. Received: date='{date_str}', start_time='{start_time_str}', end_time='{end_time_str}'", "error")
        return redirect(url_for("opportunities.opportunity_calendar", opportunity_id=opportunity_id))
    
    try:
        slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
        
        print(f"DEBUG: Parsed successfully - Date: {slot_date}, Start: {start_time}, End: {end_time}")
        
        # Validate time range
        if start_time >= end_time:
            flash("End time must be after start time.", "error")
            return redirect(url_for("opportunities.opportunity_calendar", opportunity_id=opportunity_id))
        
        # Check for overlapping slots
        existing_slot = CalendarSlot.query.filter(
            CalendarSlot.opportunity_id == opportunity_id,
            CalendarSlot.date == slot_date,
            CalendarSlot.is_available == True,
            db.or_(
                db.and_(CalendarSlot.start_time < end_time, CalendarSlot.end_time > start_time)
            )
        ).first()
        
        if existing_slot:
            flash("Calendar slot overlaps with existing availability.", "error")
            return redirect(url_for("opportunities.opportunity_calendar", opportunity_id=opportunity_id))
        
        slot = CalendarSlot(
            opportunity_id=opportunity_id,
            date=slot_date,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(slot)
        db.session.commit()
        flash("Calendar slot added successfully.", "success")
        
    except ValueError as e:
        flash(f"Invalid date or time format: {date_str}, {start_time_str}, {end_time_str}. Error: {str(e)}. Please check your input.", "error")
    
    return redirect(url_for("opportunities.opportunity_calendar", opportunity_id=opportunity_id))


@opp_bp.route("/calendar")
def global_calendar():
    """Show all available opportunities across all employers on a calendar view"""
    if not current_user.is_authenticated:
        return render_template("auth/login_required.html")
        
    # Get month parameter for navigation
    month_param = request.args.get("month")
    if month_param:
        try:
            start_date = datetime.strptime(month_param, "%Y-%m").date()
        except ValueError:
            start_date = date.today()
    else:
        start_date = date.today()
    
    # Get calendar slots for the month
    end_date = (start_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    calendar_slots = db.session.query(CalendarSlot, Opportunity, User).join(
        Opportunity, CalendarSlot.opportunity_id == Opportunity.id
    ).join(
        User, Opportunity.employer_id == User.id
    ).filter(
        CalendarSlot.date >= start_date.replace(day=1),
        CalendarSlot.date <= end_date,
        CalendarSlot.is_available == True,
        Opportunity.is_active == True
    ).order_by(CalendarSlot.date, CalendarSlot.start_time).all()
    
    return render_template("opportunities/global_calendar.html", calendar_slots=calendar_slots, start_date=start_date, timedelta=timedelta)


# Resident Profile Routes
@opp_bp.route("/profile", methods=["GET", "POST"])
@login_required
def resident_profile():
    if current_user.role != UserRole.RESIDENT:
        # Redirect employers to their profile page instead of showing 403
        return redirect(url_for("opportunities.employer_profile"))
    
    from .models import ResidentProfile
    
    profile = ResidentProfile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == "POST":
        if not profile:
            profile = ResidentProfile(user_id=current_user.id)
            db.session.add(profile)
        
        profile.medical_school = request.form.get("medical_school", "").strip()
        profile.residency_program = request.form.get("residency_program", "").strip()
        training_year_str = request.form.get("training_year")
        if training_year_str:
            try:
                profile.training_year = TrainingLevel(training_year_str)
            except ValueError:
                profile.training_year = None
        else:
            profile.training_year = None
        profile.bio = request.form.get("bio", "").strip()
        
        # Handle photo upload
        if "photo" in request.files:
            photo = request.files["photo"]
            if photo and photo.filename:
                import os
                import uuid
                from werkzeug.utils import secure_filename
                
                # Generate unique filename
                file_ext = os.path.splitext(photo.filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                
                # Save file to uploads directory
                uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                file_path = os.path.join(uploads_dir, unique_filename)
                photo.save(file_path)
                
                # Store unique filename in database
                profile.photo_filename = unique_filename
        
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("opportunities.resident_profile"))
    
    return render_template("opportunities/resident_profile.html", profile=profile)


@opp_bp.route("/profile/<int:user_id>")
def view_resident_profile(user_id):
    from .models import ResidentProfile, User
    
    user = User.query.get_or_404(user_id)
    if user.role != UserRole.RESIDENT:
        abort(404)
    
    profile = ResidentProfile.query.filter_by(user_id=user_id).first()
    return render_template("opportunities/view_resident_profile.html", user=user, profile=profile)


# Employer Profile Routes
@opp_bp.route("/employer/profile", methods=["GET", "POST"])
@login_required
def employer_profile():
    if current_user.role != UserRole.EMPLOYER:
        # Redirect residents to their profile page instead of showing 403
        return redirect(url_for("opportunities.resident_profile"))
    
    from .models import EmployerProfile
    
    profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == "POST":
        if not profile:
            profile = EmployerProfile(user_id=current_user.id)
            db.session.add(profile)
        
        profile.practice_setting = request.form.get("practice_setting", "").strip()
        profile.modalities = request.form.get("modalities", "").strip()
        profile.location = request.form.get("location", "").strip()
        profile.practice_description = request.form.get("practice_description", "").strip()
        
        db.session.commit()
        flash("Practice profile updated successfully!", "success")
        return redirect(url_for("opportunities.employer_profile"))
    
    return render_template("opportunities/employer_profile.html", profile=profile)


# Job Listing Status Routes
@opp_bp.route("/employer/listings")
@login_required
def employer_listings():
    if current_user.role != UserRole.EMPLOYER:
        # Redirect residents to opportunities page instead of showing 403
        return redirect(url_for("opportunities.list_opportunities"))
    
    from .models import Opportunity, Conversation, User, ResidentProfile
    
    # Get all opportunities posted by this employer
    opportunities = Opportunity.query.filter_by(employer_id=current_user.id, is_active=True).all()
    
    # Get conversations for each opportunity to see who's interested
    listings_data = []
    for opp in opportunities:
        conversations = Conversation.query.filter_by(opportunity_id=opp.id).all()
        
        # Get resident information for each conversation
        residents = []
        for conv in conversations:
            if conv.resident_id:
                resident_user = User.query.get(conv.resident_id)
                resident_profile = ResidentProfile.query.filter_by(user_id=conv.resident_id).first()
                residents.append({
                    'user': resident_user,
                    'profile': resident_profile,
                    'conversation_id': conv.id,
                    'last_message': conv.messages[-1] if conv.messages else None
                })
        
        listings_data.append({
            'opportunity': opp,
            'residents': residents
        })
    
    return render_template("opportunities/employer_listings.html", listings_data=listings_data)


# Application Tracking Routes
@opp_bp.route("/applications")
@login_required
def resident_applications():
    """Resident view of their applications"""
    if current_user.role != UserRole.RESIDENT:
        # Redirect employers to their applications page instead of showing 403
        return redirect(url_for("opportunities.employer_applications"))
    
    from .models import Application, Opportunity, User
    
    # Get all applications for this resident
    applications = db.session.query(Application, Opportunity, User).join(
        Opportunity, Application.opportunity_id == Opportunity.id
    ).join(
        User, Opportunity.employer_id == User.id
    ).filter(
        Application.resident_id == current_user.id
    ).order_by(Application.applied_at.desc()).all()
    
    return render_template("opportunities/resident_applications.html", applications=applications)


@opp_bp.route("/employer/applications")
@login_required
def employer_applications():
    """Employer view of all applications for their opportunities"""
    if current_user.role != UserRole.EMPLOYER:
        # Redirect residents to their applications page instead of showing 403
        return redirect(url_for("opportunities.resident_applications"))
    
    from .models import Application, Opportunity, User, ResidentProfile
    
    # Get all applications for opportunities posted by this employer
    applications = db.session.query(Application, Opportunity, User, ResidentProfile).join(
        Opportunity, Application.opportunity_id == Opportunity.id
    ).join(
        User, Application.resident_id == User.id
    ).outerjoin(
        ResidentProfile, User.id == ResidentProfile.user_id
    ).filter(
        Opportunity.employer_id == current_user.id
    ).order_by(Application.applied_at.desc()).all()
    
    return render_template("opportunities/employer_applications.html", applications=applications)


@opp_bp.route("/employer/applications/<int:application_id>/decision", methods=["POST"])
@login_required
def update_application_decision(application_id):
    """Update application status (accept/reject)"""
    if current_user.role != UserRole.EMPLOYER:
        abort(403)
    
    from .models import Application, Opportunity
    
    application = Application.query.get_or_404(application_id)
    opportunity = Opportunity.query.get_or_404(application.opportunity_id)
    
    # Check if this employer owns the opportunity
    if opportunity.employer_id != current_user.id:
        abort(403)
    
    status = request.form.get("status")
    notes = request.form.get("notes", "").strip()
    
    if status not in ["accepted", "rejected"]:
        flash("Invalid status", "error")
        return redirect(url_for("opportunities.employer_applications"))
    
    # Update application status
    application.status = ApplicationStatus(status)
    application.decision_at = datetime.utcnow()
    application.decision_notes = notes
    
    # If accepted, mark opportunity as filled
    if status == "accepted":
        opportunity.is_filled = True
        
        # Reject all other pending applications for this opportunity
        other_applications = Application.query.filter(
            Application.opportunity_id == opportunity.id,
            Application.id != application.id,
            Application.status == ApplicationStatus.PENDING
        ).all()
        
        for app in other_applications:
            app.status = ApplicationStatus.REJECTED
            app.decision_at = datetime.utcnow()
            app.decision_notes = "Position filled by another applicant"
    
    db.session.commit()
    
    status_text = "accepted" if status == "accepted" else "rejected"
    flash(f"Application {status_text} successfully", "success")
    return redirect(url_for("opportunities.employer_applications"))


@opp_bp.route("/opportunities/<int:opportunity_id>/delete", methods=["POST"])
@login_required
def delete_opportunity(opportunity_id):
    """Delete an opportunity (employer only)"""
    if current_user.role != UserRole.EMPLOYER:
        abort(403)
    
    from .models import Opportunity
    
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    
    # Check if this employer owns the opportunity
    if opportunity.employer_id != current_user.id:
        abort(403)
    
    # Soft delete by marking as inactive
    opportunity.is_active = False
    db.session.commit()
    
    flash("Opportunity deleted successfully", "success")
    return redirect(url_for("opportunities.employer_listings"))


@opp_bp.route("/opportunities/<int:opportunity_id>/apply", methods=["POST"])
@login_required
def apply_to_opportunity(opportunity_id):
    """Apply to an opportunity (resident only)"""
    if current_user.role != UserRole.RESIDENT:
        abort(403)
    
    from .models import Opportunity, Application, Conversation
    
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    
    # Check if opportunity is still active and not filled
    if not opportunity.is_active or opportunity.is_filled:
        flash("This opportunity is no longer available", "error")
        return redirect(url_for("opportunities.show_opportunity", opportunity_id=opportunity_id))
    
    # Check if already applied
    existing_application = Application.query.filter_by(
        opportunity_id=opportunity_id,
        resident_id=current_user.id
    ).first()
    
    if existing_application:
        flash("You have already applied to this opportunity", "error")
        return redirect(url_for("opportunities.show_opportunity", opportunity_id=opportunity_id))
    
    # Create application
    application = Application(
        opportunity_id=opportunity_id,
        resident_id=current_user.id,
        status=ApplicationStatus.PENDING
    )
    db.session.add(application)
    
    # Create conversation for messaging
    conversation = Conversation(
        opportunity_id=opportunity_id,
        employer_id=opportunity.employer_id,
        resident_id=current_user.id
    )
    db.session.add(conversation)
    
    db.session.commit()
    
    flash("Application submitted successfully! You can now message the employer.", "success")
    return redirect(url_for("opportunities.show_opportunity", opportunity_id=opportunity_id))
