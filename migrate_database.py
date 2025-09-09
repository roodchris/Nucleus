#!/usr/bin/env python3
"""
Database migration script to add missing columns
Run this script to update the database schema
"""
import os
import sys
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def migrate_database():
    """Add missing columns to the database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get database URL to determine database type
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"Database URL: {db_url}")
            
            # Check if timezone column exists in user table
            if 'postgresql' in db_url.lower():
                # PostgreSQL
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user' AND column_name = 'timezone'
                """))
                timezone_exists = result.fetchone() is not None
                
                if not timezone_exists:
                    print("Adding timezone column to user table...")
                    db.session.execute(text("""
                        ALTER TABLE "user" 
                        ADD COLUMN timezone VARCHAR(50)
                    """))
                    print("✅ timezone column added successfully")
                else:
                    print("✅ timezone column already exists")
                    
            elif 'sqlite' in db_url.lower():
                # SQLite
                result = db.session.execute(text("""
                    PRAGMA table_info(user)
                """))
                columns = [row[1] for row in result.fetchall()]
                timezone_exists = 'timezone' in columns
                
                if not timezone_exists:
                    print("Adding timezone column to user table...")
                    db.session.execute(text("""
                        ALTER TABLE user 
                        ADD COLUMN timezone VARCHAR(50)
                    """))
                    print("✅ timezone column added successfully")
                else:
                    print("✅ timezone column already exists")
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
    print("Starting database migration...")
    success = migrate_database()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
