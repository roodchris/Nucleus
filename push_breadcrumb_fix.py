#!/usr/bin/env python3
"""
Script to push breadcrumb navigation improvements to GitHub
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
    print("🚀 Pushing breadcrumb navigation improvements to GitHub...")
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
    
    # Commit changes
    commit_message = """feat: Make breadcrumb navigation more compact and thinner

- Reduced padding from 0.75rem to 0.375rem (50% smaller)
- Decreased font size from 0.875rem to 0.75rem
- Tightened gaps from 0.5rem to 0.25rem
- Reduced icon size from 14px to 10px
- Added subtle hover effects and better touch targets
- Improved space efficiency while maintaining usability
- Better page real estate for main content

This makes the breadcrumb navigation much less intrusive while
still providing clear navigation context for users."""
    
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
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
    print("🎉 Successfully pushed breadcrumb navigation improvements to GitHub!")
    print("📝 Changes include:")
    print("   • More compact breadcrumb navigation")
    print("   • Reduced vertical space usage")
    print("   • Better visual hierarchy")
    print("   • Improved user experience")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
