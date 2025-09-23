#!/usr/bin/env python3
"""
Script to push ultra-thin breadcrumb navigation and radiology knowledge base updates to GitHub
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(f"Command: {command}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Pushing ultra-thin breadcrumb navigation and radiology updates to GitHub...")
    print("=" * 70)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("📁 Initializing git repository...")
        if not run_command("git init", "Git initialization"):
            return False
    
    # Add all changes
    if not run_command("git add .", "Adding files to staging"):
        return False
    
    # Check if there are changes to commit
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("ℹ️  No changes to commit")
        return True
    
    # Commit changes
    commit_message = """feat: Make breadcrumb navigation ultra-thin and update knowledge base to radiology-specific

Breadcrumb Navigation Improvements:
- Reduced padding from 0.375rem to 0.125rem (67% smaller)
- Decreased font size from 0.75rem to 0.6875rem
- Tightened gaps from 0.25rem to 0.125rem (50% smaller)
- Reduced icon size from 10px to 8px
- Set line height to 1.2 for minimal vertical space
- Ultra-minimal padding (0.0625rem 0.125rem)
- Now just thick enough to accommodate text content

Radiology Knowledge Base Updates:
- Changed title from Medical Knowledge Base to Radiology Knowledge Base
- Updated description to organized by radiology subspecialty
- Maintains consistency with radiology-focused platform

This creates an ultra-thin breadcrumb navigation that takes up minimal
vertical space while remaining fully functional and accessible."""
    
    # Use single quotes to avoid shell escaping issues
    if not run_command(f"git commit -m '{commit_message}'", "Committing changes"):
        return False
    
    # Check if remote exists
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("⚠️  No remote repository configured.")
        print("Please add your GitHub remote with:")
        print("git remote add origin https://github.com/yourusername/your-repo.git")
        return False
    
    # Push to GitHub
    if not run_command("git push origin main", "Pushing to GitHub"):
        # Try master branch if main fails
        print("🔄 Trying master branch...")
        if not run_command("git push origin master", "Pushing to GitHub (master branch)"):
            return False
    
    print("=" * 70)
    print("🎉 Successfully pushed ultra-thin breadcrumb and radiology updates to GitHub!")
    print("📝 Changes include:")
    print("   • Ultra-thin breadcrumb navigation (67% smaller)")
    print("   • Minimal vertical space usage")
    print("   • Radiology-specific knowledge base tile")
    print("   • Improved page real estate for content")
    print("   • Better user experience with less visual clutter")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
