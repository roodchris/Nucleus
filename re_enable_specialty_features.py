#!/usr/bin/env python3
"""
Script to re-enable specialty features after production migration
This script uncommets the specialty column in ForumPost model and related functionality
"""

import sys
import os

def re_enable_specialty_features():
    """Re-enable all specialty features after migration is complete"""
    
    files_to_update = [
        {
            'file': 'app/models.py',
            'old': '    # specialty = db.Column(db.String(100), nullable=True, index=True)  # Medical specialty - TEMPORARILY COMMENTED FOR PRODUCTION COMPATIBILITY',
            'new': '    specialty = db.Column(db.String(100), nullable=True, index=True)  # Medical specialty'
        },
        {
            'file': 'app/forum.py', 
            'old': '    # Filter by specialty if specified (temporarily disabled until production migration)\n    # if specialty:\n    #     try:\n    #         query = query.filter(ForumPost.specialty == specialty)\n    #     except Exception:\n    #         # Ignore specialty filtering if column doesn\'t exist yet\n    #         pass',
            'new': '    # Filter by specialty if specified\n    if specialty:\n        query = query.filter(ForumPost.specialty == specialty)'
        },
        {
            'file': 'app/forum.py',
            'old': '                         # current_specialty=specialty,  # Temporarily disabled',
            'new': '                         current_specialty=specialty,'
        },
        {
            'file': 'app/forum.py',
            'old': '        # specialty = request.form.get("specialty", "")  # Temporarily disabled',
            'new': '        specialty = request.form.get("specialty", "")'
        },
        {
            'file': 'app/forum.py',
            'old': '            # specialty=specialty if specialty else None,  # Temporarily disabled',
            'new': '            specialty=specialty if specialty else None,'
        }
    ]
    
    print("🔄 Re-enabling specialty features...")
    
    for update in files_to_update:
        try:
            with open(update['file'], 'r') as f:
                content = f.read()
            
            if update['old'] in content:
                content = content.replace(update['old'], update['new'])
                with open(update['file'], 'w') as f:
                    f.write(content)
                print(f"  ✅ Updated {update['file']}")
            else:
                print(f"  ⚠️  {update['file']} - pattern not found (may already be updated)")
                
        except Exception as e:
            print(f"  ❌ Error updating {update['file']}: {e}")
            return False
    
    print("\n✅ All specialty features re-enabled!")
    print("\nNext steps:")
    print("1. git add .")
    print("2. git commit -m 'feat: Re-enable all specialty features after production migration'")
    print("3. git push origin main")
    
    return True

if __name__ == "__main__":
    success = re_enable_specialty_features()
    sys.exit(0 if success else 1)
