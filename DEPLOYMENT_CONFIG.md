# Deployment Configuration

## Required Environment Variables

Set these environment variables in your deployment platform:

### Core Configuration
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
```

### Email Configuration
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=radnucleus@gmail.com
MAIL_PASSWORD=pftmjsssraekcktm
MAIL_DEFAULT_SENDER=radnucleus@gmail.com
MAIL_SUPPRESS_SEND=false
```

## Platform-Specific Instructions

### Railway
1. Go to your Railway project dashboard
2. Click on "Variables" tab
3. Add all the environment variables listed above

### Render
1. Go to your Render dashboard
2. Select your service
3. Go to "Environment" tab
4. Add all the environment variables listed above

### Heroku
```bash
heroku config:set SECRET_KEY=your-secret-key-here
heroku config:set DATABASE_URL=sqlite:///app.db
heroku config:set MAIL_SERVER=smtp.gmail.com
heroku config:set MAIL_PORT=587
heroku config:set MAIL_USE_TLS=true
heroku config:set MAIL_USERNAME=radnucleus@gmail.com
heroku config:set MAIL_PASSWORD=pftmjsssraekcktm
heroku config:set MAIL_DEFAULT_SENDER=radnucleus@gmail.com
heroku config:set MAIL_SUPPRESS_SEND=false
```

## Testing

After deployment, you can test the email functionality by:
1. Creating a test user account
2. Creating a test opportunity
3. Submitting an application
4. Checking that emails are sent

The email system will automatically send:
- ✅ New application notifications to employers
- ✅ Status update notifications to applicants
- ✅ Position filled notifications to rejected applicants
