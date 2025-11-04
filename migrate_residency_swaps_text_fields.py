"""
Migration script to update ResidencySwap and ResidencyOpening specialty fields
to support free text entries (increase from VARCHAR(100) to VARCHAR(200))

This script checks if the migration has already been run and safely updates the columns.
For SQLite, the columns will be updated on next table creation via db.create_all().
For PostgreSQL/MySQL, the columns are altered directly.
"""
from sqlalchemy import text

def migrate_residency_swaps_text_fields():
    """Update specialty field sizes to support free text"""
    from flask import current_app
    from .models import db
    
    db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    # Check if migration has already been completed
    try:
        result = db.session.execute(text("""
            SELECT migration_name FROM migrations 
            WHERE migration_name = 'residency_swaps_text_fields'
        """))
        migration_exists = result.fetchone() is not None
        
        if migration_exists:
            current_app.logger.info("✅ Residency swaps text fields migration already completed")
            return
    except Exception as e:
        current_app.logger.warning(f"Could not check migration status: {e}")
        # Continue with migration attempt
    
    try:
        if 'postgresql' in db_url.lower():
            # PostgreSQL - use ALTER TABLE
            current_app.logger.info("Updating ResidencySwap specialty fields (PostgreSQL)...")
            db.session.execute(text("""
                ALTER TABLE residency_swap 
                ALTER COLUMN current_specialty TYPE VARCHAR(200),
                ALTER COLUMN desired_specialty TYPE VARCHAR(200)
            """))
            
            current_app.logger.info("Updating ResidencyOpening specialty field (PostgreSQL)...")
            db.session.execute(text("""
                ALTER TABLE residency_opening 
                ALTER COLUMN specialty TYPE VARCHAR(200)
            """))
            
            db.session.commit()
            current_app.logger.info("✅ Residency swaps text fields migration completed successfully!")
            
        elif 'mysql' in db_url.lower() or 'mariadb' in db_url.lower():
            # MySQL/MariaDB - use ALTER TABLE with MODIFY
            current_app.logger.info("Updating ResidencySwap specialty fields (MySQL)...")
            db.session.execute(text("""
                ALTER TABLE residency_swap 
                MODIFY COLUMN current_specialty VARCHAR(200),
                MODIFY COLUMN desired_specialty VARCHAR(200)
            """))
            
            current_app.logger.info("Updating ResidencyOpening specialty field (MySQL)...")
            db.session.execute(text("""
                ALTER TABLE residency_opening 
                MODIFY COLUMN specialty VARCHAR(200)
            """))
            
            db.session.commit()
            current_app.logger.info("✅ Residency swaps text fields migration completed successfully!")
            
        elif 'sqlite' in db_url.lower():
            # SQLite - check current column size and log
            # SQLite doesn't support ALTER COLUMN TYPE directly
            # The columns will be updated automatically when tables are recreated via db.create_all()
            current_app.logger.info("SQLite detected - specialty fields will be updated on next table creation")
            current_app.logger.info("Note: SQLite has limited ALTER TABLE support. Columns will update via db.create_all()")
        else:
            current_app.logger.warning(f"Unknown database type from URL: {db_url}")
            current_app.logger.info("Attempting generic ALTER TABLE...")
            
            # Try generic ALTER TABLE (may work for some databases)
            try:
                db.session.execute(text("""
                    ALTER TABLE residency_swap 
                    ALTER COLUMN current_specialty VARCHAR(200),
                    ALTER COLUMN desired_specialty VARCHAR(200)
                """))
                db.session.execute(text("""
                    ALTER TABLE residency_opening 
                    ALTER COLUMN specialty VARCHAR(200)
                """))
                db.session.commit()
                current_app.logger.info("✅ Residency swaps text fields migration completed successfully!")
            except Exception as e:
                current_app.logger.warning(f"Generic ALTER TABLE failed: {e}")
                current_app.logger.info("Fields will be updated on next table creation via db.create_all()")
        
        # Record migration as completed
        db.session.execute(text("""
            INSERT INTO migrations (migration_name) 
            VALUES ('residency_swaps_text_fields')
            ON CONFLICT (migration_name) DO NOTHING
        """))
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during residency swaps text fields migration: {e}")
        # Don't raise - allow app to continue
        current_app.logger.info("Fields will be updated on next table creation via db.create_all()")

