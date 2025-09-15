from datetime import datetime
from enum import Enum

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class UserRole(Enum):
    EMPLOYER = "employer"
    RESIDENT = "resident"
    ADMIN = "admin"


class OpportunityType(Enum):
    IN_PERSON_CONTRAST = "in_person_contrast"
    TELE_CONTRAST = "tele_contrast"
    DIAGNOSTIC_INTERPRETATION = "diagnostic_interpretation"
    TELE_DIAGNOSTIC_INTERPRETATION = "tele_diagnostic_interpretation"
    CONSULTING_OTHER = "consulting_other"


class ApplicationStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class TrainingLevel(Enum):
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    FELLOW = "FELLOW"
    ATTENDING = "ATTENDING"


class PayType(Enum):
    PER_HOUR = "per_hour"
    PER_RVU = "per_rvu"
    PER_YEAR = "per_year"


class WorkDuration(Enum):
    SINGLE_SHIFT = "single_shift"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    PERMANENT = "permanent"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, index=True)
    organization = db.Column(db.String(255))
    timezone = db.Column(db.String(50), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    

    opportunities = db.relationship("Opportunity", backref="employer", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def is_online(self):
        """Check if user is currently online (active within last 5 minutes)"""
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        
        # Check if user has any active sessions
        active_sessions = [session for session in self.sessions 
                          if session.last_activity and session.last_activity > cutoff_time and session.is_online]
        return len(active_sessions) > 0
    
    def get_last_activity(self):
        """Get the most recent activity time"""
        if not self.sessions:
            return None
        
        # Filter out sessions with None last_activity
        valid_sessions = [session for session in self.sessions if session.last_activity]
        if not valid_sessions:
            return None
            
        return max(session.last_activity for session in valid_sessions)


class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text)

    opportunity_type = db.Column(db.Enum(OpportunityType), nullable=True, index=True)

    zip_code = db.Column(db.String(10), nullable=True, index=True)

    pgy_min = db.Column(db.Enum(TrainingLevel), nullable=True)  # Training level min
    pgy_max = db.Column(db.Enum(TrainingLevel), nullable=True)  # Training level max

    pay_amount = db.Column(db.Float, nullable=True, index=True)
    pay_type = db.Column(db.Enum(PayType), nullable=True, index=True)
    shift_length_hours = db.Column(db.Float, nullable=True, index=True)
    hours_per_week = db.Column(db.Float, nullable=True, index=True)
    
    # Timezone for the opportunity (e.g., "America/New_York", "America/Los_Angeles")
    timezone = db.Column(db.String(50), nullable=True, index=True)
    
    # Work duration type
    work_duration = db.Column(db.Enum(WorkDuration), nullable=True, index=True)
    

    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_filled = db.Column(db.Boolean, default=False, nullable=False, index=True)  # New field
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Calendar availability
    calendar_slots = db.relationship("CalendarSlot", backref="opportunity", lazy=True, cascade="all, delete-orphan")

    def is_training_level_eligible(self, training_level: TrainingLevel) -> bool:
        # Convert enum values to numeric for comparison
        level_order = {TrainingLevel.R1: 1, TrainingLevel.R2: 2, TrainingLevel.R3: 3, 
                      TrainingLevel.R4: 4, TrainingLevel.FELLOW: 5, TrainingLevel.ATTENDING: 6}
        min_level = level_order.get(self.pgy_min, 0)
        max_level = level_order.get(self.pgy_max, 0)
        user_level = level_order.get(training_level, 0)
        return min_level <= user_level <= max_level


class CalendarSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunity.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CalendarSlot {self.date} {self.start_time}-{self.end_time}>"


class Conversation(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunity.id"), nullable=True, index=True)
	resident_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
	employer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	unread_count = db.Column(db.Integer, default=0, nullable=False)  # Track unread messages

	resident = db.relationship("User", foreign_keys=[resident_id])
	employer = db.relationship("User", foreign_keys=[employer_id])
	opportunity = db.relationship("Opportunity", foreign_keys=[opportunity_id])


class Message(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"), nullable=False, index=True)
	sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
	body = db.Column(db.Text, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
	is_read = db.Column(db.Boolean, default=False, nullable=False)  # Track if message is read

	conversation = db.relationship("Conversation", backref=db.backref("messages", lazy=True, order_by="Message.created_at"))
	sender = db.relationship("User")


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunity.id"), nullable=False, index=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    status = db.Column(db.Enum(ApplicationStatus), default=ApplicationStatus.PENDING, nullable=False, index=True)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    decision_at = db.Column(db.DateTime, nullable=True)
    decision_notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    opportunity = db.relationship("Opportunity", backref="applications")
    resident = db.relationship("User", backref="applications")
    
    def __repr__(self):
        return f"<Application {self.resident_id} -> {self.opportunity_id} ({self.status.value})>"


class ResidentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True, index=True)
    medical_school = db.Column(db.String(200), nullable=True)
    residency_program = db.Column(db.String(200), nullable=True)
    training_year = db.Column(db.Enum(TrainingLevel), nullable=True)  # Training level
    bio = db.Column(db.Text, nullable=True)
    photo_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = db.relationship("User", backref="resident_profile", uselist=False)


class EmployerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True, index=True)
    practice_setting = db.Column(db.String(200), nullable=True)  # e.g., "Academic Medical Center", "Private Practice"
    modalities = db.Column(db.Text, nullable=True)  # e.g., "CT, MRI, X-ray, Ultrasound"
    location = db.Column(db.String(500), nullable=True)  # Detailed location information
    practice_description = db.Column(db.Text, nullable=True)  # General description of the practice
    photo_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = db.relationship("User", backref="employer_profile", uselist=False)


class ForumCategory(Enum):
    JOB_ADVICE = "job_advice"
    RESIDENCY_ADVICE = "residency_advice"
    SALARY = "salary"
    STUDYING = "studying"
    FELLOWSHIP = "fellowship"
    GENERAL = "general"
    OTHER = "other"


class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(ForumCategory), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    photos = db.Column(db.Text, nullable=True)  # JSON string of photo filenames
    
    # Relationships
    author = db.relationship("User", backref="forum_posts")
    comments = db.relationship("ForumComment", backref="post", lazy=True, cascade="all, delete-orphan", order_by="ForumComment.created_at.desc()")
    
    def __repr__(self):
        return f"<ForumPost {self.title}>"
    
    @property
    def comment_count(self):
        return len(self.comments)
    
    @property
    def total_votes(self):
        """Calculate total net votes for the post"""
        upvotes = ForumVote.query.filter_by(post_id=self.id, vote_type="upvote").count()
        downvotes = ForumVote.query.filter_by(post_id=self.id, vote_type="downvote").count()
        return upvotes - downvotes


class ForumComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("forum_post.id"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey("forum_comment.id"), nullable=True, index=True)  # For nested replies
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_edited = db.Column(db.Boolean, default=False, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    photos = db.Column(db.Text, nullable=True)  # JSON string of photo filenames
    
    # Relationships
    author = db.relationship("User", backref="forum_comments")
    parent_comment = db.relationship("ForumComment", remote_side=[id], backref="replies")
    
    def __repr__(self):
        return f"<ForumComment {self.id} on post {self.post_id}>"
    
    @property
    def total_votes(self):
        """Calculate total net votes for the comment"""
        upvotes = ForumVote.query.filter_by(comment_id=self.id, vote_type="upvote").count()
        downvotes = ForumVote.query.filter_by(comment_id=self.id, vote_type="downvote").count()
        return upvotes - downvotes


class ForumVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("forum_post.id"), nullable=True, index=True)
    comment_id = db.Column(db.Integer, db.ForeignKey("forum_comment.id"), nullable=True, index=True)
    vote_type = db.Column(db.String(10), nullable=False)  # "upvote" or "downvote"
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship("User", backref="forum_votes")
    post = db.relationship("ForumPost", backref="votes")
    comment = db.relationship("ForumComment", backref="votes")
    
    def __repr__(self):
        return f"<ForumVote {self.vote_type} by {self.user_id}>"
    
    __table_args__ = (
        db.CheckConstraint("vote_type IN ('upvote', 'downvote')"),
        db.CheckConstraint("(post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL)"),
        # Ensure users can only vote once per post or comment
        db.UniqueConstraint("user_id", "post_id", name="unique_user_post_vote"),
        db.UniqueConstraint("user_id", "comment_id", name="unique_user_comment_vote"),
    )

class ProgramReview(db.Model):
    """Model for radiology residency program reviews"""
    id = db.Column(db.Integer, primary_key=True)
    program_name = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    educational_quality = db.Column(db.Integer, nullable=False)  # 1-5 rating
    work_life_balance = db.Column(db.Integer, nullable=False)   # 1-5 rating
    attending_quality = db.Column(db.Integer, nullable=False)   # 1-5 rating
    facilities_quality = db.Column(db.Integer, nullable=False)  # 1-5 rating
    research_opportunities = db.Column(db.Integer, nullable=False)  # 1-5 rating
    culture = db.Column(db.Integer, nullable=False)             # 1-5 rating
    comments = db.Column(db.Text, nullable=True)
    anonymous = db.Column(db.Boolean, default=False, nullable=False)  # Anonymous submission
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='program_reviews')
    
    def __repr__(self):
        return f'<ProgramReview {self.program_name} by {self.user.name}>'

class CompensationData(db.Model):
    """Model for MGMA compensation survey data and anonymous submissions"""
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    region = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    total_compensation = db.Column(db.Integer, nullable=False)  # Annual compensation in USD
    base_salary = db.Column(db.Integer, nullable=False)        # Base salary in USD
    bonus = db.Column(db.Integer, nullable=False)              # Bonus/incentive pay in USD
    rvu_total = db.Column(db.Integer, nullable=True)          # Total RVUs
    rvu_per_work_rvu = db.Column(db.Float, nullable=True)    # Compensation per work RVU
    work_rvus = db.Column(db.Integer, nullable=True)          # Work RVUs
    total_rvus = db.Column(db.Integer, nullable=True)         # Total RVUs
    hours_per_week = db.Column(db.Float, nullable=True)        # Average hours per week
    weeks_per_year = db.Column(db.Float, nullable=False)       # Average weeks per year
    source = db.Column(db.String(100), default='MGMA Survey')
    is_anonymous_submission = db.Column(db.Boolean, default=False)  # True for user submissions
    practice_type = db.Column(db.String(100), nullable=True)   # Private practice, academic, etc.
    experience_years = db.Column(db.Integer, nullable=True)    # Years of experience
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CompensationData {self.specialty} {self.year} {self.region}>'


class JobReview(db.Model):
    """Model for job practice reviews by attending radiologists"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    practice_name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    practice_type = db.Column(db.String(100), nullable=True)  # Private practice, academic, etc.
    work_life_balance = db.Column(db.Integer, nullable=True)  # 1-5 rating, optional
    compensation = db.Column(db.Integer, nullable=True)       # 1-5 rating, optional
    culture = db.Column(db.Integer, nullable=True)           # 1-5 rating, optional
    growth_opportunities = db.Column(db.Integer, nullable=True)  # 1-5 rating, optional
    overall_rating = db.Column(db.Integer, nullable=False)    # 1-5 rating, required
    review_text = db.Column(db.Text, nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='job_reviews')
    
    def __repr__(self):
        return f'<JobReview {self.practice_name} by {self.user.name}>'


class UserSession(db.Model):
    """Track user sessions and online status"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_online = db.Column(db.Boolean, default=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    user = db.relationship("User", backref=db.backref("sessions", lazy=True))
    
    def __repr__(self):
        return f'<UserSession {self.user_id}: {self.is_online}>'


class ShiftSession(db.Model):
    """Model for tracking shift sessions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    total_rvus = db.Column(db.Float, default=0.0, nullable=False)
    compensation_rate = db.Column(db.Float, nullable=False)
    total_revenue = db.Column(db.Float, default=0.0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='shift_sessions')
    rvu_records = db.relationship('RVURecord', backref='shift_session', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ShiftSession {self.user_id} {self.start_time.date()}>'


class RVURecord(db.Model):
    """Model for individual RVU records within a shift"""
    id = db.Column(db.Integer, primary_key=True)
    shift_session_id = db.Column(db.Integer, db.ForeignKey('shift_session.id'), nullable=False)
    study_name = db.Column(db.String(200), nullable=False)
    wrvu_value = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<RVURecord {self.study_name} {self.wrvu_value} wRVUs>'


class EmailVerification(db.Model):
    """Model for storing email verification codes"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    verification_code = db.Column(db.String(5), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'<EmailVerification {self.email}: {self.verification_code}>'
    
    def is_expired(self):
        """Check if the verification code has expired"""
        return datetime.utcnow() > self.expires_at
