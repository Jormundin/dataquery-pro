#!/usr/bin/env python3
"""
Environment Configuration Test Script
=====================================

This script tests your environment configuration for users and emails
to ensure everything is set up correctly before starting the main application.

Usage: python test_env_config.py
"""

import os
import sys
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    if os.path.exists('.env'):
        load_dotenv('.env')
        print("✅ Found and loaded .env file")
        return True
    else:
        print("⚠️  No .env file found")
        print("   Create one by copying: cp config_template.env .env")
        return False

def test_permitted_users():
    """Test the PERMITTED_USERS configuration"""
    print("\n📋 Testing PERMITTED_USERS configuration...")
    
    users_env = os.getenv('PERMITTED_USERS', '')
    
    if not users_env:
        print("⚠️  PERMITTED_USERS not set - using default user")
        print("   Add to .env: PERMITTED_USERS=00058215:Nadir:admin:read,write,admin")
        return False
    
    try:
        users = {}
        user_entries = users_env.split(';')
        
        for entry in user_entries:
            if not entry.strip():
                continue
                
            parts = entry.strip().split(':')
            if len(parts) != 4:
                print(f"❌ Invalid user entry format: {entry}")
                print("   Expected format: USER_ID:NAME:ROLE:PERMISSIONS")
                return False
            
            user_id, name, role, permissions_str = parts
            permissions = [p.strip() for p in permissions_str.split(',') if p.strip()]
            
            if not user_id or not name or not role or not permissions:
                print(f"❌ Missing information in user entry: {entry}")
                return False
            
            users[user_id] = {
                'name': name,
                'role': role,
                'permissions': permissions
            }
            
            print(f"   ✅ User: {user_id} ({name}) - Role: {role} - Permissions: {', '.join(permissions)}")
        
        print(f"✅ Successfully parsed {len(users)} user(s)")
        return True
        
    except Exception as e:
        print(f"❌ Error parsing PERMITTED_USERS: {e}")
        return False

def test_email_config():
    """Test the email configuration"""
    print("\n📧 Testing email configuration...")
    
    emails_env = os.getenv('CAMPAIGN_NOTIFICATION_EMAILS', '')
    
    if not emails_env:
        print("⚠️  CAMPAIGN_NOTIFICATION_EMAILS not set - using default emails")
        print("   Add to .env: CAMPAIGN_NOTIFICATION_EMAILS=your@email.com,admin@email.com")
        return False
    
    try:
        emails = [email.strip() for email in emails_env.split(',') if email.strip()]
        
        if not emails:
            print("❌ No valid email addresses found")
            return False
        
        # Basic email validation
        for email in emails:
            if '@' not in email or '.' not in email.split('@')[1]:
                print(f"⚠️  Potentially invalid email format: {email}")
            else:
                print(f"   ✅ Email: {email}")
        
        print(f"✅ Successfully parsed {len(emails)} email address(es)")
        return True
        
    except Exception as e:
        print(f"❌ Error parsing CAMPAIGN_NOTIFICATION_EMAILS: {e}")
        return False

def test_database_config():
    """Test basic database configuration"""
    print("\n🗄️  Testing database configuration...")
    
    required_vars = ['ORACLE_HOST', 'ORACLE_PORT', 'ORACLE_SID', 'ORACLE_USER', 'ORACLE_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Mask password for display
            display_value = '***' if 'PASSWORD' in var else value
            print(f"   ✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"❌ Missing required database configuration: {', '.join(missing_vars)}")
        return False
    
    # Test optional SPSS database
    spss_vars = ['SPSS_ORACLE_HOST', 'SPSS_ORACLE_USER', 'SPSS_ORACLE_PASSWORD']
    spss_configured = all(os.getenv(var) for var in spss_vars)
    
    if spss_configured:
        print("   ✅ SPSS database configuration found")
    else:
        print("   ⚠️  SPSS database configuration not found (optional)")
    
    return True

def test_smtp_config():
    """Test SMTP configuration"""
    print("\n📬 Testing SMTP configuration...")
    
    smtp_vars = ['EMAIL_SENDER', 'SMTP_SERVER', 'SMTP_USERNAME', 'SMTP_PASSWORD']
    configured_vars = [var for var in smtp_vars if os.getenv(var)]
    
    if len(configured_vars) == len(smtp_vars):
        print("   ✅ Full SMTP configuration found")
        for var in smtp_vars:
            value = os.getenv(var)
            display_value = '***' if 'PASSWORD' in var else value
            print(f"      {var}: {display_value}")
        return True
    elif configured_vars:
        print(f"   ⚠️  Partial SMTP configuration found: {', '.join(configured_vars)}")
        print("   Using default SMTP settings for missing values")
        return True
    else:
        print("   ⚠️  No SMTP configuration found - using hardcoded defaults")
        return True

def main():
    """Main test function"""
    print("🧪 SoftCollection Environment Configuration Test")
    print("=" * 50)
    
    # Load environment
    env_loaded = load_environment()
    
    # Run tests
    users_ok = test_permitted_users()
    emails_ok = test_email_config()
    db_ok = test_database_config()
    smtp_ok = test_smtp_config()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Configuration Test Summary:")
    
    status_icon = lambda ok: "✅" if ok else "❌"
    print(f"   {status_icon(env_loaded)} Environment file (.env)")
    print(f"   {status_icon(users_ok)} Permitted users")
    print(f"   {status_icon(emails_ok)} Email notifications")
    print(f"   {status_icon(db_ok)} Database connection")
    print(f"   {status_icon(smtp_ok)} SMTP configuration")
    
    all_critical_ok = users_ok and emails_ok and db_ok
    
    if all_critical_ok:
        print("\n🎉 Configuration looks good! You can start the application.")
        print("   Run: python main.py")
    else:
        print("\n⚠️  Please fix the configuration issues above before starting the application.")
        print("   See ENVIRONMENT_SETUP.md for detailed instructions.")
    
    print("\n📖 For detailed setup instructions, see:")
    print("   - ENVIRONMENT_SETUP.md")
    print("   - config_template.env")
    
    return 0 if all_critical_ok else 1

if __name__ == "__main__":
    try:
        # Try to import python-dotenv
        from dotenv import load_dotenv
    except ImportError:
        print("❌ python-dotenv not installed")
        print("   Install with: pip install python-dotenv")
        sys.exit(1)
    
    exit_code = main()
    sys.exit(exit_code) 