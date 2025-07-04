# Environment Setup Guide

## Overview

This guide explains how to configure SoftCollection using environment variables instead of hardcoded values. This allows you to customize users and email settings without modifying the source code, which means your settings will persist through pull requests and updates.

## Quick Setup

1. **Copy the configuration template:**
   ```bash
   cp config_template.env .env
   ```

2. **Edit the `.env` file with your actual values:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Update the required settings** (see details below)

4. **Start the application:**
   ```bash
   python main.py
   ```

## Required Environment Variables

### 1. Permitted Users (`PERMITTED_USERS`)

**Format:** `USER_ID1:NAME1:ROLE1:PERMISSION1,PERMISSION2;USER_ID2:NAME2:ROLE2:PERMISSION1`

**Example:**
```bash
PERMITTED_USERS=00058215:Nadir:admin:read,write,admin;00012345:John:user:read;00067890:Alice:analyst:read,write
```

**Available Roles:**
- `admin` - Full system access
- `user` - Basic user access
- `analyst` - Analyst access

**Available Permissions:**
- `read` - View data and reports
- `write` - Create campaigns and modify data
- `admin` - Administrative functions

**Single User Example:**
```bash
PERMITTED_USERS=00058215:Nadir:admin:read,write,admin
```

### 2. Email Notifications (`CAMPAIGN_NOTIFICATION_EMAILS`)

**Format:** Comma-separated list of email addresses

**Example:**
```bash
CAMPAIGN_NOTIFICATION_EMAILS=nadir@halykbank.kz,admin@halykbank.kz,analyst@halykbank.kz
```

**What these emails receive:**
- Campaign creation success notifications
- Campaign creation error notifications
- Daily distribution notifications
- System error alerts

## Optional Environment Variables

### Database Configuration
```bash
# Primary Database (Required)
ORACLE_HOST=your_database_host
ORACLE_PORT=1521
ORACLE_SID=DSSB_APP
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password

# Secondary Database (Optional)
SPSS_ORACLE_HOST=your_spss_host
SPSS_ORACLE_PORT=1521
SPSS_ORACLE_SID=SPSS
SPSS_ORACLE_USER=your_spss_username
SPSS_ORACLE_PASSWORD=your_spss_password
```

### Email SMTP Configuration (Optional)
```bash
EMAIL_SENDER=your-sender@company.com
SMTP_SERVER=mail.company.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
```

### Application Settings (Optional)
```bash
JWT_SECRET_KEY=your_very_secure_secret_key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
APP_HOST=0.0.0.0
APP_PORT=8000
```

## How It Works

### User Authentication
- The system reads `PERMITTED_USERS` environment variable on startup
- If not found, it falls back to default user: `00058215:Nadir:admin:read,write,admin`
- Users are authenticated against LDAP, but only allowed users can access the system

### Email Notifications
- The system reads `CAMPAIGN_NOTIFICATION_EMAILS` environment variable on startup
- If not found, it falls back to example emails that should be replaced
- All campaign and system notifications are sent to these addresses

## Troubleshooting

### Issue: Users can't log in
**Solution:** Check your `PERMITTED_USERS` format
```bash
# Correct format
PERMITTED_USERS=00058215:Nadir:admin:read,write,admin

# Wrong format (missing permissions)
PERMITTED_USERS=00058215:Nadir:admin
```

### Issue: No email notifications received
**Solution:** Check your `CAMPAIGN_NOTIFICATION_EMAILS` setting
```bash
# Correct format
CAMPAIGN_NOTIFICATION_EMAILS=user1@company.com,user2@company.com

# Wrong format (spaces around emails)
CAMPAIGN_NOTIFICATION_EMAILS=user1@company.com, user2@company.com
```

### Issue: Environment variables not loading
**Solutions:**
1. Ensure the `.env` file is in the same directory as `main.py`
2. Check file permissions: `chmod 644 .env`
3. Restart the application after changing `.env`

## Security Best Practices

1. **Never commit `.env` files to version control:**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use strong passwords for database accounts**

3. **Limit user permissions to minimum required:**
   ```bash
   # Good: minimal permissions
   PERMITTED_USERS=00012345:John:user:read
   
   # Avoid: unnecessary admin permissions
   PERMITTED_USERS=00012345:John:admin:read,write,admin
   ```

4. **Regularly review permitted users list**

## Examples

### Development Setup
```bash
# .env file for development
PERMITTED_USERS=00058215:Nadir:admin:read,write,admin;00012345:TestUser:user:read
CAMPAIGN_NOTIFICATION_EMAILS=nadir@halykbank.kz,dev@company.com
ORACLE_HOST=dev-db.company.com
ORACLE_USER=dev_user
ORACLE_PASSWORD=dev_password
```

### Production Setup
```bash
# .env file for production
PERMITTED_USERS=00058215:Nadir:admin:read,write,admin;00012345:Manager:user:read,write;00067890:Analyst:analyst:read
CAMPAIGN_NOTIFICATION_EMAILS=nadir@halykbank.kz,manager@halykbank.kz,admin@halykbank.kz
ORACLE_HOST=prod-db.company.com
ORACLE_USER=prod_user
ORACLE_PASSWORD=secure_prod_password
JWT_SECRET_KEY=very_secure_production_key
```

## Adding New Users

To add a new user:

1. **Get their LDAP user ID** (e.g., from HR or IT)
2. **Add them to `PERMITTED_USERS`:**
   ```bash
   # Before
   PERMITTED_USERS=00058215:Nadir:admin:read,write,admin
   
   # After (adding John with user role)
   PERMITTED_USERS=00058215:Nadir:admin:read,write,admin;00012345:John:user:read
   ```
3. **Restart the application**
4. **Test the new user can log in**

## Updating Email Lists

To modify notification recipients:

1. **Update `CAMPAIGN_NOTIFICATION_EMAILS`:**
   ```bash
   # Before
   CAMPAIGN_NOTIFICATION_EMAILS=old@company.com
   
   # After
   CAMPAIGN_NOTIFICATION_EMAILS=new@company.com,manager@company.com
   ```
2. **Restart the application**
3. **Test notifications** using the test endpoint

## Validation

The system validates configurations on startup and logs the results:

```bash
# Check logs for validation messages
tail -f login_history.log
```

Look for messages like:
- `"Loaded 3 permitted users from environment variable"`
- `"Loaded 2 email addresses from CAMPAIGN_NOTIFICATION_EMAILS"`
- `"No PERMITTED_USERS environment variable found, using default users"`

## Support

If you encounter issues:
1. Check the application logs for error messages
2. Verify your environment variable formats
3. Test with minimal configurations first
4. Contact the development team for assistance 