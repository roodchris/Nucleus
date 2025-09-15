from typing import List, Tuple
from wtforms import StringField, PasswordField, BooleanField, SelectField, IntegerField, DecimalField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional
from wtforms import ValidationError
from flask_wtf import FlaskForm
from .models import OpportunityType, TrainingLevel, WorkDuration, PayType


def comma_separated_number(min_val=None, max_val=None):
    """Custom validator for comma-separated numbers"""
    def _validate(form, field):
        if field.data:
            # Remove commas and convert to string
            value_str = str(field.data).replace(',', '')
            try:
                value = int(value_str)
                if min_val is not None and value < min_val:
                    raise ValidationError(f'Value must be at least {min_val:,}')
                if max_val is not None and value > max_val:
                    raise ValidationError(f'Value must be at most {max_val:,}')
                # Store the cleaned value
                field.data = value
            except ValueError:
                raise ValidationError('Please enter a valid number (commas are allowed)')
    return _validate


ROLE_CHOICES: List[Tuple[str, str]] = [("employer", "Employer (Job Poster)"), ("resident", "Radiologist (Job Seeker)")]

# Common US timezones for radiology opportunities
TIMEZONE_CHOICES: List[Tuple[str, str]] = [
    ("", "Select Timezone"),
    ("America/New_York", "Eastern Time (ET)"),
    ("America/Chicago", "Central Time (CT)"),
    ("America/Denver", "Mountain Time (MT)"),
    ("America/Los_Angeles", "Pacific Time (PT)"),
    ("America/Anchorage", "Alaska Time (AKT)"),
    ("Pacific/Honolulu", "Hawaii Time (HST)"),
    ("America/Phoenix", "Arizona Time (MST)"),
]

OPP_TYPE_CHOICES: List[Tuple[str, str]] = [
    ("", "Any Type"),
    (OpportunityType.IN_PERSON_CONTRAST.value, "In-person contrast coverage"),
    (OpportunityType.TELE_CONTRAST.value, "Tele contrast coverage"),
    (OpportunityType.DIAGNOSTIC_INTERPRETATION.value, "Diagnostic interpretation"),
    (OpportunityType.TELE_DIAGNOSTIC_INTERPRETATION.value, "Tele diagnostic interpretation"),
    (OpportunityType.INTERVENTIONAL_RADIOLOGY.value, "Interventional radiology"),
    (OpportunityType.CONSULTING_OTHER.value, "Consulting & Other Opportunities"),
]

TRAINING_LEVEL_CHOICES: List[Tuple[str, str]] = [
    ("", "Select Training Level"),
    (TrainingLevel.R1.value, "R1"),
    (TrainingLevel.R2.value, "R2"),
    (TrainingLevel.R3.value, "R3"),
    (TrainingLevel.R4.value, "R4"),
    (TrainingLevel.FELLOW.value, "FELLOW"),
    (TrainingLevel.ATTENDING.value, "ATTENDING"),
]

PAY_TYPE_CHOICES: List[Tuple[str, str]] = [
    ("", "Select Pay Type"),
    (PayType.PER_HOUR.value, "$/hr"),
    (PayType.PER_RVU.value, "$/RVU"),
    (PayType.PER_YEAR.value, "$/year"),
]

WORK_DURATION_CHOICES: List[Tuple[str, str]] = [
    ("", "Select Work Duration"),
    (WorkDuration.SINGLE_SHIFT.value, "Single Shift"),
    (WorkDuration.SHORT_TERM.value, "Short-term (less than 1 month)"),
    (WorkDuration.MEDIUM_TERM.value, "Medium-term (1 month to 6 months)"),
    (WorkDuration.PERMANENT.value, "Permanent Employment"),
]


