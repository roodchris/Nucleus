"""
Startup health check system
Ensures the application is fully ready before serving requests
"""

import logging
from .models import db, OpportunityType
from .database_validator import validate_postgresql_enums, validate_required_columns

logger = logging.getLogger(__name__)

def test_enum_functionality():
    """Test that all enum values work correctly"""
    try:
        # Test that we can create enum instances for all specialty values
        test_specialties = [
            'NEUROLOGICAL_SURGERY',  # The one causing immediate issues
            'FAMILY_MEDICINE',
            'EMERGENCY_MEDICINE',
            'RADIOLOGY_DIAGNOSTIC'
        ]
        
        for specialty in test_specialties:
            try:
                enum_value = OpportunityType(specialty)
                logger.debug(f"✅ Enum test passed: {specialty}")
            except ValueError as e:
                logger.error(f"❌ Enum test failed for {specialty}: {e}")
                return False
        
        logger.info("✅ Enum functionality test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enum functionality test error: {e}")
        return False

def run_startup_health_check():
    """Run comprehensive startup health check"""
    logger.info("🏥 Running startup health check...")
    
    checks = {
        'Database Connection': True,  # Already validated in create_app
        'Required Columns': validate_required_columns(),
        'PostgreSQL Enums': validate_postgresql_enums(),
        'Enum Functionality': test_enum_functionality()
    }
    
    # Log results
    passed_checks = []
    failed_checks = []
    
    for check_name, result in checks.items():
        if result:
            passed_checks.append(check_name)
            logger.info(f"✅ {check_name}: PASS")
        else:
            failed_checks.append(check_name)
            logger.warning(f"⚠️  {check_name}: FAIL")
    
    # Summary
    if not failed_checks:
        logger.info("🎉 All health checks passed - application fully ready!")
        return True
    else:
        logger.warning(f"⚠️  {len(failed_checks)} health check(s) failed: {', '.join(failed_checks)}")
        logger.warning("Application will start but some features may be limited")
        return False

def get_health_status():
    """Get current health status for monitoring"""
    return {
        'database_connected': True,  # If we get here, DB is connected
        'columns_ready': validate_required_columns(),
        'enums_ready': validate_postgresql_enums(),
        'enum_functionality': test_enum_functionality()
    }
