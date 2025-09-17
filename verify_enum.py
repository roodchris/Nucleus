#!/usr/bin/env python3
"""
Verify that the PostgreSQL enum has been updated correctly
"""
import os
import sys
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, OpportunityType

def verify_enum():
    """Verify the enum is working correctly"""
    app = create_app()
    
    with app.app_context():
        try:
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"Database URL: {db_url}")
            
            if 'postgresql' not in db_url.lower():
                print("This is not a PostgreSQL database - enum verification not needed")
                return True
            
            # Check enum values in database
            print("\n1. Checking enum values in PostgreSQL...")
            result = db.session.execute(text("""
                SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
                ORDER BY enum_value
            """))
            db_values = [row[0] for row in result.fetchall()]
            print(f"Database enum values: {db_values}")
            
            # Check Python enum values
            print("\n2. Checking Python enum values...")
            python_values = [e.value for e in OpportunityType]
            print(f"Python enum values: {python_values}")
            
            # Check if interventional_radiology exists in both
            if 'interventional_radiology' in db_values:
                print("✅ interventional_radiology found in database enum")
            else:
                print("❌ interventional_radiology NOT found in database enum")
                return False
            
            if 'interventional_radiology' in python_values:
                print("✅ interventional_radiology found in Python enum")
            else:
                print("❌ interventional_radiology NOT found in Python enum")
                return False
            
            # Test enum conversion
            print("\n3. Testing enum conversion...")
            try:
                ir_enum = OpportunityType('interventional_radiology')
                print(f"✅ Successfully created enum: {ir_enum.name} = {ir_enum.value}")
            except Exception as e:
                print(f"❌ Failed to create enum: {e}")
                return False
            
            print("\n🎉 Enum verification passed!")
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

if __name__ == "__main__":
    success = verify_enum()
    if not success:
        sys.exit(1)

