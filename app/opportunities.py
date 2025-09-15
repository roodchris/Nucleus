from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import and_
from .models import db, Opportunity, OpportunityType, UserRole, CalendarSlot, User, Application, ApplicationStatus, TrainingLevel, WorkDuration, PayType
from .forms import OpportunityForm, FilterForm
from datetime import date, datetime, timedelta
import math
from pyzipcode import ZipCodeDatabase

opp_bp = Blueprint("opportunities", __name__)


def get_zip_location(zip_code):
    """
    Get city and state from zip code using comprehensive US zip code database.
    Returns formatted string like "Los Angeles, CA" or None if not found.
    """
    try:
        if not zip_code:
            return None
            
        # Initialize zip code database
        zcdb = ZipCodeDatabase()
        
        # Get location info for zip code
        result = zcdb.get(zip_code)
        
        # Handle case where get() returns a list (multiple zip codes with same code)
        if isinstance(result, list):
            result = result[0] if result else None
        
        if result:
            city = result.city
            state = result.state
            return f"{city}, {state}"
        else:
            return None
    except Exception as e:
        print(f"Error getting zip location: {e}")
        return None


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
        
        # Handle case where get() returns a list (multiple zip codes with same code)
        if isinstance(result1, list):
            result1 = result1[0] if result1 else None
        if isinstance(result2, list):
            result2 = result2[0] if result2 else None
        
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
        
    form = FilterForm(data=request.args)
    
    # Clean up form data early - convert string values to proper types for numeric fields
    if form.minimum_pay.data == '':
        form.minimum_pay.data = None
    elif form.minimum_pay.data is not None:
        try:
            form.minimum_pay.data = float(form.minimum_pay.data)
        except (ValueError, TypeError):
            form.minimum_pay.data = None
    if form.radius_miles.data == '':
        form.radius_miles.data = None
    elif form.radius_miles.data is not None:
        try:
            form.radius_miles.data = int(form.radius_miles.data)
        except (ValueError, TypeError):
            form.radius_miles.data = None
    
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
    
    if form.minimum_pay.data is not None and form.minimum_pay.data != '':
        if form.pay_type.data:
            # Filter by specific pay type
            query = query.filter(Opportunity.pay_type == PayType(form.pay_type.data))
        query = query.filter(Opportunity.pay_amount >= float(form.minimum_pay.data))
    if form.work_duration.data:
        try:
            query = query.filter(Opportunity.work_duration == WorkDuration(form.work_duration.data))
        except Exception:
            pass

    opportunities = query.order_by(Opportunity.created_at.desc()).all()
    
    # Apply training level filtering after getting all opportunities
    if form.pgy_year.data and form.pgy_year.data != "":
        training_level = form.pgy_year.data
        # Convert string to TrainingLevel enum for comparison
        try:
            user_level = TrainingLevel(training_level)
            # Filter opportunities based on user's current training level
            # Show opportunities where: opportunity_min <= user_level <= opportunity_max
            # Example: If user is FELLOW, show opportunities that allow R1-R4, R1-FELLOW, R1-ATTENDING, etc.
            # But exclude opportunities that only allow R1-R4 (since FELLOW exceeds R4)
            level_order = {TrainingLevel.R1: 1, TrainingLevel.R2: 2, TrainingLevel.R3: 3, 
                          TrainingLevel.R4: 4, TrainingLevel.FELLOW: 5, TrainingLevel.ATTENDING: 6}
            user_current_level_num = level_order.get(user_level, 0)
            
            filtered_opportunities = []
            for opp in opportunities:
                opp_min_level_num = level_order.get(opp.pgy_min, 0)
                opp_max_level_num = level_order.get(opp.pgy_max, 0)
                # Show opportunity if user's level is within the opportunity's range
                if opp_min_level_num <= user_current_level_num <= opp_max_level_num:
                    filtered_opportunities.append(opp)
            
            opportunities = filtered_opportunities
        except ValueError:
            # Invalid training level, return empty results
            opportunities = []
    
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
        try:
            # Validate opportunity type before creating the opportunity
            opportunity_type_enum = None
            if form.opportunity_type.data:
                try:
                    opportunity_type_enum = OpportunityType(form.opportunity_type.data)
                except ValueError as e:
                    flash(f"Invalid opportunity type: {form.opportunity_type.data}. Please select a valid type.", "error")
                    return render_template("opportunities/create.html", form=form, today=date.today())
            
            
            opp = Opportunity(
                employer_id=current_user.id,
                title=form.title.data if form.title.data else None,
                description=form.description.data if form.description.data else None,
                opportunity_type=opportunity_type_enum,
                zip_code=form.zip_code.data if form.zip_code.data else None,
                pgy_min=TrainingLevel(form.pgy_min.data) if form.pgy_min.data else None,
                pgy_max=TrainingLevel(form.pgy_max.data) if form.pgy_max.data else None,
                pay_amount=float(form.pay_amount.data) if form.pay_amount.data else None,
                pay_type=PayType(form.pay_type.data) if form.pay_type.data else None,
                shift_length_hours=float(form.shift_length_hours.data) if form.shift_length_hours.data else None,
                hours_per_week=float(form.hours_per_week.data) if form.hours_per_week.data else None,
                timezone=form.timezone.data if form.timezone.data else None,
                work_duration=WorkDuration(form.work_duration.data) if form.work_duration.data else None,
            )
            db.session.add(opp)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create opportunity: {e}")
            flash(f"Failed to create opportunity: {str(e)}", "error")
            from datetime import date
            return render_template("opportunities/create.html", form=form, today=date.today())
        
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


