#!/usr/bin/env python3
"""
Fix the enum case mismatch issue
The problem is that the database has lowercase enum values but the application is sending uppercase
"""
import os
import sys
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def fix_enum_case_issue():
    """Fix the enum case mismatch by updating the database enum to match what the app sends"""
    app = create_app()
    
    with app.app_context():
        try:
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"Database URL: {db_url}")
            
            if 'postgresql' not in db_url.lower():
                print("This script is for PostgreSQL databases only")
                return False
            
            print("PostgreSQL detected - fixing enum case issue...")
            
            # Check current enum values
            print("\n1. Checking current enum values...")
            result = db.session.execute(text("""
                SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
                ORDER BY enum_value
            """))
            current_values = [row[0] for row in result.fetchall()]
            print(f"Current enum values: {current_values}")
            
            # The issue: Database has lowercase, but app sends uppercase
            print("\n2. Problem identified:")
            print("   - Database enum: lowercase values (e.g., 'interventional_radiology')")
            print("   - Application sends: uppercase values (e.g., 'INTERVENTIONAL_RADIOLOGY')")
            print("   - This causes the 'invalid input value for enum' error")
            
            print("\n3. Solution: Update database enum to use uppercase values")
            
            # Create a new enum type with uppercase values
            print("\n4. Creating new enum type with uppercase values...")
            
            # First, create the new enum type
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
            
            # Update the opportunity table to use the new enum
            print("\n5. Updating opportunity table...")
            db.session.execute(text("""
                ALTER TABLE opportunity 
                ALTER COLUMN opportunity_type TYPE opportunitytype_new 
                USING opportunity_type::text::opportunitytype_new
            """))
            print("   ✅ Opportunity table updated")
            
            # Drop the old enum type and rename the new one
            print("\n6. Replacing old enum type...")
            db.session.execute(text("DROP TYPE opportunitytype"))
            db.session.execute(text("ALTER TYPE opportunitytype_new RENAME TO opportunitytype"))
            print("   ✅ Old enum type replaced")
            
            # Verify the fix
            print("\n7. Verifying the fix...")
            result = db.session.execute(text("""
                SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
                ORDER BY enum_value
            """))
            new_values = [row[0] for row in result.fetchall()]
            print(f"New enum values: {new_values}")
            
            if 'INTERVENTIONAL_RADIOLOGY' in new_values:
                print("   ✅ INTERVENTIONAL_RADIOLOGY found in enum")
            else:
                print("   ❌ INTERVENTIONAL_RADIOLOGY not found in enum")
                return False
            
            db.session.commit()
            print("\n🎉 Enum case mismatch fixed!")
            print("The database now uses uppercase enum values that match what the application sends.")
            return True
            
        except Exception as e:
            print(f"❌ Fix failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("Fixing enum case mismatch issue...")
    success = fix_enum_case_issue()
    if success:
        print("🎉 Fix completed successfully!")
        print("Try creating an interventional radiology opportunity now!")
    else:
        print("💥 Fix failed!")
        sys.exit(1)
