#!/usr/bin/env python3
"""
Test database connection for deployment debugging
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_url():
    """Test if DATABASE_URL is properly configured"""
    database_url = os.getenv("DATABASE_URL")
    
    print("=== Database Configuration Test ===")
    print(f"DATABASE_URL: {database_url}")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set!")
        print("Please set DATABASE_URL in your Render environment variables.")
        return False
    
    if database_url.startswith("postgres://"):
        print("⚠️  WARNING: postgres:// URL detected, converting to postgresql://")
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        print(f"Converted URL: {database_url}")
    
    if database_url.startswith("postgresql://"):
        print("✅ PostgreSQL URL format detected")
    elif database_url.startswith("sqlite://"):
        print("✅ SQLite URL format detected")
    else:
        print(f"❌ ERROR: Unknown database URL format: {database_url}")
        return False
    
    # Test SQLAlchemy parsing
    try:
        from sqlalchemy import create_engine
        engine = create_engine(database_url)
        print("✅ SQLAlchemy can parse the database URL")
        return True
    except Exception as e:
        print(f"❌ ERROR: SQLAlchemy cannot parse the URL: {e}")
        return False

if __name__ == "__main__":
    test_database_url()
