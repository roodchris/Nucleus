#!/bin/bash

echo "🚀 Nucleus Deployment Script"
echo "============================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please run 'git init' first."
    exit 1
fi

# Check if we have uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  You have uncommitted changes. Please commit them first:"
    echo "   git add ."
    echo "   git commit -m 'Your commit message'"
    exit 1
fi

echo "✅ Repository is ready for deployment!"
echo ""
echo "🌐 Choose your deployment platform:"
echo ""
echo "1. Railway (Recommended - Easiest)"
echo "   - Go to https://railway.app"
echo "   - Sign up with GitHub"
echo "   - Click 'New Project' → 'Deploy from GitHub repo'"
echo "   - Select this repository"
echo "   - Add environment variables:"
echo "     SECRET_KEY=your-secret-key-here"
echo "     DATABASE_URL=sqlite:///app.db"
echo ""
echo "2. Render"
echo "   - Go to https://render.com"
echo "   - Sign up with GitHub"
echo "   - Click 'New' → 'Web Service'"
echo "   - Connect this repository"
echo "   - Build command: pip install -r requirements.txt"
echo "   - Start command: gunicorn app:app"
echo ""
echo "3. Heroku"
echo "   - Install Heroku CLI"
echo "   - Run: heroku login"
echo "   - Run: heroku create your-app-name"
echo "   - Run: git push heroku main"
echo "   - Run: heroku config:set SECRET_KEY=your-secret-key-here"
echo ""
echo "📝 Your app will be live at the URL provided by your chosen platform!"
echo ""
echo "🔧 For local testing, run: python app.py"
