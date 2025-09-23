#!/usr/bin/env python3
"""
Script to push ultra-thin breadcrumb navigation final improvements to GitHub
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
    print("🚀 Pushing ultra-thin breadcrumb navigation final improvements to GitHub...")
    print("=" * 75)
    
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
    commit_message = """feat: Make breadcrumb navigation ultra-thin with minimal padding and larger text

Ultra-Thin Breadcrumb Navigation:
- Reduced padding from 0.125rem to 0.0625rem (50% smaller - now just 1px)
- Decreased link padding to 0.03125rem 0.0625rem (ultra-minimal)
- Set line height to 1.1 for maximum compactness
- Increased font size from 0.6875rem to 0.75rem (better readability)
- Increased separator arrows to 0.65rem (proportionally larger)
- Maintains proper breadcrumb hierarchy (Home › Page › Section)

This creates an ultra-thin breadcrumb navigation that takes up minimal
vertical space while maintaining excellent readability and proper navigation context."""
    
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
    
    print("=" * 75)
    print("🎉 Successfully pushed ultra-thin breadcrumb navigation to GitHub!")
    print("📝 Changes include:")
    print("   • Ultra-thin breadcrumb navigation (1px padding)")
    print("   • Slightly larger text for better readability")
    print("   • Minimal vertical space usage")
    print("   • Proper breadcrumb hierarchy maintained")
    print("   • Excellent user experience with clear navigation")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
