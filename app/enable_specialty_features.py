"""
Auto-enable specialty features when database columns are available
This module dynamically enables/disables features based on database schema
"""

import logging
from .auto_migrate import check_column_exists

logger = logging.getLogger(__name__)

def should_enable_forum_specialty():
    """Check if forum specialty features should be enabled"""
    return check_column_exists('forum_post', 'specialty')

def should_enable_resident_specialty():
    """Check if resident profile specialty features should be enabled"""
    return check_column_exists('resident_profile', 'medical_specialty')

def get_forum_query_with_specialty_support():
    """
    Return appropriate forum query based on whether specialty column exists
    This allows the forum to work regardless of migration status
    """
    from .models import ForumPost, ForumCategory
    
    if should_enable_forum_specialty():
        # Full query with specialty support
        return ForumPost.query
    else:
        # Limited query without specialty column
        from .models import db
        return db.session.query(
            ForumPost.id,
            ForumPost.author_id,
            ForumPost.title, 
            ForumPost.content,
            ForumPost.category,
            ForumPost.created_at,
            ForumPost.updated_at,
            ForumPost.is_pinned,
            ForumPost.is_locked,
            ForumPost.photos
        )

def log_feature_status():
    """Log which specialty features are currently enabled"""
    features = {
        'Forum Specialty Filtering': should_enable_forum_specialty(),
        'Resident Profile Specialty': should_enable_resident_specialty(),
    }
    
    enabled_features = [name for name, enabled in features.items() if enabled]
    disabled_features = [name for name, enabled in features.items() if not enabled]
    
    if enabled_features:
        logger.info(f"✅ Enabled specialty features: {', '.join(enabled_features)}")
    
    if disabled_features:
        logger.warning(f"⚠️  Disabled specialty features (awaiting migration): {', '.join(disabled_features)}")
    
    return features