@opp_bp.route("/opportunities/<int:opportunity_id>/edit", methods=["GET", "POST"])
@login_required
def edit_opportunity(opportunity_id):
    if current_user.role != UserRole.EMPLOYER:
        abort(403)
    
    # Get the opportunity and ensure it belongs to the current employer
    opportunity = Opportunity.query.filter_by(id=opportunity_id, employer_id=current_user.id).first_or_404()
    
    form = OpportunityForm()
    
    if request.method == "GET":
        # Pre-populate the form with existing data
        form.title.data = opportunity.title
        form.description.data = opportunity.description
        form.opportunity_type.data = opportunity.opportunity_type.value if opportunity.opportunity_type else ""
        form.zip_code.data = opportunity.zip_code
        form.pgy_min.data = opportunity.pgy_min.value if opportunity.pgy_min else ""
        form.pgy_max.data = opportunity.pgy_max.value if opportunity.pgy_max else ""
        form.pay_amount.data = opportunity.pay_amount
        form.pay_type.data = opportunity.pay_type.value if opportunity.pay_type else ""
        form.shift_length_hours.data = opportunity.shift_length_hours
        form.hours_per_week.data = opportunity.hours_per_week
        form.timezone.data = opportunity.timezone
        form.work_duration.data = opportunity.work_duration.value if opportunity.work_duration else ""
    
    if form.validate_on_submit():
        # Update the opportunity with new data
        opportunity.title = form.title.data if form.title.data else None
        opportunity.description = form.description.data if form.description.data else None
        opportunity.opportunity_type = OpportunityType(form.opportunity_type.data) if form.opportunity_type.data else None
        opportunity.zip_code = form.zip_code.data if form.zip_code.data else None
        opportunity.pgy_min = TrainingLevel(form.pgy_min.data) if form.pgy_min.data else None
        opportunity.pgy_max = TrainingLevel(form.pgy_max.data) if form.pgy_max.data else None
        opportunity.pay_amount = float(form.pay_amount.data) if form.pay_amount.data else None
        opportunity.pay_type = PayType(form.pay_type.data) if form.pay_type.data else None
        opportunity.shift_length_hours = float(form.shift_length_hours.data) if form.shift_length_hours.data else None
        opportunity.hours_per_week = float(form.hours_per_week.data) if form.hours_per_week.data else None
        opportunity.timezone = form.timezone.data if form.timezone.data else None
        opportunity.work_duration = WorkDuration(form.work_duration.data) if form.work_duration.data else None
        
        db.session.commit()
        flash('Opportunity updated successfully!', 'success')
        return redirect(url_for("opportunities.employer_listings"))
    
    return render_template("opportunities/edit.html", form=form, opportunity=opportunity)


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
    

    
    # Get form data
    date_str = request.form.get("date")
    start_time_str = request.form.get("start_time")
    end_time_str = request.form.get("end_time")

    
    # Check if all required fields are present
    if not date_str or not start_time_str or not end_time_str:
        flash(f"All fields (date, start time, end time) are required. Received: date='{date_str}', start_time='{start_time_str}', end_time='{end_time_str}'", "error")
        return redirect(url_for("opportunities.opportunity_calendar", opportunity_id=opportunity_id))
    
    try:
        slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()

        
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
    
    # Check if personal filter is requested
    is_personal = request.args.get('personal') == '1'
    
    if is_personal:
        # Get accepted applications for the current user
        from .models import Application, ApplicationStatus
        
        personal_slots = db.session.query(CalendarSlot, Opportunity, User).join(
            Opportunity, CalendarSlot.opportunity_id == Opportunity.id
        ).join(
            User, Opportunity.employer_id == User.id
        ).join(
            Application, Application.opportunity_id == Opportunity.id
        ).filter(
            Application.resident_id == current_user.id,
            Application.status == ApplicationStatus.ACCEPTED,
            CalendarSlot.date >= start_date.replace(day=1),
            CalendarSlot.date <= end_date
        ).order_by(CalendarSlot.date, CalendarSlot.start_time).all()
        
        calendar_slots = []
        flexible_opportunities = []
    else:
        # Get all available calendar slots
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
        
        # Get opportunities without specific calendar slots (flexible scheduling)
        all_opportunities = Opportunity.query.filter_by(is_active=True).all()
        opportunities_with_slots = db.session.query(Opportunity).join(CalendarSlot).filter(
            Opportunity.is_active == True,
            CalendarSlot.is_available == True
        ).distinct().all()
        flexible_opportunities = [opp for opp in all_opportunities if opp not in opportunities_with_slots]
        
        personal_slots = []
    
    return render_template("opportunities/global_calendar.html", 
                         calendar_slots=calendar_slots, 
                         personal_slots=personal_slots,
                         flexible_opportunities=flexible_opportunities,
                         start_date=start_date, 
                         timedelta=timedelta)


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
    
    # Send email notifications
    from .email_service import send_status_notification, send_bulk_status_notifications
    
    # Send notification to the applicant whose status changed
    send_status_notification(application.id, status)
    
    # If accepted, send notifications to all rejected applicants
    if status == "accepted" and other_applications:
        rejected_app_ids = [app.id for app in other_applications]
        send_bulk_status_notifications(rejected_app_ids, "rejected")
    
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
    
    # Send email notification to employer
    from .email_service import send_application_notification
    send_application_notification(application.id)
    
    flash("Application submitted successfully! You can now message the employer.", "success")
    return redirect(url_for("opportunities.show_opportunity", opportunity_id=opportunity_id))
