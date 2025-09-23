#!/bin/bash

# GitHub Push Script for SEO Implementation
# This script will commit and push all SEO changes to the GitHub repository.

echo "🚀 Starting GitHub push for SEO implementation..."
echo "============================================================"

# Check if we're in the right directory
if [ ! -d "app" ] || [ ! -f "main.py" ]; then
    echo "❌ Error: Not in the correct project directory"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Step 1: Initialize git repository if needed
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    if [ $? -ne 0 ]; then
        echo "❌ Git initialization failed"
        exit 1
    fi
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already initialized"
fi

# Step 2: Add remote origin if not exists
echo ""
echo "🔗 Setting up remote repository..."
if ! git remote | grep -q "origin"; then
    git remote add origin https://github.com/roodchris/Nucleus.git
    if [ $? -ne 0 ]; then
        echo "⚠️  Remote might already exist, continuing..."
    else
        echo "✅ Remote origin added"
    fi
else
    echo "✅ Remote origin already configured"
fi

# Step 3: Add all files
echo ""
echo "📦 Adding files to git..."
git add .
if [ $? -ne 0 ]; then
    echo "❌ Failed to add files"
    exit 1
fi
echo "✅ Files added to git"

# Step 4: Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo "ℹ️  No changes to commit"
    exit 0
fi

# Step 5: Commit changes
echo ""
echo "💾 Committing changes..."
git commit -m "Implement comprehensive SEO optimization for physician platform

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

Generated on: $(date)"

if [ $? -ne 0 ]; then
    echo "❌ Failed to commit changes"
    exit 1
fi
echo "✅ Changes committed"

# Step 6: Push to GitHub
echo ""
echo "🚀 Pushing to GitHub..."
git push -u origin main
if [ $? -ne 0 ]; then
    echo "⚠️  Trying alternative branch names..."
    git push -u origin master
    if [ $? -ne 0 ]; then
        echo "❌ Failed to push to GitHub"
        echo "   Please check your GitHub credentials and repository permissions"
        exit 1
    fi
fi

echo ""
echo "============================================================"
echo "🎉 SEO implementation successfully pushed to GitHub!"
echo "🔗 Repository: https://github.com/roodchris/Nucleus"
echo "📊 All SEO optimizations are now live and ready for search engines"
echo "============================================================"
