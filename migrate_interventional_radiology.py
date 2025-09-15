#!/usr/bin/env python3
"""
Database migration script to add interventional radiology job type
Run this script to update the database schema with the new opportunity type
"""
import os
import sys
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def migrate_interventional_radiology():
    """Add interventional radiology opportunity type to the database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get database URL to determine database type
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"Database URL: {db_url}")
            
            if 'postgresql' in db_url.lower():
                # PostgreSQL - Add the new enum value
                print("Adding interventional_radiology to opportunity_type enum...")
                
                # First, check if the enum value already exists
                result = db.session.execute(text("""
                    SELECT 1 FROM pg_enum 
                    WHERE enumlabel = 'interventional_radiology' 
                    AND enumtypid = (
                        SELECT oid FROM pg_type WHERE typname = 'opportunitytype'
                    )
                """))
                
                if result.fetchone() is None:
                    # Add the new enum value
                    db.session.execute(text("""
                        ALTER TYPE opportunitytype 
                        ADD VALUE 'interventional_radiology' BEFORE 'consulting_other'
                    """))
                    print("✅ interventional_radiology added to opportunity_type enum")
                else:
                    print("✅ interventional_radiology already exists in opportunity_type enum")
                    
            elif 'sqlite' in db_url.lower():
                # SQLite - For SQLite, we need to recreate the table with the new enum
                print("SQLite detected - recreating opportunity table with new enum...")
                
                # Check if the column exists and what type it is
                result = db.session.execute(text("PRAGMA table_info(opportunity)"))
                columns = {row[1]: row[2] for row in result.fetchall()}
                
                if 'opportunity_type' in columns:
                    print("✅ opportunity_type column exists in SQLite")
                    print("Note: SQLite doesn't enforce enum constraints, so the new value will work automatically")
                else:
                    print("❌ opportunity_type column not found")
                    return False
            else:
                print("❌ Unsupported database type")
                return False
            
            db.session.commit()
            print("✅ Database migration completed successfully")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("Starting interventional radiology migration...")
    success = migrate_interventional_radiology()
    if success:
        print("🎉 Migration completed successfully!")
        print("The interventional radiology job type is now available in the application.")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
