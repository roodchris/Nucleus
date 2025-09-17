#!/usr/bin/env python3
"""
Direct PostgreSQL enum fix - runs the SQL commands directly
This bypasses any transaction issues and directly updates the enum
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_direct_enum_fix():
    """Run direct SQL commands to fix the PostgreSQL enum"""
    from app import create_app
    from app.models import db
    from sqlalchemy import text
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔧 Running direct PostgreSQL enum fix...")
            
            # Check if this is PostgreSQL
            engine_url = str(db.engine.url)
            if 'postgresql' not in engine_url:
                logger.info("✅ Not PostgreSQL - enum fix not needed")
                return True
            
            logger.info("📋 Detected PostgreSQL - running direct enum commands...")
            
            # List of SQL commands to add each enum value
            enum_commands = [
                "ALTER TYPE opportunitytype ADD VALUE 'AEROSPACE_MEDICINE'",
                "ALTER TYPE opportunitytype ADD VALUE 'ANESTHESIOLOGY'",
                "ALTER TYPE opportunitytype ADD VALUE 'CHILD_NEUROLOGY'",
                "ALTER TYPE opportunitytype ADD VALUE 'DERMATOLOGY'",
                "ALTER TYPE opportunitytype ADD VALUE 'EMERGENCY_MEDICINE'",
                "ALTER TYPE opportunitytype ADD VALUE 'FAMILY_MEDICINE'",
                "ALTER TYPE opportunitytype ADD VALUE 'INTERNAL_MEDICINE'",
                "ALTER TYPE opportunitytype ADD VALUE 'MEDICAL_GENETICS'",
                "ALTER TYPE opportunitytype ADD VALUE 'NEUROLOGICAL_SURGERY'",
                "ALTER TYPE opportunitytype ADD VALUE 'NEUROLOGY'",
                "ALTER TYPE opportunitytype ADD VALUE 'NUCLEAR_MEDICINE'",
                "ALTER TYPE opportunitytype ADD VALUE 'OBSTETRICS_GYNECOLOGY'",
                "ALTER TYPE opportunitytype ADD VALUE 'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE'",
                "ALTER TYPE opportunitytype ADD VALUE 'ORTHOPAEDIC_SURGERY'",
                "ALTER TYPE opportunitytype ADD VALUE 'OTOLARYNGOLOGY'",
                "ALTER TYPE opportunitytype ADD VALUE 'PATHOLOGY'",
                "ALTER TYPE opportunitytype ADD VALUE 'PEDIATRICS'",
                "ALTER TYPE opportunitytype ADD VALUE 'PHYSICAL_MEDICINE_REHABILITATION'",
                "ALTER TYPE opportunitytype ADD VALUE 'PLASTIC_SURGERY'",
                "ALTER TYPE opportunitytype ADD VALUE 'PSYCHIATRY'",
                "ALTER TYPE opportunitytype ADD VALUE 'RADIATION_ONCOLOGY'",
                "ALTER TYPE opportunitytype ADD VALUE 'RADIOLOGY_DIAGNOSTIC'",
                "ALTER TYPE opportunitytype ADD VALUE 'GENERAL_SURGERY'",
                "ALTER TYPE opportunitytype ADD VALUE 'THORACIC_SURGERY'",
                "ALTER TYPE opportunitytype ADD VALUE 'UROLOGY'",
                "ALTER TYPE opportunitytype ADD VALUE 'VASCULAR_SURGERY'"
            ]
            
            # Get current enum values first
            with db.engine.connect() as connection:
                try:
                    result = connection.execute(text("""
                        SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                    """))
                    existing_values = set(row[0] for row in result.fetchall())
                    logger.info(f"📊 Current enum values: {sorted(existing_values)}")
                    
                except Exception as e:
                    logger.error(f"❌ Could not read current enum values: {e}")
                    return False
                
                # Execute each command individually
                success_count = 0
                already_exists_count = 0
                failed_count = 0
                
                for command in enum_commands:
                    # Extract the enum value from the command
                    enum_value = command.split("'")[1]
                    
                    if enum_value in existing_values:
                        logger.info(f"    ✅ Already exists: {enum_value}")
                        already_exists_count += 1
                        continue
                    
                    try:
                        # Execute with raw connection to avoid transaction issues
                        raw_connection = db.engine.raw_connection()
                        cursor = raw_connection.cursor()
                        cursor.execute(command)
                        raw_connection.commit()
                        cursor.close()
                        raw_connection.close()
                        
                        logger.info(f"    ✅ Added: {enum_value}")
                        success_count += 1
                        
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.info(f"    ✅ Already exists: {enum_value}")
                            already_exists_count += 1
                        else:
                            logger.error(f"    ❌ Failed to add {enum_value}: {e}")
                            failed_count += 1
                
                logger.info(f"📊 Results: {success_count} added, {already_exists_count} already existed, {failed_count} failed")
                
                # Verify final state
                try:
                    result = connection.execute(text("""
                        SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                    """))
                    final_values = set(row[0] for row in result.fetchall())
                    logger.info(f"📊 Final enum has {len(final_values)} values: {sorted(final_values)}")
                    
                    return success_count > 0 or already_exists_count > 20  # Success if we added values or most already existed
                        
                except Exception as e:
                    logger.error(f"❌ Could not verify final enum state: {e}")
                    return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Direct enum fix failed: {e}")
            return False

if __name__ == "__main__":
    logger.info("🚀 Running direct PostgreSQL enum fix...")
    success = run_direct_enum_fix()
    
    if success:
        logger.info("✅ Direct PostgreSQL enum fix completed!")
        print("SUCCESS: Direct enum fix completed")
    else:
        logger.error("❌ Direct PostgreSQL enum fix failed!")
        print("FAILED: Direct enum fix unsuccessful")
    
    sys.exit(0 if success else 1)
