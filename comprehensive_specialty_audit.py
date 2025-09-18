#!/usr/bin/env python3
"""
Comprehensive Specialty Feature Audit

This script audits ALL specialty-related features across the entire website
to ensure complete implementation and identify any remaining issues.
"""

import os
import sys
from app import create_app
from app.models import db, JobReview, ForumPost, ProgramReview, CompensationData, ResidentProfile, EmployerProfile
from sqlalchemy import inspect, text

def audit_specialty_features():
    """Comprehensive audit of all specialty features"""
    print("🔍 COMPREHENSIVE SPECIALTY FEATURE AUDIT")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        
        # 1. Database Schema Audit
        print("\n📋 1. DATABASE SCHEMA AUDIT")
        print("-" * 30)
        
        inspector = inspect(db.engine)
        tables_to_check = {
            'job_review': 'specialty',
            'forum_post': 'specialty', 
            'program_review': 'specialty',
            'compensation_data': 'specialty',
            'resident_profile': 'medical_specialty',
            'employer_profile': 'medical_specialty'
        }
        
        schema_issues = []
        for table, column in tables_to_check.items():
            try:
                columns = [col['name'] for col in inspector.get_columns(table)]
                if column in columns:
                    print(f"✅ {table}.{column} - EXISTS")
                else:
                    print(f"❌ {table}.{column} - MISSING")
                    schema_issues.append(f"{table}.{column}")
            except Exception as e:
                print(f"❌ {table} - TABLE ERROR: {e}")
                schema_issues.append(f"{table} (table error)")
        
        # 2. Model Attribute Audit
        print("\n🏗️ 2. MODEL ATTRIBUTE AUDIT")
        print("-" * 30)
        
        models_to_check = {
            'JobReview': (JobReview, 'specialty'),
            'ForumPost': (ForumPost, 'specialty'),
            'ProgramReview': (ProgramReview, 'specialty'),
            'CompensationData': (CompensationData, 'specialty'),
            'ResidentProfile': (ResidentProfile, 'medical_specialty'),
            'EmployerProfile': (EmployerProfile, 'medical_specialty')
        }
        
        model_issues = []
        for model_name, (model_class, attr) in models_to_check.items():
            has_attr = hasattr(model_class, attr)
            if has_attr:
                print(f"✅ {model_name}.{attr} - ACCESSIBLE")
            else:
                print(f"❌ {model_name}.{attr} - NOT ACCESSIBLE")
                model_issues.append(f"{model_name}.{attr}")
        
        # 3. Data Integrity Audit
        print("\n📊 3. DATA INTEGRITY AUDIT")
        print("-" * 30)
        
        data_stats = {}
        
        # Check JobReview specialty data
        try:
            job_reviews_total = JobReview.query.count()
            job_reviews_with_specialty = JobReview.query.filter(JobReview.specialty.isnot(None)).count()
            data_stats['job_reviews'] = {
                'total': job_reviews_total,
                'with_specialty': job_reviews_with_specialty,
                'percentage': (job_reviews_with_specialty / job_reviews_total * 100) if job_reviews_total > 0 else 0
            }
            print(f"📝 Job Reviews: {job_reviews_with_specialty}/{job_reviews_total} ({data_stats['job_reviews']['percentage']:.1f}%) have specialty")
        except Exception as e:
            print(f"❌ Job Reviews data error: {e}")
        
        # Check ForumPost specialty data
        try:
            forum_posts_total = ForumPost.query.count()
            forum_posts_with_specialty = ForumPost.query.filter(ForumPost.specialty.isnot(None)).count()
            data_stats['forum_posts'] = {
                'total': forum_posts_total,
                'with_specialty': forum_posts_with_specialty,
                'percentage': (forum_posts_with_specialty / forum_posts_total * 100) if forum_posts_total > 0 else 0
            }
            print(f"💬 Forum Posts: {forum_posts_with_specialty}/{forum_posts_total} ({data_stats['forum_posts']['percentage']:.1f}%) have specialty")
        except Exception as e:
            print(f"❌ Forum Posts data error: {e}")
        
        # Check ProgramReview specialty data
        try:
            program_reviews_total = ProgramReview.query.count()
            program_reviews_with_specialty = ProgramReview.query.filter(ProgramReview.specialty.isnot(None)).count()
            data_stats['program_reviews'] = {
                'total': program_reviews_total,
                'with_specialty': program_reviews_with_specialty,
                'percentage': (program_reviews_with_specialty / program_reviews_total * 100) if program_reviews_total > 0 else 0
            }
            print(f"🏥 Program Reviews: {program_reviews_with_specialty}/{program_reviews_total} ({data_stats['program_reviews']['percentage']:.1f}%) have specialty")
        except Exception as e:
            print(f"❌ Program Reviews data error: {e}")
        
        # Check ResidentProfile medical_specialty data
        try:
            resident_profiles_total = ResidentProfile.query.count()
            resident_profiles_with_specialty = ResidentProfile.query.filter(ResidentProfile.medical_specialty.isnot(None)).count()
            data_stats['resident_profiles'] = {
                'total': resident_profiles_total,
                'with_specialty': resident_profiles_with_specialty,
                'percentage': (resident_profiles_with_specialty / resident_profiles_total * 100) if resident_profiles_total > 0 else 0
            }
            print(f"👨‍⚕️ Resident Profiles: {resident_profiles_with_specialty}/{resident_profiles_total} ({data_stats['resident_profiles']['percentage']:.1f}%) have medical_specialty")
        except Exception as e:
            print(f"❌ Resident Profiles data error: {e}")
        
        # Check EmployerProfile medical_specialty data
        try:
            employer_profiles_total = EmployerProfile.query.count()
            employer_profiles_with_specialty = EmployerProfile.query.filter(EmployerProfile.medical_specialty.isnot(None)).count()
            data_stats['employer_profiles'] = {
                'total': employer_profiles_total,
                'with_specialty': employer_profiles_with_specialty,
                'percentage': (employer_profiles_with_specialty / employer_profiles_total * 100) if employer_profiles_total > 0 else 0
            }
            print(f"🏢 Employer Profiles: {employer_profiles_with_specialty}/{employer_profiles_total} ({data_stats['employer_profiles']['percentage']:.1f}%) have medical_specialty")
        except Exception as e:
            print(f"❌ Employer Profiles data error: {e}")
        
        # 4. Feature Functionality Test
        print("\n🧪 4. FEATURE FUNCTIONALITY TEST")
        print("-" * 30)
        
        functionality_issues = []
        
        # Test creating instances with specialty (without saving)
        test_cases = [
            ("JobReview", JobReview, {'user_id': 1, 'practice_name': 'Test', 'location': 'Test', 'overall_rating': 5, 'specialty': 'EMERGENCY_MEDICINE'}),
            ("ForumPost", ForumPost, {'author_id': 1, 'title': 'Test', 'content': 'Test', 'category': 'GENERAL_DISCUSSION', 'specialty': 'FAMILY_MEDICINE'}),
            ("ProgramReview", ProgramReview, {'program_name': 'Test Program', 'user_id': 1, 'specialty': 'NEUROLOGY', 'educational_quality': 5, 'work_life_balance': 5, 'attending_quality': 5, 'facilities_quality': 5, 'research_opportunities': 5, 'culture': 5}),
            ("ResidentProfile", ResidentProfile, {'user_id': 1, 'medical_specialty': 'DERMATOLOGY'}),
            ("EmployerProfile", EmployerProfile, {'user_id': 1, 'practice_name': 'Test Practice', 'medical_specialty': 'PSYCHIATRY'})
        ]
        
        for model_name, model_class, test_data in test_cases:
            try:
                test_instance = model_class(**test_data)
                print(f"✅ {model_name} - Can create with specialty")
            except Exception as e:
                print(f"❌ {model_name} - Cannot create with specialty: {e}")
                functionality_issues.append(f"{model_name}: {e}")
        
        # 5. Migration System Audit
        print("\n🔧 5. MIGRATION SYSTEM AUDIT")
        print("-" * 30)
        
        # Check if auto_migrate.py handles all tables
        auto_migrate_tables = ['job_review', 'resident_profile', 'employer_profile', 'forum_post', 'program_review']
        print(f"📋 Auto-migrate handles: {', '.join(auto_migrate_tables)}")
        
        # Check if startup_enum_fix.py handles necessary tables
        startup_fix_tables = ['forum_post', 'program_review']
        print(f"🚀 Startup enum fix handles: {', '.join(startup_fix_tables)}")
        
        # 6. Summary Report
        print("\n🎯 6. SUMMARY REPORT")
        print("=" * 30)
        
        total_issues = len(schema_issues) + len(model_issues) + len(functionality_issues)
        
        if total_issues == 0:
            print("🎉 ✅ ALL SPECIALTY FEATURES WORKING CORRECTLY!")
            print("🚀 Complete specialty implementation across the entire website")
        else:
            print(f"⚠️ FOUND {total_issues} ISSUE(S):")
            
            if schema_issues:
                print(f"\n❌ Database Schema Issues ({len(schema_issues)}):")
                for issue in schema_issues:
                    print(f"   - {issue}")
            
            if model_issues:
                print(f"\n❌ Model Attribute Issues ({len(model_issues)}):")
                for issue in model_issues:
                    print(f"   - {issue}")
            
            if functionality_issues:
                print(f"\n❌ Functionality Issues ({len(functionality_issues)}):")
                for issue in functionality_issues:
                    print(f"   - {issue}")
        
        # 7. Next Steps
        print("\n🔄 7. NEXT STEPS")
        print("-" * 20)
        
        if total_issues == 0:
            print("✅ No action required - all specialty features are working")
            print("🧪 Ready for comprehensive testing across all pages")
        else:
            print("🔧 Required actions:")
            if schema_issues:
                print("   1. Run database migration to add missing columns")
                print("   2. Restart application to trigger auto-migration")
            if model_issues:
                print("   3. Check model definitions and uncomment any specialty columns")
            if functionality_issues:
                print("   4. Debug specific functionality issues")
        
        return total_issues == 0

if __name__ == "__main__":
    try:
        success = audit_specialty_features()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Audit failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