class SignupForm(FlaskForm):
    name = StringField("Name (can use a username to stay anonymous)", validators=[DataRequired(), Length(max=255)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=255)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    role = SelectField("Role", choices=ROLE_CHOICES, validators=[DataRequired()])
    organization = StringField("Organization (for employers)", validators=[Optional(), Length(max=255)])


class EmailVerificationForm(FlaskForm):
    verification_code = StringField("Verification Code", validators=[DataRequired(), Length(min=5, max=5)])


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=255)])
    remember = BooleanField("Remember me")


class OpportunityForm(FlaskForm):
    title = StringField("Title", validators=[Optional(), Length(max=255)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=5000)])
    opportunity_type = SelectField("Type", choices=[("", "Select Type")] + OPP_TYPE_CHOICES[1:], validators=[Optional()])
    zip_code = StringField("Zip Code", validators=[Optional(), Length(min=5, max=10)])
    pgy_min = SelectField("Training Level Minimum", choices=[("", "Select Minimum")] + TRAINING_LEVEL_CHOICES[1:], validators=[Optional()])
    pgy_max = SelectField("Training Level Maximum", choices=[("", "Select Maximum")] + TRAINING_LEVEL_CHOICES[1:], validators=[Optional()])
    pay_amount = DecimalField("Pay Amount", validators=[Optional(), NumberRange(min=0)], places=2)
    pay_type = SelectField("Pay Type", choices=PAY_TYPE_CHOICES, validators=[Optional()])
    shift_length_hours = DecimalField("Shift length (hours)", validators=[Optional(), NumberRange(min=0)], places=1)
    hours_per_week = DecimalField("Hours per week", validators=[Optional(), NumberRange(min=0)], places=1)
    timezone = SelectField("Timezone", choices=TIMEZONE_CHOICES, validators=[Optional()])
    work_duration = SelectField("Work Duration", choices=WORK_DURATION_CHOICES, validators=[Optional()])

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        
        # Only validate training level logic if both fields are provided
        if self.pgy_min.data and self.pgy_min.data != "" and self.pgy_max.data and self.pgy_max.data != "":
            level_order = {TrainingLevel.R1: 1, TrainingLevel.R2: 2, TrainingLevel.R3: 3, 
                          TrainingLevel.R4: 4, TrainingLevel.FELLOW: 5, TrainingLevel.ATTENDING: 6}
            min_level = level_order.get(TrainingLevel(self.pgy_min.data), 0)
            max_level = level_order.get(TrainingLevel(self.pgy_max.data), 0)
            if min_level > max_level:
                self.pgy_max.errors.append("Training level max must be greater than or equal to training level min")
                return False
        return True


class FilterForm(FlaskForm):
    opportunity_type = SelectField("Type", choices=OPP_TYPE_CHOICES, validators=[Optional()])
    zip_code = StringField("Zip Code", validators=[Optional(), Length(min=5, max=10)])
    radius_miles = IntegerField("Radius (miles)", validators=[Optional(), NumberRange(min=1)])
    pgy_year = SelectField("Your Current Training Level", choices=TRAINING_LEVEL_CHOICES, validators=[Optional()])
    minimum_pay = DecimalField("Minimum Pay", validators=[Optional(), NumberRange(min=0)], places=2)
    pay_type = SelectField("Pay Type", choices=PAY_TYPE_CHOICES, validators=[Optional()])
    work_duration = SelectField("Work Duration", choices=[("", "Any Duration")] + WORK_DURATION_CHOICES[1:], validators=[Optional()])


