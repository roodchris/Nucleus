#!/usr/bin/env python3
"""
Simple test script to verify the app can start properly
"""

try:
    from app import create_app
    print("✅ Successfully imported create_app")
    
    app = create_app()
    print("✅ Successfully created app")
    
    print("✅ App is ready to run!")
    print("✅ All dependencies are working correctly")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This usually means a missing dependency in requirements.txt")
    
except Exception as e:
    print(f"❌ Error creating app: {e}")
    print("This might be a configuration or code issue")
