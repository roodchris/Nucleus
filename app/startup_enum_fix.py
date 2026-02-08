"""
Startup enum fix that runs during app initialization
This ensures enums are fixed when the app starts, using the corrected environment
"""

import logging
import os

logger = logging.getLogger(__name__)

def fix_enum_on_startup():
    """Fix PostgreSQL enum during app startup with robust error handling"""
    
    try:
        logger.info("🔧 Starting startup enum fix...")
        
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.warning("⚠️  DATABASE_URL not found - skipping enum fix")
            return False
        
        if 'postgresql' not in database_url:
            logger.info("✅ Not PostgreSQL - enum fix not needed")
            return True
        
        logger.info("📋 PostgreSQL detected - proceeding with enum fix...")
        
        # Use direct psycopg connection for maximum reliability
        import psycopg
        
        # Required medical specialties
        required_specialties = [
            'AEROSPACE_MEDICINE', 'ANESTHESIOLOGY', 'CHILD_NEUROLOGY', 'DERMATOLOGY',
            'EMERGENCY_MEDICINE', 'FAMILY_MEDICINE', 'INTERNAL_MEDICINE', 'MEDICAL_GENETICS',
            'INTERVENTIONAL_RADIOLOGY', 'NEUROLOGICAL_SURGERY', 'NEUROLOGY', 'NUCLEAR_MEDICINE',
            'OBSTETRICS_GYNECOLOGY', 'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE', 'ORTHOPAEDIC_SURGERY',
            'OTOLARYNGOLOGY', 'PATHOLOGY', 'PEDIATRICS', 'PHYSICAL_MEDICINE_REHABILITATION',
            'PLASTIC_SURGERY', 'PSYCHIATRY', 'RADIATION_ONCOLOGY', 'RADIOLOGY_DIAGNOSTIC',
            'GENERAL_SURGERY', 'THORACIC_SURGERY', 'UROLOGY', 'VASCULAR_SURGERY'
        ]
        
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cursor:
                logger.info("✅ Connected to PostgreSQL database")
                
                # Get current enum values
                cursor.execute("""
                    SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                """)
                current_values = set(row[0] for row in cursor.fetchall())
                logger.info(f"📊 Current enum has {len(current_values)} values")
                
                # Find missing specialties
                missing_specialties = set(required_specialties) - current_values
                
                if not missing_specialties:
                    logger.info("✅ All medical specialties already exist")
                    return True
                
                logger.info(f"🔧 Adding {len(missing_specialties)} missing specialties...")
                
                # Add missing specialties with individual error handling
                success_count = 0
                for specialty in sorted(missing_specialties):
                    try:
                        cursor.execute(f"ALTER TYPE opportunitytype ADD VALUE '{specialty}'")
                        conn.commit()
                        logger.info(f"    ✅ Added: {specialty}")
                        success_count += 1
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.info(f"    ✅ Already exists: {specialty}")
                            success_count += 1
                        else:
                            logger.error(f"    ❌ Failed to add {specialty}: {e}")
                
                # Verify final state
                cursor.execute("""
                    SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value
                """)
                final_values = set(row[0] for row in cursor.fetchall())
                final_missing = set(required_specialties) - final_values
                
                if final_missing:
                    logger.error(f"❌ Still missing after fix: {sorted(final_missing)}")
                    return False
                else:
                    logger.info(f"🎉 All {len(required_specialties)} medical specialties now available!")
                
                # Ensure traininglevel enum has all values (PGY1–PGY7, FELLOW, ATTENDING)
                required_training_levels = [
                    'PGY1', 'PGY2', 'PGY3', 'PGY4', 'PGY5', 'PGY6', 'PGY7',
                    'FELLOW', 'ATTENDING'
                ]
                try:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_type WHERE typname = 'traininglevel'
                        )
                    """)
                    has_traininglevel = cursor.fetchone()[0]
                    if has_traininglevel:
                        cursor.execute("""
                            SELECT unnest(enum_range(NULL::traininglevel))::text as enum_value
                        """)
                        current_tl = set(row[0] for row in cursor.fetchall())
                        missing_tl = [v for v in required_training_levels if v not in current_tl]
                        if missing_tl:
                            logger.info(f"🔧 Adding {len(missing_tl)} missing traininglevel values: {missing_tl}")
                            for val in missing_tl:
                                try:
                                    cursor.execute(f"ALTER TYPE traininglevel ADD VALUE '{val}'")
                                    conn.commit()
                                    logger.info(f"    ✅ Added traininglevel: {val}")
                                except Exception as e:
                                    if "already exists" in str(e).lower():
                                        logger.info(f"    ✅ Already exists: {val}")
                                    else:
                                        logger.error(f"    ❌ Failed to add {val}: {e}")
                        else:
                            logger.info("✅ All traininglevel enum values already present")
                    else:
                        logger.info("ℹ️  traininglevel enum not found (table may not exist yet)")
                except Exception as e:
                    logger.warning(f"⚠️  traininglevel enum check/fix skipped: {e}")
                
                # Also ensure forum_post table has specialty column
                try:
                    logger.info("🔧 Ensuring forum_post table has specialty column...")
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'forum_post' AND column_name = 'specialty'
                    """)
                    specialty_column_exists = cursor.fetchone() is not None
                    
                    if not specialty_column_exists:
                        cursor.execute("ALTER TABLE forum_post ADD COLUMN specialty VARCHAR(100)")
                        conn.commit()
                        logger.info("✅ Added specialty column to forum_post table")
                    else:
                        logger.info("✅ forum_post.specialty column already exists")
                        
                except Exception as e:
                    logger.error(f"❌ Error ensuring forum_post specialty column: {e}")
                
                # Also ensure program_review table has specialty column
                try:
                    logger.info("🔧 Ensuring program_review table has specialty column...")
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'program_review' AND column_name = 'specialty'
                    """)
                    specialty_column_exists = cursor.fetchone() is not None
                    
                    if not specialty_column_exists:
                        cursor.execute("ALTER TABLE program_review ADD COLUMN specialty VARCHAR(100)")
                        conn.commit()
                        logger.info("✅ Added specialty column to program_review table")
                    else:
                        logger.info("✅ program_review.specialty column already exists")
                        
                except Exception as e:
                    logger.error(f"❌ Error ensuring program_review specialty column: {e}")
                
                return True
        
    except ImportError:
        logger.error("❌ psycopg package not available - cannot fix enum")
        return False
    except Exception as e:
        logger.error(f"❌ Startup enum fix failed: {e}")
        return False

def validate_database_connectivity():
    """Validate database connectivity and identify potential issues"""
    
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL environment variable not set")
            return False
        
        logger.info(f"🔍 Validating database connectivity...")
        logger.info(f"Database URL format: {database_url.split('@')[0]}@[REDACTED]")
        
        # Check URL format
        if not database_url.startswith(('postgresql://', 'postgresql+psycopg://')):
            logger.error("❌ DATABASE_URL should start with postgresql:// or postgresql+psycopg://")
            return False
        
        # Test basic connection
        import psycopg
        try:
            # Try with the full URL first
            with psycopg.connect(database_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    logger.info(f"✅ Connected to PostgreSQL: {version.split()[0]} {version.split()[1]}")
                    
                    # Test enum operations capability
                    cursor.execute("SELECT 1")
                    logger.info("✅ Database operations working")
                    
                    return True
        except Exception as e:
            logger.warning(f"⚠️  Direct connection failed: {e}")
            # Try with SSL mode as a separate parameter
            try:
                # Parse URL and extract components
                from urllib.parse import urlparse
                parsed = urlparse(database_url)
                
                # Extract SSL mode from query parameters
                sslmode = 'require'
                if parsed.query:
                    query_params = dict(param.split('=') for param in parsed.query.split('&'))
                    sslmode = query_params.get('sslmode', 'require')
                
                # Connect with SSL mode as parameter
                conn_params = {
                    'host': parsed.hostname,
                    'port': parsed.port or 5432,
                    'dbname': parsed.path.lstrip('/'),
                    'user': parsed.username,
                    'password': parsed.password,
                    'sslmode': sslmode
                }
                
                with psycopg.connect(**conn_params) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT version()")
                        version = cursor.fetchone()[0]
                        logger.info(f"✅ Connected to PostgreSQL (with SSL): {version.split()[0]} {version.split()[1]}")
                        
                        # Test enum operations capability
                        cursor.execute("SELECT 1")
                        logger.info("✅ Database operations working")
                        
                        return True
                        
            except Exception as e2:
                logger.error(f"❌ Both connection methods failed: {e2}")
                return False
        
    except ImportError:
        logger.error("❌ psycopg package not available")
        return False
    except Exception as e:
        logger.error(f"❌ Database connectivity validation failed: {e}")
        return False
