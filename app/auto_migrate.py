"""
Automatic database migration system
Runs on application startup to ensure database schema is up to date
"""

import logging
from sqlalchemy import text
from .models import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        logger.error(f"Error checking column {table_name}.{column_name}: {e}")
        return False

def run_auto_migration():
    """
    Automatically run database migrations on startup
    This ensures the database schema is always up to date
    """
    try:
        logger.info("🚀 Starting automatic database migration check...")
        
        # Check database connection
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        
        migrations_needed = []
        
        # Check for needed migrations
        if not check_column_exists('job_review', 'specialty'):
            migrations_needed.append(('job_review', 'specialty', 'VARCHAR(100)'))
            
        if not check_column_exists('resident_profile', 'medical_specialty'):
            migrations_needed.append(('resident_profile', 'medical_specialty', 'VARCHAR(100)'))
            
        if not check_column_exists('employer_profile', 'medical_specialty'):
            migrations_needed.append(('employer_profile', 'medical_specialty', 'VARCHAR(100)'))
            
        if not check_column_exists('forum_post', 'specialty'):
            migrations_needed.append(('forum_post', 'specialty', 'VARCHAR(100)'))
        
        # Check if modalities column still exists (should be removed)
        if check_column_exists('employer_profile', 'modalities'):
            migrations_needed.append(('employer_profile', 'DROP modalities', None))
        
        if not migrations_needed:
            logger.info("✅ Database schema is up to date - no migrations needed")
            return True
        
        logger.info(f"📋 Found {len(migrations_needed)} migration(s) to apply...")
        
        # Apply migrations
        with db.engine.connect() as connection:
            for table, column, data_type in migrations_needed:
                try:
                    if column.startswith('DROP'):
                        # Handle column drops
                        column_to_drop = column.split(' ')[1]
                        sql = f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column_to_drop}"
                        logger.info(f"  Removing column {table}.{column_to_drop}...")
                    else:
                        # Handle column additions
                        sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {data_type}"
                        logger.info(f"  Adding column {table}.{column}...")
                    
                    connection.execute(text(sql))
                    logger.info(f"  ✅ Successfully updated {table}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to update {table}: {e}")
                    # Continue with other migrations even if one fails
                    continue
            
            connection.commit()
        
        # Migration 5: Update PostgreSQL enum types to include all specialty values
        logger.info("🔧 Updating PostgreSQL enum types...")
        
        # List of all specialty values that should be in the enum
        all_specialty_values = [
            'AEROSPACE_MEDICINE', 'ANESTHESIOLOGY', 'CHILD_NEUROLOGY', 'DERMATOLOGY',
            'EMERGENCY_MEDICINE', 'FAMILY_MEDICINE', 'INTERNAL_MEDICINE', 'MEDICAL_GENETICS',
            'INTERVENTIONAL_RADIOLOGY', 'NEUROLOGICAL_SURGERY', 'NEUROLOGY', 'NUCLEAR_MEDICINE',
            'OBSTETRICS_GYNECOLOGY', 'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE', 'ORTHOPAEDIC_SURGERY',
            'OTOLARYNGOLOGY', 'PATHOLOGY', 'PEDIATRICS', 'PHYSICAL_MEDICINE_REHABILITATION',
            'PLASTIC_SURGERY', 'PSYCHIATRY', 'RADIATION_ONCOLOGY', 'RADIOLOGY_DIAGNOSTIC',
            'GENERAL_SURGERY', 'THORACIC_SURGERY', 'UROLOGY', 'VASCULAR_SURGERY'
        ]
        
        try:
            with db.engine.connect() as connection:
                # Check if we're using PostgreSQL by looking for the opportunitytype enum
                try:
                    result = connection.execute(text("""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_type WHERE typname = 'opportunitytype'
                        )
                    """))
                    has_enum = result.scalar()
                    
                    if has_enum:
                        logger.info("  Detected PostgreSQL with opportunitytype enum - updating...")
                        
                        # Get current enum values
                        result = connection.execute(text("""
                            SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                        """))
                        existing_values = {row[0] for row in result.fetchall()}
                        logger.info(f"  Current enum values: {sorted(existing_values)}")
                        
                        # Add missing values to opportunitytype enum
                        added_count = 0
                        failed_count = 0
                        
                        for value in all_specialty_values:
                            if value not in existing_values:
                                try:
                                    # Each enum addition needs to be in its own transaction
                                    with db.engine.begin() as trans:
                                        trans.execute(text(f"ALTER TYPE opportunitytype ADD VALUE '{value}'"))
                                    logger.info(f"    ✅ Added enum value: {value}")
                                    added_count += 1
                                except Exception as e:
                                    logger.error(f"    ❌ Failed to add enum value {value}: {e}")
                                    failed_count += 1
                            else:
                                logger.debug(f"    ✅ Enum value already exists: {value}")
                        
                        if added_count > 0:
                            logger.info(f"  ✅ Successfully added {added_count} new enum values")
                        if failed_count > 0:
                            logger.error(f"  ❌ Failed to add {failed_count} enum values")
                        if added_count == 0 and failed_count == 0:
                            logger.info("  ✅ All enum values already exist")
                        
                        # Verify final state
                        result = connection.execute(text("""
                            SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                        """))
                        final_values = {row[0] for row in result.fetchall()}
                        logger.info(f"  Final enum values count: {len(final_values)}")
                        
                    else:
                        logger.info("  ✅ No opportunitytype enum found - likely SQLite")
                        
                except Exception as enum_check_error:
                    logger.info(f"  ✅ Non-PostgreSQL database detected: {enum_check_error}")
                    
        except Exception as e:
            logger.error(f"❌ Error updating enum types: {e}")
            # Don't crash the app if enum update fails
        
        # Update practice type values from Teleradiology to Telemedicine
        try:
            from .models import JobReview, EmployerProfile, CompensationData
            
            job_reviews_updated = db.session.query(JobReview).filter(
                JobReview.practice_type == 'Teleradiology'
            ).update({JobReview.practice_type: 'Telemedicine'}, synchronize_session=False)
            
            employer_profiles_updated = db.session.query(EmployerProfile).filter(
                EmployerProfile.practice_setting == 'Teleradiology'
            ).update({EmployerProfile.practice_setting: 'Telemedicine'}, synchronize_session=False)
            
            compensation_data_updated = db.session.query(CompensationData).filter(
                CompensationData.practice_type == 'Teleradiology'
            ).update({CompensationData.practice_type: 'Telemedicine'}, synchronize_session=False)
            
            db.session.commit()
            
            if job_reviews_updated or employer_profiles_updated or compensation_data_updated:
                logger.info(f"🔄 Updated practice type values:")
                logger.info(f"  - {job_reviews_updated} JobReview records")
                logger.info(f"  - {employer_profiles_updated} EmployerProfile records")
                logger.info(f"  - {compensation_data_updated} CompensationData records")
            
        except Exception as e:
            logger.error(f"❌ Error updating practice type values: {e}")
        
        logger.info("🎉 Automatic database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Automatic migration failed: {e}")
        # Don't crash the app if migration fails - just log the error
        return False

def ensure_schema_compatibility():
    """
    Ensure the application can run even if some columns are missing
    This is called during app initialization
    """
    try:
        # Check if we need to temporarily disable features due to missing columns
        missing_columns = []
        
        if not check_column_exists('forum_post', 'specialty'):
            missing_columns.append('forum_post.specialty')
            
        if not check_column_exists('resident_profile', 'medical_specialty'):
            missing_columns.append('resident_profile.medical_specialty')
            
        if missing_columns:
            logger.warning(f"⚠️  Missing columns detected: {missing_columns}")
            logger.warning("Some features may be temporarily disabled until migration completes")
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking schema compatibility: {e}")
        return False
