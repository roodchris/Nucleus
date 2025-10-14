#!/usr/bin/env python3
"""
Database migration script to add NON_CLINICAL_OTHER to the OpportunityType enum
This script adds the new enum value to the PostgreSQL database
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def add_enum_value():
    """Add NON_CLINICAL_OTHER to the OpportunityType enum"""
    
    # Import config to get database URL
    try:
        from config import Config
        database_url = Config.SQLALCHEMY_DATABASE_URI
    except ImportError:
        # Fallback to environment variables
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            database_url = os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    if not database_url:
        print("❌ Error: No database URL found in environment variables or config")
        print("Please set DATABASE_URL or SQLALCHEMY_DATABASE_URI")
        return False
    
    # Skip if using SQLite (no enum support needed)
    if database_url.startswith('sqlite'):
        print("ℹ️  SQLite detected - no enum migration needed")
        return True
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                print("🔄 Adding NON_CLINICAL_OTHER to OpportunityType enum...")
                
                # Check if the enum value already exists
                check_query = text("""
                    SELECT 1 FROM pg_enum 
                    WHERE enumlabel = 'NON_CLINICAL_OTHER' 
                    AND enumtypid = (
                        SELECT oid FROM pg_type WHERE typname = 'opportunitytype'
                    )
                """)
                
                result = conn.execute(check_query).fetchone()
                
                if result:
                    print("✅ NON_CLINICAL_OTHER already exists in OpportunityType enum")
                    trans.rollback()
                    return True
                
                # Add the new enum value at the beginning (position 0)
                add_enum_query = text("""
                    ALTER TYPE opportunitytype ADD VALUE 'NON_CLINICAL_OTHER' BEFORE 'AEROSPACE_MEDICINE'
                """)
                
                conn.execute(add_enum_query)
                
                # Commit the transaction
                trans.commit()
                
                print("✅ Successfully added NON_CLINICAL_OTHER to OpportunityType enum")
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error adding enum value: {e}")
                return False
                
    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting database migration to add NON_CLINICAL_OTHER enum value...")
    
    success = add_enum_value()
    
    if success:
        print("🎉 Migration completed successfully!")
        return 0
    else:
        print("💥 Migration failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
