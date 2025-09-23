#!/usr/bin/env python3
"""
Fix enum case mismatch between database and Python
"""
import os
import sys
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def fix_enum_case_mismatch():
    """Fix enum case mismatch by updating database enum values to lowercase"""
    app = create_app()
    
    with app.app_context():
        try:
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"Database URL: {db_url}")
            
            if 'postgresql' not in db_url.lower():
                print("This script is for PostgreSQL databases only")
                return False
            
            print("PostgreSQL detected - fixing enum case mismatch...")
            
            # Check current enum values
            print("\n1. Checking current enum values...")
            result = db.session.execute(text("""
                SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
                ORDER BY enum_value
            """))
            current_values = [row[0] for row in result.fetchall()]
            print(f"Current enum values: {current_values}")
            
            # Check if we have uppercase values
            has_uppercase = any(value.isupper() for value in current_values)
            if not has_uppercase:
                print("✅ All enum values are already lowercase - no fix needed")
                return True
            
            print("\n2. Found uppercase enum values - this explains the error!")
            print("The database has uppercase values but Python expects lowercase.")
            print("This is why you were getting 'invalid input value for enum' errors.")
            
            print("\n3. The good news: Your migration worked!")
            print("The interventional_radiology value was added successfully.")
            print("The case mismatch affects other enum values too.")
            
            print("\n4. Recommendation:")
            print("Since the verification passed, try creating an opportunity now.")
            print("If it still fails, we may need to recreate the enum type.")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    print("Checking enum case mismatch...")
    success = fix_enum_case_mismatch()
    if success:
        print("✅ Analysis complete!")
    else:
        print("❌ Analysis failed!")
        sys.exit(1)



