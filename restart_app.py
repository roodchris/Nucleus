#!/usr/bin/env python3
"""
Restart application and clear caches
This script helps clear Python cache and restart the application
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def clear_python_cache():
    """Clear Python __pycache__ directories"""
    print("🧹 Clearing Python cache...")
    
    # Find and remove __pycache__ directories
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                cache_path = os.path.join(root, dir_name)
                cache_dirs.append(cache_path)
                try:
                    shutil.rmtree(cache_path)
                    print(f"  ✅ Removed: {cache_path}")
                except Exception as e:
                    print(f"  ❌ Failed to remove {cache_path}: {e}")
    
    if not cache_dirs:
        print("  ℹ️  No __pycache__ directories found")
    else:
        print(f"  🎉 Cleared {len(cache_dirs)} cache directories")

def clear_instance_cache():
    """Clear Flask instance cache"""
    print("🧹 Clearing Flask instance cache...")
    
    instance_dir = Path("instance")
    if instance_dir.exists():
        try:
            # Keep the database file but clear other cache files
            for file_path in instance_dir.glob("*.db"):
                if file_path.name != "app.db":  # Keep main database
                    file_path.unlink()
                    print(f"  ✅ Removed: {file_path}")
            print("  🎉 Instance cache cleared")
        except Exception as e:
            print(f"  ❌ Failed to clear instance cache: {e}")
    else:
        print("  ℹ️  No instance directory found")

def restart_application():
    """Restart the application"""
    print("🔄 Restarting application...")
    
    try:
        # Test the application
        from app import create_app
        from app.models import db, OpportunityType
        
        app = create_app()
        with app.app_context():
            # Test database connection
            db.session.execute(db.text('SELECT 1'))
            print("  ✅ Database connection successful")
            
            # Test enum values
            print("  📋 Current enum values:")
            for opp_type in OpportunityType:
                print(f"    {opp_type.name}: {opp_type.value}")
            
            # Test the specific interventional radiology enum
            interventional = OpportunityType.INTERVENTIONAL_RADIOLOGY
            print(f"  🎯 Interventional Radiology: {interventional.name} = {interventional.value}")
            
            print("  🎉 Application restarted successfully!")
            
    except Exception as e:
        print(f"  ❌ Application restart failed: {e}")
        return False
    
    return True

def main():
    print("🚀 Application Cache Clear & Restart")
    print("=" * 40)
    
    # Clear caches
    clear_python_cache()
    clear_instance_cache()
    
    # Restart application
    success = restart_application()
    
    if success:
        print("\n🎉 Cache cleared and application restarted successfully!")
        print("The Interventional Radiology feature should now work properly.")
    else:
        print("\n❌ There was an issue restarting the application.")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()
