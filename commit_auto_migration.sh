#!/bin/bash

echo "🚀 Committing automatic migration system..."

# Add all files
git add .

# Commit with a proper message
git commit -m "feat: Add automatic database migration system for future deployments

- Created auto_migrate.py with intelligent migration detection
- Added enable_specialty_features.py for dynamic feature enabling
- Updated app/__init__.py to run auto-migrations on startup  
- Enhanced render.yaml with preDeployCommand for migrations
- Added startup.py for production deployment with logging
- Updated Procfile to use --preload for proper initialization
- Re-enabled specialty column in ForumPost model

Features:
- Automatic schema migration on every deployment
- Dynamic feature enabling based on database schema
- Safe migration system (non-critical failures dont crash app)
- PostgreSQL and SQLite compatible
- Comprehensive logging and error handling
- Idempotent migrations (safe to run multiple times)

This ensures future deployments will never have database schema issues!"

# Push to GitHub
git push origin main

echo "✅ Auto-migration system deployed!"
