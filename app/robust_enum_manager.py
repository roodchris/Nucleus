"""
Robust PostgreSQL enum management system
This system ensures enums are properly managed regardless of environment issues
"""

import logging
import os
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

class RobustEnumManager:
    """Manages PostgreSQL enums with robust error handling and validation"""
    
    def __init__(self):
        self.required_specialties = [
            'AEROSPACE_MEDICINE', 'ANESTHESIOLOGY', 'CHILD_NEUROLOGY', 'DERMATOLOGY',
            'EMERGENCY_MEDICINE', 'FAMILY_MEDICINE', 'INTERNAL_MEDICINE', 'MEDICAL_GENETICS',
            'INTERVENTIONAL_RADIOLOGY', 'NEUROLOGICAL_SURGERY', 'NEUROLOGY', 'NUCLEAR_MEDICINE',
            'OBSTETRICS_GYNECOLOGY', 'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE', 'ORTHOPAEDIC_SURGERY',
            'OTOLARYNGOLOGY', 'PATHOLOGY', 'PEDIATRICS', 'PHYSICAL_MEDICINE_REHABILITATION',
            'PLASTIC_SURGERY', 'PSYCHIATRY', 'RADIATION_ONCOLOGY', 'RADIOLOGY_DIAGNOSTIC',
            'GENERAL_SURGERY', 'THORACIC_SURGERY', 'UROLOGY', 'VASCULAR_SURGERY'
        ]
    
    def get_database_connection(self):
        """Get database connection with multiple fallback methods"""
        try:
            # Method 1: Try DATABASE_URL from environment
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                logger.info("✅ Using DATABASE_URL from environment")
                return create_engine(database_url)
            
            # Method 2: Try from Flask app config
            try:
                from flask import current_app
                database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
                if database_url:
                    logger.info("✅ Using DATABASE_URL from Flask config")
                    return create_engine(database_url)
            except:
                pass
            
            # Method 3: Try from models
            try:
                from .models import db
                if db.engine:
                    logger.info("✅ Using existing database engine")
                    return db.engine
            except:
                pass
            
            logger.error("❌ Could not get database connection")
            return None
            
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            return None
    
    def check_postgresql_enum_exists(self, engine):
        """Check if PostgreSQL opportunitytype enum exists"""
        try:
            with engine.connect() as connection:
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'opportunitytype'
                    )
                """))
                return result.scalar()
        except Exception as e:
            logger.warning(f"⚠️  Could not check enum existence: {e}")
            return False
    
    def get_current_enum_values(self, engine):
        """Get current enum values from PostgreSQL"""
        try:
            with engine.connect() as connection:
                result = connection.execute(text("""
                    SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                """))
                return set(row[0] for row in result.fetchall())
        except Exception as e:
            logger.error(f"❌ Could not get enum values: {e}")
            return set()
    
    def add_enum_value_safely(self, engine, enum_value):
        """Add a single enum value with maximum safety"""
        try:
            # Use raw psycopg connection for maximum reliability
            import psycopg
            database_url = str(engine.url)
            
            with psycopg.connect(database_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"ALTER TYPE opportunitytype ADD VALUE '{enum_value}'")
                    conn.commit()
            
            logger.info(f"    ✅ Added enum value: {enum_value}")
            return True
            
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"    ✅ Enum value already exists: {enum_value}")
                return True
            else:
                logger.error(f"    ❌ Failed to add enum value {enum_value}: {e}")
                return False
    
    def ensure_all_specialties_exist(self):
        """Ensure all medical specialties exist in the PostgreSQL enum"""
        logger.info("🏥 Starting robust enum management...")
        
        # Get database connection
        engine = self.get_database_connection()
        if not engine:
            logger.error("❌ Could not establish database connection")
            return False
        
        # Check if this is PostgreSQL with the enum
        if not self.check_postgresql_enum_exists(engine):
            logger.info("✅ Not PostgreSQL or enum doesn't exist - skipping")
            return True
        
        logger.info("📋 PostgreSQL opportunitytype enum detected")
        
        # Get current enum values
        current_values = self.get_current_enum_values(engine)
        logger.info(f"📊 Current enum has {len(current_values)} values: {sorted(current_values)}")
        
        # Find missing specialties
        missing_specialties = set(self.required_specialties) - current_values
        
        if not missing_specialties:
            logger.info("✅ All medical specialties already exist in enum")
            return True
        
        logger.info(f"🔧 Need to add {len(missing_specialties)} specialties: {sorted(missing_specialties)}")
        
        # Add missing specialties one by one
        success_count = 0
        for specialty in sorted(missing_specialties):
            if self.add_enum_value_safely(engine, specialty):
                success_count += 1
        
        # Verify final state
        final_values = self.get_current_enum_values(engine)
        final_missing = set(self.required_specialties) - final_values
        
        if final_missing:
            logger.error(f"❌ Still missing specialties: {sorted(final_missing)}")
            logger.error("🔧 Manual intervention required - see SIMPLE_MANUAL_FIX.md")
            return False
        else:
            logger.info(f"🎉 All {len(self.required_specialties)} medical specialties now available!")
            logger.info(f"📊 Final enum has {len(final_values)} total values")
            return True

# Global instance
enum_manager = RobustEnumManager()

def ensure_enum_compatibility():
    """Public function to ensure enum compatibility"""
    return enum_manager.ensure_all_specialties_exist()
