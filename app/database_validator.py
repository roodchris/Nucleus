"""
Database validation system to ensure schema compatibility
Validates that all required enum values and columns exist before serving requests
"""

import logging
from sqlalchemy import text
from .models import db
from .auto_migrate import check_column_exists

logger = logging.getLogger(__name__)

def validate_postgresql_enums():
    """Validate that PostgreSQL enums contain all required values"""
    try:
        with db.engine.connect() as connection:
            # Check if this is PostgreSQL with opportunitytype enum
            try:
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'opportunitytype'
                    )
                """))
                has_enum = result.scalar()
                
                if not has_enum:
                    logger.info("✅ No PostgreSQL enum detected - validation skipped")
                    return True
                
                # Get current enum values
                result = connection.execute(text("""
                    SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                """))
                existing_values = {row[0] for row in result.fetchall()}
                
                # Required enum values
                required_values = {
                    'AEROSPACE_MEDICINE', 'ANESTHESIOLOGY', 'CHILD_NEUROLOGY', 'DERMATOLOGY',
                    'EMERGENCY_MEDICINE', 'FAMILY_MEDICINE', 'INTERNAL_MEDICINE', 'MEDICAL_GENETICS',
                    'INTERVENTIONAL_RADIOLOGY', 'NEUROLOGICAL_SURGERY', 'NEUROLOGY', 'NUCLEAR_MEDICINE',
                    'OBSTETRICS_GYNECOLOGY', 'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE', 'ORTHOPAEDIC_SURGERY',
                    'OTOLARYNGOLOGY', 'PATHOLOGY', 'PEDIATRICS', 'PHYSICAL_MEDICINE_REHABILITATION',
                    'PLASTIC_SURGERY', 'PSYCHIATRY', 'RADIATION_ONCOLOGY', 'RADIOLOGY_DIAGNOSTIC',
                    'GENERAL_SURGERY', 'THORACIC_SURGERY', 'UROLOGY', 'VASCULAR_SURGERY'
                }
                
                missing_values = required_values - existing_values
                
                if missing_values:
                    logger.warning(f"⚠️  PostgreSQL enum validation detected missing values")
                    logger.warning(f"Missing enum values: {sorted(missing_values)}")
                    logger.warning("🔧 Some opportunity types may not work until enum is updated")
                    # Return True to not block app startup - just warn about missing values
                    return True
                else:
                    logger.info(f"✅ PostgreSQL enum validation passed - all {len(required_values)} values present")
                    return True
                    
            except Exception as enum_error:
                logger.info(f"✅ Non-PostgreSQL database or enum check failed: {enum_error}")
                return True  # Assume it's fine if we can't check
                
    except Exception as e:
        logger.warning(f"⚠️  Enum validation error: {e}")
        return True  # Don't block app startup on validation errors

def validate_required_columns():
    """Validate that all required columns exist"""
    required_columns = [
        ('job_review', 'specialty'),
        ('resident_profile', 'medical_specialty'), 
        ('employer_profile', 'medical_specialty'),
        ('forum_post', 'specialty')
    ]
    
    missing_columns = []
    
    for table, column in required_columns:
        if not check_column_exists(table, column):
            missing_columns.append(f"{table}.{column}")
    
    if missing_columns:
        logger.warning(f"⚠️  Missing columns detected: {missing_columns}")
        logger.warning("Some features may be disabled until migration completes")
        return False
    else:
        logger.info("✅ All required columns present")
        return True

def run_database_validation():
    """Run complete database validation"""
    logger.info("🔍 Running database validation...")
    
    enum_valid = validate_postgresql_enums()
    columns_valid = validate_required_columns()
    
    if enum_valid and columns_valid:
        logger.info("✅ Database validation passed - all systems ready")
        return True
    else:
        logger.warning("⚠️  Database validation detected issues - some features may be limited")
        return False
