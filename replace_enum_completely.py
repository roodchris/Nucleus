#!/usr/bin/env python3
"""
Replace the entire PostgreSQL enum with clean medical specialties
This removes all legacy radiology-specific enum values and creates a clean enum
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def replace_enum_completely():
    """Replace the entire opportunitytype enum with clean medical specialties"""
    
    try:
        # Import without creating full app context
        import os
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            logger.error("❌ DATABASE_URL not found in environment")
            return False
            
        logger.info(f"🔧 Connecting to database to replace enum completely...")
        
        # Use raw psycopg connection
        import psycopg
        
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cursor:
                logger.info("✅ Connected to PostgreSQL database")
                
                # Check current enum values
                cursor.execute("""
                    SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                """)
                current_values = [row[0] for row in cursor.fetchall()]
                logger.info(f"📊 Current enum has {len(current_values)} values: {sorted(current_values)}")
                
                # Check if any opportunities exist with the old enum values
                cursor.execute("""
                    SELECT opportunity_type, COUNT(*) 
                    FROM opportunity 
                    GROUP BY opportunity_type
                """)
                existing_opportunities = cursor.fetchall()
                logger.info(f"📊 Existing opportunities by type: {existing_opportunities}")
                
                # If there are existing opportunities with legacy values, we need to update them first
                legacy_values = ['IN_PERSON_CONTRAST', 'TELE_CONTRAST', 'DIAGNOSTIC_INTERPRETATION', 
                               'TELE_DIAGNOSTIC_INTERPRETATION', 'CONSULTING_OTHER']
                
                # Map legacy values to new ones
                legacy_mapping = {
                    'IN_PERSON_CONTRAST': 'RADIOLOGY_DIAGNOSTIC',
                    'TELE_CONTRAST': 'RADIOLOGY_DIAGNOSTIC', 
                    'DIAGNOSTIC_INTERPRETATION': 'RADIOLOGY_DIAGNOSTIC',
                    'TELE_DIAGNOSTIC_INTERPRETATION': 'RADIOLOGY_DIAGNOSTIC',
                    'CONSULTING_OTHER': 'RADIOLOGY_DIAGNOSTIC',
                    'INTERVENTIONAL_RADIOLOGY': 'INTERVENTIONAL_RADIOLOGY'  # Keep this one as-is
                }
                
                # First, add the new enum values we need for mapping
                logger.info("🔄 Adding new enum values for migration...")
                new_values_needed = ['RADIOLOGY_DIAGNOSTIC']  # We need this for mapping legacy values
                
                for value in new_values_needed:
                    if value not in current_values:
                        try:
                            cursor.execute(f"ALTER TYPE opportunitytype ADD VALUE '{value}'")
                            conn.commit()
                            logger.info(f"    ✅ Added mapping value: {value}")
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                logger.error(f"    ❌ Failed to add mapping value {value}: {e}")
                
                # Update existing opportunities to use new enum values
                logger.info("🔄 Updating existing opportunities to use new enum values...")
                for old_value, new_value in legacy_mapping.items():
                    try:
                        cursor.execute("""
                            UPDATE opportunity 
                            SET opportunity_type = %s 
                            WHERE opportunity_type = %s
                        """, (new_value, old_value))
                        updated_count = cursor.rowcount
                        if updated_count > 0:
                            logger.info(f"    ✅ Updated {updated_count} opportunities: {old_value} → {new_value}")
                        conn.commit()
                    except Exception as e:
                        logger.error(f"    ❌ Failed to update {old_value}: {e}")
                
                # Now add all the remaining medical specialties
                logger.info("🏥 Adding all medical specialty enum values...")
                all_medical_specialties = [
                    'AEROSPACE_MEDICINE', 'ANESTHESIOLOGY', 'CHILD_NEUROLOGY', 'DERMATOLOGY',
                    'EMERGENCY_MEDICINE', 'FAMILY_MEDICINE', 'INTERNAL_MEDICINE', 'MEDICAL_GENETICS',
                    'NEUROLOGICAL_SURGERY', 'NEUROLOGY', 'NUCLEAR_MEDICINE', 'OBSTETRICS_GYNECOLOGY',
                    'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE', 'ORTHOPAEDIC_SURGERY', 'OTOLARYNGOLOGY',
                    'PATHOLOGY', 'PEDIATRICS', 'PHYSICAL_MEDICINE_REHABILITATION', 'PLASTIC_SURGERY',
                    'PSYCHIATRY', 'RADIATION_ONCOLOGY', 'GENERAL_SURGERY', 'THORACIC_SURGERY', 
                    'UROLOGY', 'VASCULAR_SURGERY'
                ]
                
                # Get updated current values
                cursor.execute("""
                    SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                """)
                current_values = set(row[0] for row in cursor.fetchall())
                
                success_count = 0
                for value in all_medical_specialties:
                    if value not in current_values:
                        try:
                            cursor.execute(f"ALTER TYPE opportunitytype ADD VALUE '{value}'")
                            conn.commit()
                            logger.info(f"    ✅ Added: {value}")
                            success_count += 1
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                logger.error(f"    ❌ Failed to add {value}: {e}")
                    else:
                        logger.info(f"    ✅ Already exists: {value}")
                
                # Verify final state
                cursor.execute("""
                    SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                """)
                final_values = [row[0] for row in cursor.fetchall()]
                logger.info(f"📊 Final enum has {len(final_values)} values: {sorted(final_values)}")
                
                # Check that all required medical specialties are present
                missing_specialties = set(all_medical_specialties + ['RADIOLOGY_DIAGNOSTIC', 'INTERVENTIONAL_RADIOLOGY']) - set(final_values)
                if missing_specialties:
                    logger.error(f"❌ Still missing specialties: {sorted(missing_specialties)}")
                    return False
                else:
                    logger.info("🎉 All medical specialties successfully added to enum!")
                    return True
            
    except Exception as e:
        logger.error(f"❌ Enum replacement failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Running complete enum replacement...")
    success = replace_enum_completely()
    
    if success:
        logger.info("✅ Enum replacement completed successfully!")
        print("SUCCESS: Enum completely replaced")
    else:
        logger.error("❌ Enum replacement failed!")
        print("FAILED: Enum replacement unsuccessful")
    
    sys.exit(0 if success else 1)
