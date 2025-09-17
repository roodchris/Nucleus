#!/usr/bin/env python3
"""
Production database migration script for PostgreSQL
This script applies all the changes we made:
1. Add specialty column to job_review table
2. Add medical_specialty column to resident_profile table
3. Update employer_profile table (replace modalities with medical_specialty)
4. Update practice type values from 'Teleradiology' to 'Telemedicine'
"""

import sys
import os
import traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, JobReview, ResidentProfile, EmployerProfile, CompensationData

def run_production_migration():
    """Run all database migrations for production PostgreSQL database"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 Starting production database migration...")
            print(f"Database URL: {app.config.get('DATABASE_URL', 'Not set')}")
            
            # Check database connection
            inspector = db.inspect(db.engine)
            print("✅ Database connection successful")
            
            # Migration 1: Add specialty column to job_review table
            print("\n📋 Migration 1: JobReview table")
            job_review_columns = [col['name'] for col in inspector.get_columns('job_review')]
            if 'specialty' not in job_review_columns:
                print("  Adding specialty column to job_review...")
                with db.engine.connect() as connection:
                    connection.execute(db.text("ALTER TABLE job_review ADD COLUMN specialty VARCHAR(100)"))
                    connection.commit()
                print("  ✅ Added specialty column to job_review")
            else:
                print("  ✅ specialty column already exists in job_review")
            
            # Migration 2: Add medical_specialty column to resident_profile table
            print("\n👤 Migration 2: ResidentProfile table")
            resident_profile_columns = [col['name'] for col in inspector.get_columns('resident_profile')]
            if 'medical_specialty' not in resident_profile_columns:
                print("  Adding medical_specialty column to resident_profile...")
                with db.engine.connect() as connection:
                    connection.execute(db.text("ALTER TABLE resident_profile ADD COLUMN medical_specialty VARCHAR(100)"))
                    connection.commit()
                print("  ✅ Added medical_specialty column to resident_profile")
            else:
                print("  ✅ medical_specialty column already exists in resident_profile")
            
            # Migration 3: Update employer_profile table
            print("\n🏥 Migration 3: EmployerProfile table")
            employer_profile_columns = [col['name'] for col in inspector.get_columns('employer_profile')]
            
            if 'medical_specialty' not in employer_profile_columns:
                print("  Adding medical_specialty column to employer_profile...")
                with db.engine.connect() as connection:
                    connection.execute(db.text("ALTER TABLE employer_profile ADD COLUMN medical_specialty VARCHAR(100)"))
                    connection.commit()
                print("  ✅ Added medical_specialty column to employer_profile")
            else:
                print("  ✅ medical_specialty column already exists in employer_profile")
            
            if 'modalities' in employer_profile_columns:
                print("  Removing modalities column from employer_profile...")
                with db.engine.connect() as connection:
                    connection.execute(db.text("ALTER TABLE employer_profile DROP COLUMN IF EXISTS modalities"))
                    connection.commit()
                print("  ✅ Removed modalities column from employer_profile")
            else:
                print("  ✅ modalities column already removed from employer_profile")
            
            # Migration 4: Update practice type values
            print("\n🔄 Migration 4: Update practice type values")
            
            # Update JobReview records
            job_reviews_updated = db.session.query(JobReview).filter(
                JobReview.practice_type == 'Teleradiology'
            ).update(
                {JobReview.practice_type: 'Telemedicine'}, 
                synchronize_session=False
            )
            
            # Update EmployerProfile records
            employer_profiles_updated = db.session.query(EmployerProfile).filter(
                EmployerProfile.practice_setting == 'Teleradiology'
            ).update(
                {EmployerProfile.practice_setting: 'Telemedicine'}, 
                synchronize_session=False
            )
            
            # Update CompensationData records
            compensation_data_updated = db.session.query(CompensationData).filter(
                CompensationData.practice_type == 'Teleradiology'
            ).update(
                {CompensationData.practice_type: 'Telemedicine'}, 
                synchronize_session=False
            )
            
            db.session.commit()
            
            print(f"  ✅ Updated {job_reviews_updated} JobReview records")
            print(f"  ✅ Updated {employer_profiles_updated} EmployerProfile records")
            print(f"  ✅ Updated {compensation_data_updated} CompensationData records")
            
            print("\n🎉 All migrations completed successfully!")
            print("\n📊 Final table structures:")
            
            # Show final table structures
            for table_name in ['job_review', 'resident_profile', 'employer_profile']:
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                print(f"  {table_name}: {columns}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Migration failed: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = run_production_migration()
    if success:
        print("\n✅ Production migration completed successfully!")
        print("Your PostgreSQL database is now ready for the updated application.")
    else:
        print("\n❌ Production migration failed!")
        print("Please check the error messages above and fix any issues before deploying.")
    
    sys.exit(0 if success else 1)