class CompensationSubmissionForm(FlaskForm):
    year = IntegerField("Year", validators=[DataRequired(), NumberRange(min=2020, max=2025)])
    region = SelectField("Region", choices=[
        ('', 'Select Region'),
        ('Northeast', 'Northeast'),
        ('Southeast', 'Southeast'),
        ('Midwest', 'Midwest'),
        ('West', 'West')
    ], validators=[DataRequired()])
    specialty = SelectField("Specialty", choices=[
        ('', 'Select Specialty'),
        ('Diagnostic', 'Diagnostic'),
        ('Interventional', 'Interventional')
    ], validators=[DataRequired()])
    total_compensation = StringField("Total Annual Compensation ($)", validators=[DataRequired(), comma_separated_number(min_val=50000, max_val=2000000)])
    practice_type = SelectField("Practice Type", choices=[
        ('', 'Select Practice Type'),
        ('Private Practice', 'Private Practice'),
        ('Academic', 'Academic'),
        ('Hospital Employed', 'Hospital Employed'),
        ('Government', 'Government'),
        ('Teleradiology', 'Teleradiology'),
        ('1099 Contractor', '1099 Contractor'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    hours_per_week = DecimalField("Hours per Week", validators=[Optional(), NumberRange(min=10, max=100)], places=1)
    
    # Optional fields
    total_yearly_rvu = StringField("Total Yearly RVU", validators=[Optional(), comma_separated_number(min_val=1000, max_val=20000)])
    compensation_per_rvu = StringField("Compensation per RVU ($)", validators=[Optional(), comma_separated_number(min_val=0)])
    weeks_vacation = IntegerField("Weeks of Vacation", validators=[Optional(), NumberRange(min=0, max=50)])


class JobReviewForm(FlaskForm):
    practice_name = StringField("Practice Name", validators=[DataRequired(), Length(max=200)])
    location = StringField("Location (City, State)", validators=[DataRequired(), Length(max=200)])
    practice_type = SelectField("Practice Type (optional)", choices=[
        ('', 'Select Practice Type'),
        ('Private Practice', 'Private Practice'),
        ('Academic', 'Academic'),
        ('Hospital Employed', 'Hospital Employed'),
        ('Government', 'Government'),
        ('Teleradiology', 'Teleradiology'),
        ('1099 Contractor', '1099 Contractor'),
        ('Other', 'Other')
    ], validators=[Optional()])
    work_life_balance = SelectField("Work-Life Balance (optional)", choices=[
        ('', 'Not Rated'),
        (1, "1 - Poor"),
        (2, "2 - Below Average"),
        (3, "3 - Average"),
        (4, "4 - Above Average"),
        (5, "5 - Excellent")
    ], validators=[Optional()])
    compensation = SelectField("Compensation (optional)", choices=[
        ('', 'Not Rated'),
        (1, "1 - Poor"),
        (2, "2 - Below Average"),
        (3, "3 - Average"),
        (4, "4 - Above Average"),
        (5, "5 - Excellent")
    ], validators=[Optional()])
    culture = SelectField("Culture & Environment (optional)", choices=[
        ('', 'Not Rated'),
        (1, "1 - Poor"),
        (2, "2 - Below Average"),
        (3, "3 - Average"),
        (4, "4 - Above Average"),
        (5, "5 - Excellent")
    ], validators=[Optional()])
    growth_opportunities = SelectField("Growth & Development Opportunities (optional)", choices=[
        ('', 'Not Rated'),
        (1, "1 - Poor"),
        (2, "2 - Below Average"),
        (3, "3 - Average"),
        (4, "4 - Above Average"),
        (5, "5 - Excellent")
    ], validators=[Optional()])
    overall_rating = SelectField("Overall Rating", choices=[
        (1, "1 - Poor"),
        (2, "2 - Below Average"),
        (3, "3 - Average"),
        (4, "4 - Above Average"),
        (5, "5 - Excellent")
    ], validators=[DataRequired()])
    review_text = TextAreaField("Detailed Review (optional)", validators=[Optional(), Length(max=5000)])
    is_anonymous = BooleanField("Submit anonymously")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values for optional fields to empty string
        if not self.practice_type.data:
            self.practice_type.data = ''
        if not self.work_life_balance.data:
            self.work_life_balance.data = ''
        if not self.compensation.data:
            self.compensation.data = ''
        if not self.culture.data:
            self.culture.data = ''
        if not self.growth_opportunities.data:
            self.growth_opportunities.data = ''
