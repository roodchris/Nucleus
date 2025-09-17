#!/usr/bin/env python3
"""
Fix PostgreSQL enum to add interventional_radiology value
This script handles the PostgreSQL enum update properly
"""
import os
import sys
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def fix_postgresql_enum():
    """Fix PostgreSQL enum to include interventional_radiology"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get database URL to determine database type
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"Database URL: {db_url}")
            
            if 'postgresql' not in db_url.lower():
                print("❌ This script is for PostgreSQL databases only")
                print("For SQLite, the enum values are not enforced, so no migration is needed")
                return False
            
            print("PostgreSQL detected - fixing enum...")
            
            # First, check current enum values
            print("\n1. Checking current enum values...")
            result = db.session.execute(text("""
                SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
                ORDER BY enum_value
            """))
            current_values = [row[0] for row in result.fetchall()]
            print(f"Current enum values: {current_values}")
            
            # Check if interventional_radiology already exists
            if 'interventional_radiology' in current_values:
                print("✅ interventional_radiology already exists in enum")
                return True
            
            # Add the new enum value
            print("\n2. Adding interventional_radiology to enum...")
            try:
                db.session.execute(text("""
                    ALTER TYPE opportunitytype 
                    ADD VALUE 'interventional_radiology' BEFORE 'consulting_other'
                """))
                print("✅ Successfully added interventional_radiology to enum")
            except Exception as e:
                if 'already exists' in str(e).lower():
                    print("✅ interventional_radiology already exists in enum")
                else:
                    print(f"❌ Error adding enum value: {e}")
                    return False
            
            # Verify the addition
            print("\n3. Verifying enum values...")
            result = db.session.execute(text("""
                SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
                ORDER BY enum_value
            """))
            new_values = [row[0] for row in result.fetchall()]
            print(f"Updated enum values: {new_values}")
            
            if 'interventional_radiology' in new_values:
                print("✅ interventional_radiology successfully added to enum")
            else:
                print("❌ interventional_radiology not found in enum after addition")
                return False
            
            db.session.commit()
            print("\n🎉 PostgreSQL enum migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("Starting PostgreSQL enum fix...")
    success = fix_postgresql_enum()
    if success:
        print("🎉 Migration completed successfully!")
        print("The interventional radiology job type is now available in PostgreSQL.")
    else:
        print("💥 Migration failed!")
        sys.exit(1)

