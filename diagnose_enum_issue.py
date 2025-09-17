#!/usr/bin/env python3
"""
Diagnostic script to understand exactly what's happening with the enum
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_enum_issue():
    """Diagnose the exact state of the PostgreSQL enum"""
    
    try:
        # Import without creating full app context to avoid validation
        import os
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            logger.error("❌ DATABASE_URL not found in environment")
            return False
            
        logger.info(f"🔍 Connecting to database: {database_url[:50]}...")
        
        # Use raw psycopg connection
        import psycopg
        
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cursor:
                logger.info("✅ Connected to PostgreSQL database")
                
                # Check if opportunitytype enum exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'opportunitytype'
                    )
                """)
                enum_exists = cursor.fetchone()[0]
                logger.info(f"📊 opportunitytype enum exists: {enum_exists}")
                
                if enum_exists:
                    # Get current enum values
                    cursor.execute("""
                        SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                    """)
                    current_values = [row[0] for row in cursor.fetchall()]
                    logger.info(f"📊 Current enum has {len(current_values)} values:")
                    for value in sorted(current_values):
                        logger.info(f"    - {value}")
                    
                    # Check for specific values we need
                    required_values = ['NEUROLOGICAL_SURGERY', 'FAMILY_MEDICINE', 'EMERGENCY_MEDICINE']
                    missing_critical = [v for v in required_values if v not in current_values]
                    
                    if missing_critical:
                        logger.error(f"❌ Critical missing values: {missing_critical}")
                        
                        # Try to add NEUROLOGICAL_SURGERY directly
                        logger.info("🔧 Attempting to add NEUROLOGICAL_SURGERY directly...")
                        try:
                            cursor.execute("ALTER TYPE opportunitytype ADD VALUE 'NEUROLOGICAL_SURGERY'")
                            conn.commit()
                            logger.info("✅ Successfully added NEUROLOGICAL_SURGERY")
                            
                            # Verify it was added
                            cursor.execute("""
                                SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                            """)
                            new_values = [row[0] for row in cursor.fetchall()]
                            if 'NEUROLOGICAL_SURGERY' in new_values:
                                logger.info("✅ NEUROLOGICAL_SURGERY confirmed in enum")
                                return True
                            else:
                                logger.error("❌ NEUROLOGICAL_SURGERY not found after addition")
                                return False
                                
                        except Exception as e:
                            logger.error(f"❌ Failed to add NEUROLOGICAL_SURGERY: {e}")
                            return False
                    else:
                        logger.info("✅ All critical enum values already exist")
                        return True
                else:
                    logger.error("❌ opportunitytype enum does not exist")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Diagnostic failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Running PostgreSQL enum diagnostic...")
    success = diagnose_enum_issue()
    
    if success:
        logger.info("✅ Enum diagnostic and fix completed!")
    else:
        logger.error("❌ Enum diagnostic failed!")
    
    sys.exit(0 if success else 1)
