#!/usr/bin/env python3
"""
Dedicated PostgreSQL enum fix script for production
This script focuses specifically on fixing the enum issues
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_postgresql_enums():
    """Fix PostgreSQL enum issues permanently"""
    from app import create_app
    from app.models import db
    from sqlalchemy import text
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔧 Starting PostgreSQL enum fix...")
            
            # All specialty values that need to be in the enum
            all_specialty_values = [
                'AEROSPACE_MEDICINE', 'ANESTHESIOLOGY', 'CHILD_NEUROLOGY', 'DERMATOLOGY',
                'EMERGENCY_MEDICINE', 'FAMILY_MEDICINE', 'INTERNAL_MEDICINE', 'MEDICAL_GENETICS',
                'INTERVENTIONAL_RADIOLOGY', 'NEUROLOGICAL_SURGERY', 'NEUROLOGY', 'NUCLEAR_MEDICINE',
                'OBSTETRICS_GYNECOLOGY', 'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE', 'ORTHOPAEDIC_SURGERY',
                'OTOLARYNGOLOGY', 'PATHOLOGY', 'PEDIATRICS', 'PHYSICAL_MEDICINE_REHABILITATION',
                'PLASTIC_SURGERY', 'PSYCHIATRY', 'RADIATION_ONCOLOGY', 'RADIOLOGY_DIAGNOSTIC',
                'GENERAL_SURGERY', 'THORACIC_SURGERY', 'UROLOGY', 'VASCULAR_SURGERY'
            ]
            
            # Check if this is PostgreSQL
            engine_url = str(db.engine.url)
            if 'postgresql' not in engine_url:
                logger.info("✅ Not PostgreSQL - enum fix not needed")
                return True
            
            logger.info("📋 Detected PostgreSQL - proceeding with enum fix...")
            
            # Get current enum values
            with db.engine.connect() as connection:
                try:
                    result = connection.execute(text("""
                        SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                    """))
                    existing_values = set(row[0] for row in result.fetchall())
                    logger.info(f"📊 Current enum has {len(existing_values)} values: {sorted(existing_values)}")
                    
                except Exception as e:
                    logger.error(f"❌ Could not read enum values: {e}")
                    return False
                
                # Find missing values
                missing_values = set(all_specialty_values) - existing_values
                logger.info(f"🔍 Found {len(missing_values)} missing enum values: {sorted(missing_values)}")
                
                if not missing_values:
                    logger.info("✅ All enum values already exist - no fix needed")
                    return True
                
                # Add missing values one by one
                success_count = 0
                for value in sorted(missing_values):
                    try:
                        # Use autocommit mode for enum additions
                        connection.execute(text(f"ALTER TYPE opportunitytype ADD VALUE '{value}'"))
                        logger.info(f"    ✅ Added: {value}")
                        success_count += 1
                    except Exception as e:
                        logger.error(f"    ❌ Failed to add {value}: {e}")
                
                # Verify final state
                try:
                    result = connection.execute(text("""
                        SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                    """))
                    final_values = set(row[0] for row in result.fetchall())
                    logger.info(f"📊 Final enum has {len(final_values)} values")
                    
                    still_missing = set(all_specialty_values) - final_values
                    if still_missing:
                        logger.error(f"❌ Still missing enum values: {sorted(still_missing)}")
                        return False
                    else:
                        logger.info("🎉 All enum values successfully added!")
                        return True
                        
                except Exception as e:
                    logger.error(f"❌ Could not verify final enum state: {e}")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Enum fix failed: {e}")
            return False

if __name__ == "__main__":
    logger.info("🚀 Running dedicated PostgreSQL enum fix...")
    success = fix_postgresql_enums()
    
    if success:
        logger.info("✅ PostgreSQL enum fix completed successfully!")
        print("SUCCESS: All enum values added")
    else:
        logger.error("❌ PostgreSQL enum fix failed!")
        print("FAILED: Enum fix unsuccessful")
    
    sys.exit(0 if success else 1)
