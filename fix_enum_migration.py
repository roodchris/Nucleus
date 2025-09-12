#!/usr/bin/env python3
"""
Fix PostgreSQL enum migration for interventional_radiology
Run this script to add the missing enum value to the production database
"""
import os
import sys
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def fix_enum_migration():
    """Add interventional_radiology to the opportunitytype enum"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get database URL to determine database type
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"Database URL: {db_url}")
            
            if 'postgresql' in db_url.lower():
                print("✅ Using PostgreSQL database")
                
                # Check if the enum value already exists
                result = db.session.execute(text("""
                    SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
                """))
                enum_values = [row[0] for row in result.fetchall()]
                print(f"Current enum values: {enum_values}")
                
                if 'interventional_radiology' in enum_values:
                    print("✅ interventional_radiology enum value already exists")
                    return True
                
                # Add the new enum value
                print("Adding interventional_radiology to opportunitytype enum...")
                db.session.execute(text("""
                    ALTER TYPE opportunitytype 
                    ADD VALUE 'interventional_radiology'
                """))
                db.session.commit()
                print("✅ interventional_radiology enum value added successfully")
                
                # Verify the addition
                result = db.session.execute(text("""
                    SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
                """))
                enum_values = [row[0] for row in result.fetchall()]
                print(f"Updated enum values: {enum_values}")
                
                if 'interventional_radiology' in enum_values:
                    print("✅ Verification successful - interventional_radiology is now available")
                    return True
                else:
                    print("❌ Verification failed - interventional_radiology not found after addition")
                    return False
                    
            elif 'sqlite' in db_url.lower():
                print("✅ Using SQLite database - no enum migration needed")
                return True
            else:
                print("❌ Unsupported database type")
                return False
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("🔧 Starting enum migration fix...")
    success = fix_enum_migration()
    if success:
        print("🎉 Migration completed successfully!")
        print("You can now create Interventional Radiology opportunities!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
