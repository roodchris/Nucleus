from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, text
from sqlalchemy.exc import ProgrammingError
from .models import db, ResidencySwap, ResidencyOpening, User, Conversation
from datetime import datetime

residency_swaps_bp = Blueprint("residency_swaps", __name__)


@residency_swaps_bp.route("/residency-swaps")
def index():
    """Main page showing all residency swaps and openings"""
    if not current_user.is_authenticated:
        return render_template("auth/login_required.html")
    
    # Get all active swaps and openings
    # Handle case where additional_info column doesn't exist yet
    try:
        swaps = ResidencySwap.query.filter_by(is_active=True).order_by(ResidencySwap.created_at.desc()).all()
        openings = ResidencyOpening.query.filter_by(is_active=True).order_by(ResidencyOpening.created_at.desc()).all()
    except ProgrammingError as e:
        # If additional_info column doesn't exist, query without it and set it to None
        if "additional_info" in str(e):
            current_app.logger.warning("additional_info column doesn't exist yet, querying without it")
            # Query swaps using raw SQL without additional_info
            swap_results = db.session.execute(text("""
                SELECT id, user_id, current_specialty, current_state, current_city,
                       desired_specialty, desired_state, desired_city, created_at, is_active
                FROM residency_swap
                WHERE is_active = true
                ORDER BY created_at DESC
            """))
            swaps = []
            for row in swap_results:
                swap = ResidencySwap(
                    id=row.id,
                    user_id=row.user_id,
                    current_specialty=row.current_specialty,
                    current_state=row.current_state,
                    current_city=row.current_city,
                    desired_specialty=row.desired_specialty,
                    desired_state=row.desired_state,
                    desired_city=row.desired_city,
                    created_at=row.created_at,
                    is_active=row.is_active
                )
                swap.additional_info = None  # Set to None since column doesn't exist
                swaps.append(swap)
            
            # Query openings using raw SQL without additional_info
            opening_results = db.session.execute(text("""
                SELECT id, user_id, specialty, state, city, institution, contact_email, created_at, is_active
                FROM residency_opening
                WHERE is_active = true
                ORDER BY created_at DESC
            """))
            openings = []
            for row in opening_results:
                opening = ResidencyOpening(
                    id=row.id,
                    user_id=row.user_id,
                    specialty=row.specialty,
                    state=row.state,
                    city=row.city,
                    institution=row.institution,
                    contact_email=row.contact_email,
                    created_at=row.created_at,
                    is_active=row.is_active
                )
                opening.additional_info = None  # Set to None since column doesn't exist
                openings.append(opening)
        else:
            # Re-raise if it's a different error
            raise
    
    return render_template("residency_swaps/index.html", swaps=swaps, openings=openings)


@residency_swaps_bp.route("/residency-swaps/new", methods=["GET", "POST"])
@login_required
def new_post():
    """Page to select between swap or opening"""
    if request.method == "POST":
        post_type = request.form.get("post_type")
        if post_type == "swap":
            return redirect(url_for("residency_swaps.new_swap"))
        elif post_type == "opening":
            return redirect(url_for("residency_swaps.new_opening"))
        else:
            flash("Please select a post type", "error")
    
    return render_template("residency_swaps/new_post.html")


@residency_swaps_bp.route("/residency-swaps/new/swap", methods=["GET", "POST"])
@login_required
def new_swap():
    """Create a new residency/fellowship swap request"""
    if request.method == "POST":
        current_specialty = request.form.get("current_specialty", "").strip()
        desired_specialty = request.form.get("desired_specialty", "").strip()
        current_state = request.form.get("current_state", "").strip() or None
        current_city = request.form.get("current_city", "").strip() or None
        desired_state = request.form.get("desired_state", "").strip() or None
        desired_city = request.form.get("desired_city", "").strip() or None
        
        # Validate required fields
        if not current_specialty or not desired_specialty:
            flash("Current specialty and desired specialty are required", "error")
            return render_template("residency_swaps/new_swap.html")
        
        # Get additional info
        additional_info = request.form.get("additional_info", "").strip() or None
        
        # Check if additional_info column exists
        try:
            db.session.execute(text("SELECT additional_info FROM residency_swap LIMIT 1"))
            column_exists = True
        except:
            column_exists = False
        
        # Create swap
        if column_exists:
            swap = ResidencySwap(
                user_id=current_user.id,
                current_specialty=current_specialty,
                desired_specialty=desired_specialty,
                current_state=current_state,
                current_city=current_city,
                desired_state=desired_state,
                desired_city=desired_city,
                additional_info=additional_info
            )
            db.session.add(swap)
            db.session.commit()
        else:
            # Use raw SQL if column doesn't exist yet
            db.session.execute(text("""
                INSERT INTO residency_swap (user_id, current_specialty, current_state, current_city,
                                           desired_specialty, desired_state, desired_city, created_at, is_active)
                VALUES (:user_id, :current_specialty, :current_state, :current_city,
                        :desired_specialty, :desired_state, :desired_city, :created_at, :is_active)
            """), {
                "user_id": current_user.id,
                "current_specialty": current_specialty,
                "current_state": current_state,
                "current_city": current_city,
                "desired_specialty": desired_specialty,
                "desired_state": desired_state,
                "desired_city": desired_city,
                "created_at": datetime.utcnow(),
                "is_active": True
            })
            db.session.commit()
        
        flash("Residency swap posted successfully!", "success")
        return redirect(url_for("residency_swaps.index"))
    
    return render_template("residency_swaps/new_swap.html")


