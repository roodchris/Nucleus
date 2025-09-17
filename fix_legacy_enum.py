#!/usr/bin/env python3
"""
Fix legacy PostgreSQL enum issue
The production database has old radiology-specific enum values that need to be updated
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_legacy_enum():
    """Fix the legacy PostgreSQL enum by adding all new medical specialties"""
    from app import create_app
    from app.models import db
    from sqlalchemy import text
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔧 Fixing legacy PostgreSQL enum...")
            
            # Check if this is PostgreSQL
            engine_url = str(db.engine.url)
            if 'postgresql' not in engine_url:
                logger.info("✅ Not PostgreSQL - enum fix not needed")
                return True
            
            logger.info("📋 Detected PostgreSQL - proceeding with legacy enum fix...")
            
            # All new specialty values that need to be added
            new_specialty_values = [
                'AEROSPACE_MEDICINE', 'ANESTHESIOLOGY', 'CHILD_NEUROLOGY', 'DERMATOLOGY',
                'EMERGENCY_MEDICINE', 'FAMILY_MEDICINE', 'INTERNAL_MEDICINE', 'MEDICAL_GENETICS',
                'NEUROLOGICAL_SURGERY', 'NEUROLOGY', 'NUCLEAR_MEDICINE', 'OBSTETRICS_GYNECOLOGY',
                'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE', 'ORTHOPAEDIC_SURGERY', 'OTOLARYNGOLOGY',
                'PATHOLOGY', 'PEDIATRICS', 'PHYSICAL_MEDICINE_REHABILITATION', 'PLASTIC_SURGERY',
                'PSYCHIATRY', 'RADIATION_ONCOLOGY', 'RADIOLOGY_DIAGNOSTIC', 'GENERAL_SURGERY',
                'THORACIC_SURGERY', 'UROLOGY', 'VASCULAR_SURGERY'
            ]
            
            # Get current enum values
            with db.engine.connect() as connection:
                try:
                    result = connection.execute(text("""
                        SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                    """))
                    existing_values = set(row[0] for row in result.fetchall())
                    logger.info(f"📊 Current enum values: {sorted(existing_values)}")
                    
                except Exception as e:
                    logger.error(f"❌ Could not read enum values: {e}")
                    return False
                
                # Find values that need to be added
                values_to_add = set(new_specialty_values) - existing_values
                logger.info(f"🔍 Need to add {len(values_to_add)} enum values: {sorted(values_to_add)}")
                
                if not values_to_add:
                    logger.info("✅ All enum values already exist - no fix needed")
                    return True
                
                # Add missing values one by one using autocommit
                success_count = 0
                failed_count = 0
                
                # Use autocommit mode for enum additions
                connection = connection.execution_options(autocommit=True)
                
                for value in sorted(values_to_add):
                    try:
                        connection.execute(text(f"ALTER TYPE opportunitytype ADD VALUE '{value}'"))
                        logger.info(f"    ✅ Added: {value}")
                        success_count += 1
                    except Exception as e:
                        logger.error(f"    ❌ Failed to add {value}: {e}")
                        failed_count += 1
                
                logger.info(f"📊 Results: {success_count} added, {failed_count} failed")
                
                # Verify final state
                try:
                    result = connection.execute(text("""
                        SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                    """))
                    final_values = set(row[0] for row in result.fetchall())
                    logger.info(f"📊 Final enum has {len(final_values)} values: {sorted(final_values)}")
                    
                    still_missing = set(new_specialty_values) - final_values
                    if still_missing:
                        logger.error(f"❌ Still missing enum values: {sorted(still_missing)}")
                        return False
                    else:
                        logger.info("🎉 All required enum values successfully added!")
                        return True
                        
                except Exception as e:
                    logger.error(f"❌ Could not verify final enum state: {e}")
                    return success_count > 0  # Return True if we added at least some values
            
        except Exception as e:
            logger.error(f"❌ Legacy enum fix failed: {e}")
            return False

if __name__ == "__main__":
    logger.info("🚀 Running legacy PostgreSQL enum fix...")
    success = fix_legacy_enum()
    
    if success:
        logger.info("✅ Legacy PostgreSQL enum fix completed successfully!")
        print("SUCCESS: Legacy enum fixed")
    else:
        logger.error("❌ Legacy PostgreSQL enum fix failed!")
        print("FAILED: Legacy enum fix unsuccessful")
    
    sys.exit(0 if success else 1)
