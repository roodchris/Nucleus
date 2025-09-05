# Email Notification Setup

This application now includes email notifications for application status changes. Here's how to configure it:

## Email Configuration

### Environment Variables

Set these environment variables to configure email sending:

```bash
# Gmail SMTP Configuration (recommended)
export MAIL_SERVER=smtp.gmail.com
export MAIL_PORT=587
export MAIL_USE_TLS=true
export MAIL_USERNAME=your-email@gmail.com
export MAIL_PASSWORD=your-app-password
export MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# For testing without sending emails
export MAIL_SUPPRESS_SEND=false
```

### Gmail Setup

1. Enable 2-factor authentication on your Gmail account
2. Generate an "App Password" for this application:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this password as `MAIL_PASSWORD`

### Other Email Providers

You can use other SMTP providers by changing the configuration:

```bash
# Outlook/Hotmail
export MAIL_SERVER=smtp-mail.outlook.com
export MAIL_PORT=587

# Yahoo
export MAIL_SERVER=smtp.mail.yahoo.com
export MAIL_PORT=587

# Custom SMTP
export MAIL_SERVER=your-smtp-server.com
export MAIL_PORT=587
```

## Testing

Run the test script to verify email configuration:

```bash
python test_email.py
```

## Email Templates

The following email templates are included:

- **New Application**: Sent to employers when a radiologist applies
- **Status Update**: Sent to radiologists when their application status changes
- **Position Filled**: Sent to radiologists when a position is filled by another applicant

## Features

- ✅ Email notifications when radiologists apply for positions
- ✅ Email notifications when application status changes (accepted/rejected)
- ✅ Bulk notifications when positions are filled
- ✅ Professional HTML email templates
- ✅ Encouragement messages for rejected applicants
- ✅ Employer contact information in notifications

## Troubleshooting

### Common Issues

1. **Authentication failed**: Check your email credentials and app password
2. **Connection refused**: Verify SMTP server and port settings
3. **Emails not sending**: Check if `MAIL_SUPPRESS_SEND` is set to `false`

### Testing Without Sending Emails

Set `MAIL_SUPPRESS_SEND=true` to test the system without actually sending emails.

### Logs

Check the application logs for email sending errors and debugging information.
