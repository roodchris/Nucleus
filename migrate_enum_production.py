#!/usr/bin/env python3
"""
Production database migration script to add NON_CLINICAL_OTHER to the OpportunityType enum
This script can be run against production PostgreSQL databases
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def migrate_enum_production():
    """Add NON_CLINICAL_OTHER to the OpportunityType enum in production"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to your PostgreSQL connection string")
        print("Example: DATABASE_URL=postgresql://user:password@host:port/database")
        return False
    
    # Ensure it's PostgreSQL
    if not database_url.startswith('postgresql'):
        print("❌ Error: This script is for PostgreSQL databases only")
        print(f"Current URL scheme: {database_url.split('://')[0]}")
        return False
    
    try:
        print(f"🔗 Connecting to database...")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                print("🔄 Checking if NON_CLINICAL_OTHER already exists...")
                
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
                
                print("🔄 Adding NON_CLINICAL_OTHER to OpportunityType enum...")
                
                # Add the new enum value at the beginning (position 0)
                add_enum_query = text("""
                    ALTER TYPE opportunitytype ADD VALUE 'NON_CLINICAL_OTHER' BEFORE 'AEROSPACE_MEDICINE'
                """)
                
                conn.execute(add_enum_query)
                
                # Commit the transaction
                trans.commit()
                
                print("✅ Successfully added NON_CLINICAL_OTHER to OpportunityType enum")
                
                # Verify the addition
                verify_query = text("""
                    SELECT enumlabel FROM pg_enum 
                    WHERE enumtypid = (
                        SELECT oid FROM pg_type WHERE typname = 'opportunitytype'
                    )
                    ORDER BY enumsortorder
                """)
                
                enum_values = conn.execute(verify_query).fetchall()
                print("📋 Current enum values:")
                for i, (value,) in enumerate(enum_values):
                    marker = "🆕" if value == 'NON_CLINICAL_OTHER' else "  "
                    print(f"  {marker} {i+1}. {value}")
                
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
    print("🚀 Starting production database migration to add NON_CLINICAL_OTHER enum value...")
    print("⚠️  This will modify the PostgreSQL database schema")
    
    # Ask for confirmation in production
    if os.environ.get('ENVIRONMENT') == 'production':
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Migration cancelled by user")
            return 1
    
    success = migrate_enum_production()
    
    if success:
        print("🎉 Migration completed successfully!")
        print("💡 You can now use NON_CLINICAL_OTHER in your application")
        return 0
    else:
        print("💥 Migration failed!")
        print("💡 You can also run the SQL script manually:")
        print("   psql -d your_database -f add_non_clinical_other_enum.sql")
        return 1

if __name__ == "__main__":
    sys.exit(main())
