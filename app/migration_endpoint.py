"""
Emergency migration endpoint for fixing the interventional enum issue.
This provides a manual way to trigger the enum migration.
"""

from flask import Blueprint, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import text
from app.models import db

migration_bp = Blueprint('migration', __name__)

def admin_required(f):
    """Decorator to require admin access (radnucleus@gmail.com)"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.email != 'radnucleus@gmail.com':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@migration_bp.route('/admin/fix-interventional-enum', methods=['POST'])
@login_required
@admin_required
def fix_interventional_enum():
    """Emergency endpoint to manually fix the interventional enum issue."""
    
    current_app.logger.info("🚨 EMERGENCY: Manual interventional enum fix triggered!")
    
    try:
        # Check current enum values
        result = db.session.execute(text("""
            SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
        """))
        existing_values = [row[0] for row in result.fetchall()]
        current_app.logger.info(f"📋 Current enum values: {existing_values}")
        
        if 'interventional' in existing_values:
            return jsonify({
                'success': True, 
                'message': 'interventional enum value already exists',
                'existing_values': existing_values
            })
        
        current_app.logger.warning("🚨 CRITICAL: 'interventional' enum value MISSING!")
        
        # Method 1: Standard ADD VALUE
        try:
            current_app.logger.info("🔧 Method 1: Standard ALTER TYPE ADD VALUE...")
            db.session.execute(text("""
                ALTER TYPE opportunitytype 
                ADD VALUE 'interventional'
            """))
            db.session.commit()
            current_app.logger.info("✅ SUCCESS: Method 1 worked!")
            
        except Exception as method1_error:
            current_app.logger.error(f"❌ Method 1 FAILED: {method1_error}")
            db.session.rollback()
            
            # Method 2: Try with IF NOT EXISTS
            try:
                current_app.logger.info("🔧 Method 2: DO $$ BEGIN IF NOT EXISTS...")
                db.session.execute(text("""
                    DO $$ BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_enum 
                            WHERE enumlabel = 'interventional' 
                            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'opportunitytype')
                        ) THEN
                            ALTER TYPE opportunitytype ADD VALUE 'interventional';
                            RAISE NOTICE 'Added interventional enum value';
                        ELSE
                            RAISE NOTICE 'interventional enum value already exists';
                        END IF;
                    END $$;
                """))
                db.session.commit()
                current_app.logger.info("✅ SUCCESS: Method 2 worked!")
                
            except Exception as method2_error:
                current_app.logger.error(f"❌ Method 2 FAILED: {method2_error}")
                db.session.rollback()
                
                # Method 3: Direct insertion into pg_enum
                try:
                    current_app.logger.info("🔧 Method 3: Direct pg_enum insertion...")
                    db.session.execute(text("""
                        INSERT INTO pg_enum (enumtypid, enumlabel, enumsortorder)
                        SELECT 
                            (SELECT oid FROM pg_type WHERE typname = 'opportunitytype'),
                            'interventional',
                            COALESCE(MAX(enumsortorder), 0) + 1
                        FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'opportunitytype')
                    """))
                    db.session.commit()
                    current_app.logger.info("✅ SUCCESS: Method 3 worked!")
                    
                except Exception as method3_error:
                    current_app.logger.error(f"❌ Method 3 FAILED: {method3_error}")
                    db.session.rollback()
                    return jsonify({
                        'success': False,
                        'error': f'All three methods failed. Method 3 error: {method3_error}',
                        'existing_values': existing_values
                    }), 500
        
        # Verify the enum value was added
        result = db.session.execute(text("""
            SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
        """))
        final_values = [row[0] for row in result.fetchall()]
        current_app.logger.info(f"📋 Final enum values: {final_values}")
        
        if 'interventional' in final_values:
            current_app.logger.info("🎉 SUCCESS: interventional enum value added!")
            return jsonify({
                'success': True,
                'message': 'interventional enum value successfully added',
                'final_values': final_values
            })
        else:
            current_app.logger.error("❌ FAILURE: interventional enum value still missing!")
            return jsonify({
                'success': False,
                'error': 'interventional enum value still missing after migration',
                'final_values': final_values
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"🚨 CRITICAL ERROR: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@migration_bp.route('/admin/check-enum-values', methods=['GET'])
@login_required
@admin_required
def check_enum_values():
    """Check current enum values in the database."""
    
    try:
        result = db.session.execute(text("""
            SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
        """))
        enum_values = [row[0] for row in result.fetchall()]
        
        return jsonify({
            'success': True,
            'enum_values': enum_values,
            'has_interventional': 'interventional' in enum_values
        })
        
    except Exception as e:
        current_app.logger.error(f"Error checking enum values: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