@residency_swaps_bp.route("/residency-swaps/new/opening", methods=["GET", "POST"])
@login_required
def new_opening():
    """Create a new open residency/fellowship position"""
    if request.method == "POST":
        specialty = request.form.get("specialty", "").strip()
        state = request.form.get("state", "").strip() or None
        city = request.form.get("city", "").strip() or None
        institution = request.form.get("institution", "").strip() or None
        contact_email = request.form.get("contact_email", "").strip() or None
        
        # Validate required fields
        if not specialty:
            flash("Medical specialty is required", "error")
            return render_template("residency_swaps/new_opening.html")
        
        # Get additional info
        additional_info = request.form.get("additional_info", "").strip() or None
        
        # Check if additional_info column exists
        try:
            db.session.execute(text("SELECT additional_info FROM residency_opening LIMIT 1"))
            column_exists = True
        except:
            column_exists = False
        
        # Create opening
        if column_exists:
            opening = ResidencyOpening(
                user_id=current_user.id,
                specialty=specialty,
                state=state,
                city=city,
                institution=institution,
                contact_email=contact_email,
                additional_info=additional_info
            )
            db.session.add(opening)
            db.session.commit()
        else:
            # Use raw SQL if column doesn't exist yet
            db.session.execute(text("""
                INSERT INTO residency_opening (user_id, specialty, state, city, institution, contact_email, created_at, is_active)
                VALUES (:user_id, :specialty, :state, :city, :institution, :contact_email, :created_at, :is_active)
            """), {
                "user_id": current_user.id,
                "specialty": specialty,
                "state": state,
                "city": city,
                "institution": institution,
                "contact_email": contact_email,
                "created_at": datetime.utcnow(),
                "is_active": True
            })
            db.session.commit()
        
        flash("Open position posted successfully!", "success")
        return redirect(url_for("residency_swaps.index"))
    
    return render_template("residency_swaps/new_opening.html")


@residency_swaps_bp.route("/residency-swaps/swap/<int:swap_id>/contact", methods=["POST"])
@login_required
def contact_swap_poster(swap_id):
    """Start a conversation with the swap poster"""
    swap = ResidencySwap.query.get_or_404(swap_id)
    poster = User.query.get_or_404(swap.user_id)
    
    # Don't allow users to contact themselves
    if poster.id == current_user.id:
        flash("You cannot contact yourself", "error")
        return redirect(url_for("residency_swaps.index"))
    
    # Check if conversation already exists
    existing_convo = Conversation.query.filter(
        or_(
            (Conversation.resident_id == current_user.id) & (Conversation.employer_id == poster.id),
            (Conversation.resident_id == poster.id) & (Conversation.employer_id == current_user.id)
        ),
        Conversation.opportunity_id.is_(None)
    ).first()
    
    if existing_convo:
        return redirect(url_for("chat.thread", conversation_id=existing_convo.id))
    
    # Create new conversation
    if current_user.role.value == "resident":
        convo = Conversation(resident_id=current_user.id, employer_id=poster.id, opportunity_id=None)
    else:
        convo = Conversation(resident_id=poster.id, employer_id=current_user.id, opportunity_id=None)
    
    db.session.add(convo)
    db.session.commit()
    
    flash("Conversation started!", "success")
    return redirect(url_for("chat.thread", conversation_id=convo.id))


@residency_swaps_bp.route("/residency-swaps/opening/<int:opening_id>/contact", methods=["POST"])
@login_required
def contact_opening_poster(opening_id):
    """Start a conversation with the opening poster"""
    opening = ResidencyOpening.query.get_or_404(opening_id)
    poster = User.query.get_or_404(opening.user_id)
    
    # Don't allow users to contact themselves
    if poster.id == current_user.id:
        flash("You cannot contact yourself", "error")
        return redirect(url_for("residency_swaps.index"))
    
    # Check if conversation already exists
    existing_convo = Conversation.query.filter(
        or_(
            (Conversation.resident_id == current_user.id) & (Conversation.employer_id == poster.id),
            (Conversation.resident_id == poster.id) & (Conversation.employer_id == current_user.id)
        ),
        Conversation.opportunity_id.is_(None)
    ).first()
    
    if existing_convo:
        return redirect(url_for("chat.thread", conversation_id=existing_convo.id))
    
    # Create new conversation
    if current_user.role.value == "resident":
        convo = Conversation(resident_id=current_user.id, employer_id=poster.id, opportunity_id=None)
    else:
        convo = Conversation(resident_id=poster.id, employer_id=current_user.id, opportunity_id=None)
    
    db.session.add(convo)
    db.session.commit()
    
    flash("Conversation started!", "success")
    return redirect(url_for("chat.thread", conversation_id=convo.id))

