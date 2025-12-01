#!/usr/bin/env python3
"""
Database migration script to change pay_amount column from Float to String
This allows free text entry in the pay amount field
Run this script to update the database schema
"""
import os
import sys
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def migrate_pay_amount():
    """Change pay_amount column from Float to String"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get database URL to determine database type
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"Database URL: {db_url[:50]}...")  # Don't print full URL for security
            
            # Create migrations table if it doesn't exist
            try:
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        id SERIAL PRIMARY KEY,
                        migration_name VARCHAR(255) UNIQUE NOT NULL,
                        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.session.commit()
            except:
                # For SQLite, use different syntax
                try:
                    db.session.execute(text("""
                        CREATE TABLE IF NOT EXISTS migrations (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            migration_name VARCHAR(255) UNIQUE NOT NULL,
                            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    db.session.commit()
                except:
                    pass  # Table might already exist
            
            # Check if migration has already been completed
            result = db.session.execute(text("""
                SELECT migration_name FROM migrations 
                WHERE migration_name = 'change_pay_amount_to_string'
            """))
            migration_exists = result.fetchone() is not None
            
            if migration_exists:
                print("✅ Migration 'change_pay_amount_to_string' has already been completed")
                return True
            
            if 'postgresql' in db_url.lower():
                # PostgreSQL - check current column type
                print("Checking pay_amount column type (PostgreSQL)...")
                result = db.session.execute(text("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'opportunity' AND column_name = 'pay_amount'
                """))
                column_info = result.fetchone()
                
                if column_info and column_info[0] in ('double precision', 'real', 'numeric', 'float'):
                    print(f"Current type: {column_info[0]}")
                    print("Converting pay_amount column from Float to String...")
                    # Convert float to string, handling NULL values
                    db.session.execute(text("""
                        ALTER TABLE opportunity 
                        ALTER COLUMN pay_amount TYPE VARCHAR(255) 
                        USING CASE 
                            WHEN pay_amount IS NULL THEN NULL 
                            ELSE pay_amount::text 
                        END
                    """))
                    db.session.commit()
                    print("✅ pay_amount column converted to String successfully!")
                elif column_info and column_info[0] in ('character varying', 'varchar', 'text'):
                    print(f"✅ pay_amount column is already String type ({column_info[0]})")
                else:
                    print(f"⚠️ pay_amount column type is {column_info[0] if column_info else 'unknown'}, skipping migration")
                    return False
                    
            elif 'sqlite' in db_url.lower():
                # SQLite - check if column exists
                print("Checking pay_amount column (SQLite)...")
                result = db.session.execute(text("""
                    PRAGMA table_info(opportunity)
                """))
                columns = result.fetchall()
                pay_amount_info = next((col for col in columns if col[1] == 'pay_amount'), None)
                
                if pay_amount_info:
                    print("ℹ️ SQLite detected - pay_amount will be stored as text (SQLite is type-flexible)")
                    print("   Note: SQLite doesn't support ALTER COLUMN TYPE, but the column will work as string")
                else:
                    print("ℹ️ pay_amount column doesn't exist yet, will be created as String")
                    
            elif 'mysql' in db_url.lower() or 'mariadb' in db_url.lower():
                # MySQL/MariaDB
                print("Converting pay_amount column from Float to String (MySQL)...")
                try:
                    db.session.execute(text("""
                        ALTER TABLE opportunity 
                        MODIFY COLUMN pay_amount VARCHAR(255)
                    """))
                    db.session.commit()
                    print("✅ pay_amount column converted to String successfully!")
                except Exception as e:
                    print(f"❌ Could not update pay_amount column: {e}")
                    db.session.rollback()
                    return False
            else:
                print("⚠️ Unsupported database type - migration may not work correctly")
                return False
            
            # Record migration as completed
            db.session.execute(text("""
                INSERT INTO migrations (migration_name) 
                VALUES ('change_pay_amount_to_string')
                ON CONFLICT (migration_name) DO NOTHING
            """))
            db.session.commit()
            print("✅ Migration recorded successfully")
            print("🎉 Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("Starting pay_amount to String migration...")
    print("=" * 60)
    success = migrate_pay_amount()
    print("=" * 60)
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)

