#!/usr/bin/env python3
"""
Script to push hero subtitle update to GitHub
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
    print("🚀 Pushing hero subtitle update to GitHub...")
    print("=" * 60)
    
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
    
    # Commit changes - use a simple single-line message to avoid shell escaping issues
    commit_message = "feat: Update hero subtitle to be more action-oriented and community-focused"
    
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
    
    print("=" * 60)
    print("🎉 Successfully pushed hero subtitle update to GitHub!")
    print("📝 Changes include:")
    print("   • More action-oriented hero subtitle")
    print("   • Emphasis on applying for career opportunities")
    print("   • Community learning focus")
    print("   • Better user engagement messaging")
    print("   • Improved platform positioning")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
