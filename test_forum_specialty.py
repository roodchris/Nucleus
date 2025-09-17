#!/usr/bin/env python3
"""
Forum Specialty Diagnostic Script

This script tests if the forum specialty functionality is working properly.
Run this after deployment to verify specialty bubbles should appear.
"""

import os
import sys
from app import create_app
from app.models import db, ForumPost

def test_forum_specialty():
    """Test forum specialty functionality"""
    print("🔍 Testing Forum Specialty Functionality")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        # Test 1: Check if ForumPost model has specialty attribute
        has_specialty_attr = hasattr(ForumPost, 'specialty')
        print(f"✅ ForumPost model has specialty attribute: {has_specialty_attr}")
        
        # Test 2: List all model columns
        print("\n📋 ForumPost model columns:")
        for column in ForumPost.__table__.columns:
            marker = "🎯" if column.name == "specialty" else "  "
            print(f"{marker} {column.name}: {column.type}")
        
        # Test 3: Check database table structure
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        db_columns = inspector.get_columns('forum_post')
        db_column_names = [col['name'] for col in db_columns]
        specialty_in_db = 'specialty' in db_column_names
        print(f"\n✅ Database has specialty column: {specialty_in_db}")
        
        # Test 4: Query posts and test specialty access
        posts = ForumPost.query.all()
        print(f"\n📊 Total forum posts: {len(posts)}")
        
        posts_with_specialty = 0
        for post in posts:
            try:
                specialty_value = getattr(post, 'specialty', None)
                if specialty_value:
                    posts_with_specialty += 1
                    print(f"📝 Post {post.id}: \"{post.title[:30]}...\" -> Specialty: {specialty_value}")
            except Exception as e:
                print(f"❌ Error accessing specialty for post {post.id}: {e}")
        
        print(f"\n📈 Posts with specialty data: {posts_with_specialty}")
        
        # Test 5: Test specialty saving (create a test post)
        print("\n🧪 Testing specialty saving...")
        try:
            test_post = ForumPost(
                author_id=1,  # Assuming user ID 1 exists
                title="Specialty Test Post",
                content="Testing specialty functionality",
                category="GENERAL_DISCUSSION",
                specialty="EMERGENCY_MEDICINE"
            )
            
            # Don't actually save it, just test if it can be created
            print("✅ ForumPost with specialty can be created successfully")
            
        except Exception as e:
            print(f"❌ Error creating ForumPost with specialty: {e}")
        
        # Summary
        print("\n🎯 SUMMARY")
        print("=" * 20)
        if has_specialty_attr and specialty_in_db:
            print("✅ Forum specialty functionality is READY")
            print("✅ Specialty bubbles should appear on forum posts")
        else:
            print("❌ Forum specialty functionality has issues:")
            if not has_specialty_attr:
                print("   - ForumPost model missing specialty attribute")
            if not specialty_in_db:
                print("   - Database missing specialty column")
        
        return has_specialty_attr and specialty_in_db

if __name__ == "__main__":
    try:
        success = test_forum_specialty()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
