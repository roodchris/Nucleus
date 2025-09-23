#!/usr/bin/env python3
"""
GitHub Push Script for SEO Implementation
This script will commit and push all SEO changes to the GitHub repository.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr.strip()}")
        return False

def main():
    """Main function to push SEO changes to GitHub"""
    print("🚀 Starting GitHub push for SEO implementation...")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("app") or not os.path.exists("main.py"):
        print("❌ Error: Not in the correct project directory")
        print("   Please run this script from the project root directory")
        sys.exit(1)
    
    # Step 1: Initialize git repository if needed
    if not os.path.exists(".git"):
        print("📁 Initializing git repository...")
        if not run_command("git init", "Git initialization"):
            sys.exit(1)
    else:
        print("✅ Git repository already initialized")
    
    # Step 2: Add remote origin if not exists
    print("\n🔗 Setting up remote repository...")
    remote_check = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if "origin" not in remote_check.stdout:
        if not run_command("git remote add origin https://github.com/roodchris/Nucleus.git", "Adding remote origin"):
            print("⚠️  Remote might already exist, continuing...")
    else:
        print("✅ Remote origin already configured")
    
    # Step 3: Add all files
    print("\n📦 Adding files to git...")
    if not run_command("git add .", "Adding all files"):
        sys.exit(1)
    
    # Step 4: Check if there are changes to commit
    status_check = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if not status_check.stdout.strip():
        print("ℹ️  No changes to commit")
        return
    
    # Step 5: Create comprehensive commit message
    commit_message = f"""Implement comprehensive SEO optimization for physician platform

✅ SEO Features Implemented:
- Comprehensive meta tags (title, description, keywords, og:, twitter:)
- Schema.org structured data (WebSite, JobPosting, ItemList, DiscussionForumPosting)
- Breadcrumb navigation system with proper ARIA labels
- Pagination component with rel=next/prev tags
- Content optimization with physician-focused keywords
- robots.txt and XML sitemap generator
- Updated content to be inclusive of all medical specialties

📁 New Files:
- app/sitemap.py (XML sitemap generator)
- app/templates/components/pagination.html (pagination component)
- static/robots.txt (robots.txt file)
- SEO_IMPLEMENTATION_SUMMARY.md (comprehensive documentation)

🔧 Modified Files:
- app/templates/base.html (meta tags, breadcrumbs, pagination CSS)
- app/templates/home.html (structured data, content optimization)
- app/templates/opportunities/list.html (JobPosting schema, SEO meta)
- app/templates/forum/index.html (DiscussionForumPosting schema, SEO meta)
- app/__init__.py (registered sitemap blueprint)

🎯 Target Keywords: physician opportunities, medical jobs, physician forum, medical networking, physician compensation, medical moonlighting, residency programs, medical community, physician careers

This update transforms the platform from radiology-specific to all-medical-specialties while significantly improving SEO performance and search engine visibility.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    # Step 6: Commit changes
    print("\n💾 Committing changes...")
    commit_cmd = f'git commit -m "{commit_message}"'
    if not run_command(commit_cmd, "Committing SEO changes"):
        sys.exit(1)
    
    # Step 7: Push to GitHub
    print("\n🚀 Pushing to GitHub...")
    if not run_command("git push -u origin main", "Pushing to GitHub"):
        # Try alternative branch names
        print("⚠️  Trying alternative branch names...")
        if not run_command("git push -u origin master", "Pushing to master branch"):
            print("❌ Failed to push to GitHub")
            print("   Please check your GitHub credentials and repository permissions")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 SEO implementation successfully pushed to GitHub!")
    print("🔗 Repository: https://github.com/roodchris/Nucleus")
    print("📊 All SEO optimizations are now live and ready for search engines")
    print("=" * 60)

if __name__ == "__main__":
    main()