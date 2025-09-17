#!/usr/bin/env python3
import subprocess
import sys

def run_git_commands():
    """Run git commands to push the enum fix"""
    try:
        print("🚀 Pushing enum fix to GitHub...")
        
        # Add files
        subprocess.run(['git', 'add', '.'], check=True)
        print("✅ Files added to git")
        
        # Commit
        commit_msg = "fix: Add PostgreSQL enum update for all 27 medical specialties\n\n- Updated auto_migrate.py to handle PostgreSQL enum additions\n- Updated production_migration.py with proper enum handling\n- Created immediate SQL fix for enum issues\n- Added comprehensive enum migration logic\n\nFixes: invalid input value for enum opportunitytype errors\nEnsures all 27 specialties work in opportunity creation"
        
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        print("✅ Changes committed")
        
        # Push
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Changes pushed to GitHub")
        
        print("\n🎉 Enum fix successfully deployed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = run_git_commands()
    sys.exit(0 if success else 1)
