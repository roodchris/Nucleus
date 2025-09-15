#!/usr/bin/env python3
"""
Startup script to automatically fix enum case mismatch
This runs when the application starts up
"""
import os
import sys
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def check_and_fix_enum_case():
    """Check if enum case mismatch exists and fix it automatically"""
    app = create_app()
    
    with app.app_context():
        try:
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            
            # Only run for PostgreSQL databases
            if 'postgresql' not in db_url.lower():
                print("ℹ️  Not PostgreSQL - skipping enum case check")
                return True
            
            print("🔍 Checking enum case mismatch...")
            
            # Check current enum values
            result = db.session.execute(text("""
                SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
                ORDER BY enum_value
            """))
            current_values = [row[0] for row in result.fetchall()]
            print(f"Current enum values: {current_values}")
            
            # Check if we have the case mismatch
            has_lowercase = any(value.islower() for value in current_values)
            has_uppercase = any(value.isupper() for value in current_values)
            
            if not has_lowercase and has_uppercase:
                print("✅ Enum case is already correct (uppercase) - no fix needed")
                return True
            elif has_lowercase and not has_uppercase:
                print("🔧 Found lowercase enum values - fixing to uppercase...")
            else:
                print("⚠️  Mixed case enum values detected - fixing to uppercase...")
            
            # Check if INTERVENTIONAL_RADIOLOGY exists
            if 'INTERVENTIONAL_RADIOLOGY' in current_values:
                print("✅ INTERVENTIONAL_RADIOLOGY already exists - no fix needed")
                return True
            
            print("🔧 Creating new enum type with uppercase values...")
            
            # Create new enum type with uppercase values
            db.session.execute(text("""
                CREATE TYPE opportunitytype_new AS ENUM (
                    'IN_PERSON_CONTRAST',
                    'TELE_CONTRAST', 
                    'DIAGNOSTIC_INTERPRETATION',
                    'TELE_DIAGNOSTIC_INTERPRETATION',
                    'INTERVENTIONAL_RADIOLOGY',
                    'CONSULTING_OTHER'
                )
            """))
            print("   ✅ New enum type created")
            
            # Update opportunity table
            print("🔧 Updating opportunity table...")
            db.session.execute(text("""
                ALTER TABLE opportunity 
                ALTER COLUMN opportunity_type TYPE opportunitytype_new 
                USING opportunity_type::text::opportunitytype_new
            """))
            print("   ✅ Opportunity table updated")
            
            # Replace old enum type
            print("🔧 Replacing old enum type...")
            db.session.execute(text("DROP TYPE opportunitytype"))
            db.session.execute(text("ALTER TYPE opportunitytype_new RENAME TO opportunitytype"))
            print("   ✅ Old enum type replaced")
            
            db.session.commit()
            print("✅ Enum case mismatch fixed automatically!")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not fix enum case automatically: {e}")
            # Don't fail the startup, just log the issue
            try:
                db.session.rollback()
            except:
                pass
            return True

if __name__ == "__main__":
    check_and_fix_enum_case()
