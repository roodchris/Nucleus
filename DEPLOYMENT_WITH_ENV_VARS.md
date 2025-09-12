# Deployment Guide with Environment Variables

## 🚀 Interventional Radiology Feature Deployed

The "Interventional Radiology" option has been successfully added to all job type fields throughout the application.

### ✅ Changes Made:
- Added `INTERVENTIONAL_RADIOLOGY` to the `OpportunityType` enum
- Updated all forms to include the new option
- Added automatic database migration for PostgreSQL
- Updated `render.yaml` with your production environment variables

### 🔧 Environment Variables Configured:
```
CORS_ORIGINS=*
DATABASE_URL=postgresql://nucleus_database_user:yWmpdEqkhdvvH0rbLuuXmFC4Gbx6BVJB@dpg-d2urvt7fte5s73bgkei0-a.oregon-postgres.render.com/nucleus_database
MAIL_DEFAULT_SENDER=radnucleus@gmail.com
MAIL_PASSWORD="tiry nsjm cqup rlhc"
MAIL_USERNAME=radnucleus@gmail.com
SECRET_KEY=a9e714c81188772bed55550380341d80b4ac5d55c82b59c42df6ca1a5df3826
```

### 🚀 Deployment Options:

#### Option 1: Render (Recommended)
1. Go to [render.com](https://render.com)
2. Connect your GitHub repository: `roodchris/Nucleus`
3. The `render.yaml` file is already configured with your environment variables
4. Render will automatically deploy when you push to main branch

#### Option 2: Railway
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add these environment variables in Railway dashboard:
   - `DATABASE_URL`: `postgresql://nucleus_database_user:yWmpdEqkhdvvH0rbLuuXmFC4Gbx6BVJB@dpg-d2urvt7fte5s73bgkei0-a.oregon-postgres.render.com/nucleus_database`
   - `SECRET_KEY`: `a9e714c81188772bed55550380341d80b4ac5d55c82b59c42df6ca1a5df3826`
   - `MAIL_USERNAME`: `radnucleus@gmail.com`
   - `MAIL_PASSWORD`: `tiry nsjm cqup rlhc`
   - `MAIL_DEFAULT_SENDER`: `radnucleus@gmail.com`
   - `CORS_ORIGINS`: `*`

#### Option 3: Heroku
1. Install Heroku CLI
2. Run: `heroku create your-app-name`
3. Set environment variables:
   ```bash
   heroku config:set DATABASE_URL="postgresql://nucleus_database_user:yWmpdEqkhdvvH0rbLuuXmFC4Gbx6BVJB@dpg-d2urvt7fte5s73bgkei0-a.oregon-postgres.render.com/nucleus_database"
   heroku config:set SECRET_KEY="a9e714c81188772bed55550380341d80b4ac5d55c82b59c42df6ca1a5df3826"
   heroku config:set MAIL_USERNAME="radnucleus@gmail.com"
   heroku config:set MAIL_PASSWORD="tiry nsjm cqup rlhc"
   heroku config:set MAIL_DEFAULT_SENDER="radnucleus@gmail.com"
   heroku config:set CORS_ORIGINS="*"
   ```
4. Run: `git push heroku main`

### 🎯 What's New:
- **Interventional Radiology** option now appears in all job type dropdowns
- Available in: Create Opportunity, Edit Opportunity, Filter Opportunities
- Fully integrated with backend filtering and search functionality
- Database migration automatically handles the new enum value

### ✅ Testing:
The feature has been tested with both SQLite and PostgreSQL databases and is ready for production deployment.

---
**Repository**: https://github.com/roodchris/Nucleus
**Last Updated**: $(date)
