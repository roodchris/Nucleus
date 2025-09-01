#!/usr/bin/env python3
"""
Minimal test to check basic imports
"""

print("Testing basic imports...")

try:
    import flask
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")

try:
    import flask_sqlalchemy
    print("✅ Flask-SQLAlchemy imported successfully")
except ImportError as e:
    print(f"❌ Flask-SQLAlchemy import failed: {e}")

try:
    import flask_login
    print("✅ Flask-Login imported successfully")
except ImportError as e:
    print(f"❌ Flask-Login import failed: {e}")

try:
    import gunicorn
    print("✅ Gunicorn imported successfully")
except ImportError as e:
    print(f"❌ Gunicorn import failed: {e}")

print("\nTesting app creation...")
try:
    from app import create_app
    app = create_app()
    print("✅ App created successfully")
except Exception as e:
    print(f"❌ App creation failed: {e}")
    import traceback
    traceback.print_exc()
