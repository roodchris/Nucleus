# Email Setup Guide

## Issue Identified
After your recent deployment, emails aren't being sent because the email credentials are not configured. The email functionality is working correctly, but the required environment variables are missing.

## Quick Fix

### For Local Development
Set these environment variables in your terminal:

```bash
export MAIL_USERNAME=your-email@gmail.com
export MAIL_PASSWORD=your-app-password
export MAIL_DEFAULT_SENDER=radnucleus@gmail.com
```

### For Production Deployment

#### Railway
1. Go to your Railway project dashboard
2. Click on "Variables" tab
3. Add these environment variables:
   - `MAIL_USERNAME`: your-email@gmail.com
   - `MAIL_PASSWORD`: your-app-password
   - `MAIL_DEFAULT_SENDER`: radnucleus@gmail.com

#### Render
1. Go to your Render dashboard
2. Select your service
3. Go to "Environment" tab
4. Add these environment variables:
   - `MAIL_USERNAME`: your-email@gmail.com
   - `MAIL_PASSWORD`: your-app-password
   - `MAIL_DEFAULT_SENDER`: radnucleus@gmail.com

#### Heroku
```bash
heroku config:set MAIL_USERNAME=your-email@gmail.com
heroku config:set MAIL_PASSWORD=your-app-password
heroku config:set MAIL_DEFAULT_SENDER=radnucleus@gmail.com
```

## Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this password as `MAIL_PASSWORD`

## Testing

After setting up the environment variables, test the email functionality:

```bash
python test_email.py
```

This will verify your email configuration and test sending emails.

## What Was Fixed

1. **Flask-Mail Instance**: Fixed the Flask-Mail instance to be globally accessible
2. **Email Service**: Updated email service functions to use the correct mail instance
3. **Configuration**: Verified email configuration is properly set up

## Email Features

The following emails are automatically sent:

- ✅ **New Application**: Sent to employers when radiologists apply
- ✅ **Status Update**: Sent to radiologists when application status changes (accepted/rejected)
- ✅ **Position Filled**: Sent to radiologists when a position is filled by another applicant

## Troubleshooting

If emails still don't work after setting environment variables:

1. Check that `MAIL_USERNAME` and `MAIL_PASSWORD` are set correctly
2. Verify the Gmail app password is correct
3. Check the application logs for error messages
4. Run `python test_email.py` to diagnose issues
