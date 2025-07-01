#!/usr/bin/env python3
"""
SOFTCOLLECTION EMAIL SENDER MODULE
==================================

This module handles email notifications for the SoftCollection application.
Specifically designed for campaign creation and stratification notifications.

Features:
- Campaign success notifications
- Dual database insertion status reporting
- Detailed stratification results
- Error notifications for failed operations

"""

import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO
from datetime import datetime
import json
from typing import List, Dict, Any, Optional

# Setup logging
logger = logging.getLogger('softcollection.email')

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

# HARDCODED EMAIL CONFIGURATION (for plug-and-play functionality)
EMAIL_SENDER = 'cdsrb@halykbank.kz'
SMTP_SERVER = 'mail.halykbank.nb'
SMTP_PORT = 587
SMTP_USERNAME = 'cdsrb'
SMTP_PASSWORD = 'oREgNwtWr9B5F4dsGjjZ'

# Override with environment variables if they exist (for security)
EMAIL_SENDER = os.getenv('EMAIL_SENDER', EMAIL_SENDER)
SMTP_SERVER = os.getenv('SMTP_SERVER', SMTP_SERVER)
SMTP_PORT = int(os.getenv('SMTP_PORT', str(SMTP_PORT)))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', SMTP_USERNAME)
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', SMTP_PASSWORD)

# HARDCODED CAMPAIGN NOTIFICATION RECIPIENTS
CAMPAIGN_NOTIFICATION_EMAILS = [
    'manager@example.com',  # Replace with actual manager email
    'admin@example.com',    # Replace with actual admin email
    'analyst@example.com'   # Replace with actual analyst email
]

# Override with environment variables if configured
def parse_email_list(env_var_name, default_list=None):
    """Parse comma-separated email list from environment variable"""
    email_string = os.getenv(env_var_name, '')
    if email_string:
        return [email.strip() for email in email_string.split(',') if email.strip()]
    return default_list or []

CAMPAIGN_NOTIFICATION_EMAILS = parse_email_list('CAMPAIGN_NOTIFICATION_EMAILS', CAMPAIGN_NOTIFICATION_EMAILS)

# =============================================================================
# CORE EMAIL FUNCTIONS
# =============================================================================

def send_email(recipients: List[str], subject: str, message: str, attachments: Optional[List] = None) -> bool:
    """
    Send email with optional attachments
    
    Args:
        recipients: List of email addresses
        subject: Subject line for the email
        message: Body content of the email (can be HTML)
        attachments: Optional list of attachments
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        if not recipients:
            logger.warning("No email recipients provided")
            return False
            
        # Ensure recipients is a list
        if isinstance(recipients, str):
            recipients = [recipients]
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        
        # Add HTML content
        html_part = MIMEText(message, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Process attachments if provided
        if attachments:
            for attachment in attachments:
                if attachment is None:
                    continue
                    
                part = MIMEBase('application', 'octet-stream')
                if hasattr(attachment, 'read'):
                    part.set_payload(attachment.read())
                else:
                    part.set_payload(attachment)
                    
                encoders.encode_base64(part)
                
                filename = getattr(attachment, 'name', f"attachment_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                part.add_header('Content-Disposition', f"attachment; filename= {filename}")
                msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, recipients, text)
        server.quit()
        
        logger.info(f"Email sent successfully to {', '.join(recipients)}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

# =============================================================================
# CAMPAIGN NOTIFICATION FUNCTIONS
# =============================================================================

def create_campaign_success_email(stratification_result: Dict[str, Any], user: str) -> tuple:
    """
    Create email content for successful campaign creation
    
    Args:
        stratification_result: Result from stratification process
        user: Username who created the campaign
    
    Returns:
        tuple: (subject, html_message)
    """
    theories = stratification_result.get('theories', [])
    base_campaign_id = stratification_result.get('base_campaign_id', 'N/A')
    total_users = stratification_result.get('total_users', 0)
    execution_time = stratification_result.get('execution_time', 'N/A')
    
    # Determine database status
    database_status = "✅ Успешно"
    database_details = ""
    
    # Check if any theory has detailed results (indicating dual database)
    for theory in theories:
        if theory.get('detailed_results'):
            detailed = theory['detailed_results']
            dssb_success = detailed.get('dssb_app', {}).get('success', False)
            spss_success = detailed.get('spss', {}).get('success', False)
            
            if dssb_success and spss_success:
                database_status = "✅ Обе базы данных (DSSB_APP + SPSS)"
            elif dssb_success:
                database_status = "⚠️ Частично (только DSSB_APP)"
            else:
                database_status = "❌ Ошибка"
            break
    
    subject = f"✅ SoftCollection: Кампания {base_campaign_id} успешно создана"
    
    # Create groups table
    groups_html = ""
    for theory in theories:
        group_type_icon = "🎯" if theory.get('group_type') == 'control' else "📊"
        target_table = "SC_local_control" if theory.get('group_type') == 'control' else "SC_local_target"
        
        groups_html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">
                {group_type_icon} {theory.get('group', 'N/A')}
            </td>
            <td style="padding: 8px; border: 1px solid #ddd;">
                {theory.get('theory_id', 'N/A')}
            </td>
            <td style="padding: 8px; border: 1px solid #ddd;">
                {theory.get('group_type', 'N/A')}
            </td>
            <td style="padding: 8px; border: 1px solid #ddd;">
                {theory.get('users_added', 0):,}
            </td>
            <td style="padding: 8px; border: 1px solid #ddd;">
                {target_table}
            </td>
        </tr>
        """
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Уведомление о создании кампании</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 28px;">
                ✅ Кампания успешно создана
            </h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                SoftCollection Система Стратификации
            </p>
        </div>
        
        <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 25px;">
            <h2 style="color: #2c3e50; margin-top: 0;">📋 Сводка кампании</h2>
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 5px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <tr style="background: #3498db; color: white;">
                    <th style="padding: 12px; text-align: left;">Параметр</th>
                    <th style="padding: 12px; text-align: left;">Значение</th>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <strong>Базовый ID кампании</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <code style="background: #e8f4f8; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{base_campaign_id}</code>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <strong>Общее количество пользователей</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <span style="font-size: 18px; font-weight: bold; color: #27ae60;">{total_users:,}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <strong>Количество групп</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        {len(theories)}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <strong>Время выполнения</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        {execution_time}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <strong>Статус баз данных</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        {database_status}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px;">
                        <strong>Создано пользователем</strong>
                    </td>
                    <td style="padding: 10px;">
                        {user}
                    </td>
                </tr>
            </table>
        </div>
        
        <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 25px;">
            <h2 style="color: #2c3e50; margin-top: 0;">🎯 Детали групп</h2>
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 5px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background: #3498db; color: white;">
                        <th style="padding: 12px; text-align: left;">Группа</th>
                        <th style="padding: 12px; text-align: left;">ID Теории</th>
                        <th style="padding: 12px; text-align: left;">Тип</th>
                        <th style="padding: 12px; text-align: left;">Пользователей</th>
                        <th style="padding: 12px; text-align: left;">Целевая таблица</th>
                    </tr>
                </thead>
                <tbody>
                    {groups_html}
                </tbody>
            </table>
        </div>
        
        <div style="background: #e8f5e8; border: 1px solid #c3e6c3; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
            <h3 style="color: #2d5a2d; margin-top: 0;">💡 Информация о размещении данных</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li><strong>Контрольная группа (A):</strong> размещена в <code>DSSB_APP.SC_local_control</code></li>
                <li><strong>Целевые группы (B, C, D, E):</strong> размещены в <code>DSSB_APP.SC_local_target</code> и <code>SPSS.SC_theory_users</code></li>
                <li><strong>Реестр кампаний:</strong> зарегистрирован в <code>DSSB_APP.SoftCollection_theories</code></li>
            </ul>
        </div>
        
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p style="margin: 0; color: #856404;">
                <strong>📧 Это автоматическое уведомление</strong> от системы SoftCollection.
                Кампания готова к использованию в аналитических процессах.
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #666; font-size: 14px; border-top: 1px solid #eee;">
            <p>SoftCollection - Система Управления Кампаниями</p>
            <p>Время отправки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """
    
    return subject, html_message

def create_campaign_error_email(error_details: Dict[str, Any], user: str) -> tuple:
    """
    Create email content for failed campaign creation
    
    Args:
        error_details: Details about the error
        user: Username who attempted to create the campaign
    
    Returns:
        tuple: (subject, html_message)
    """
    error_message = error_details.get('error', 'Unknown error')
    operation = error_details.get('operation', 'Campaign creation')
    
    subject = f"❌ SoftCollection: Ошибка создания кампании"
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Ошибка создания кампании</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 28px;">
                ❌ Ошибка создания кампании
            </h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                SoftCollection Система Стратификации
            </p>
        </div>
        
        <div style="background: #fff5f5; border: 1px solid #fed7d7; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
            <h3 style="color: #c53030; margin-top: 0;">🚨 Детали ошибки</h3>
            <p><strong>Операция:</strong> {operation}</p>
            <p><strong>Пользователь:</strong> {user}</p>
            <p><strong>Время:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
            <div style="background: #f7fafc; padding: 15px; border-left: 4px solid #e53e3e; margin-top: 15px;">
                <p style="margin: 0; font-family: monospace; color: #c53030;">
                    {error_message}
                </p>
            </div>
        </div>
        
        <div style="background: #e6fffa; border: 1px solid #81e6d9; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
            <h3 style="color: #234e52; margin-top: 0;">🔧 Рекомендуемые действия</h3>
            <ul>
                <li>Проверьте подключение к базам данных</li>
                <li>Убедитесь в корректности данных стратификации</li>
                <li>Проверьте логи приложения для получения дополнительной информации</li>
                <li>При необходимости обратитесь к администратору системы</li>
            </ul>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #666; font-size: 14px; border-top: 1px solid #eee;">
            <p>SoftCollection - Система Управления Кампаниями</p>
            <p>Автоматическое уведомление об ошибке</p>
        </div>
    </body>
    </html>
    """
    
    return subject, html_message

# =============================================================================
# HIGH-LEVEL NOTIFICATION FUNCTIONS
# =============================================================================

def send_campaign_success_notification(stratification_result: Dict[str, Any], user: str) -> bool:
    """
    Send success notification for campaign creation
    
    Args:
        stratification_result: Result from successful stratification
        user: Username who created the campaign
    
    Returns:
        bool: True if notification sent successfully
    """
    try:
        subject, message = create_campaign_success_email(stratification_result, user)
        
        # Create JSON attachment with detailed results
        json_data = json.dumps(stratification_result, indent=2, ensure_ascii=False, default=str)
        attachment = BytesIO(json_data.encode('utf-8'))
        attachment.name = f"campaign_details_{stratification_result.get('base_campaign_id', 'unknown')}.json"
        
        return send_email(CAMPAIGN_NOTIFICATION_EMAILS, subject, message, [attachment])
    except Exception as e:
        logger.error(f"Failed to send campaign success notification: {str(e)}")
        return False

def send_campaign_error_notification(error_details: Dict[str, Any], user: str) -> bool:
    """
    Send error notification for failed campaign creation
    
    Args:
        error_details: Details about the error
        user: Username who attempted the operation
    
    Returns:
        bool: True if notification sent successfully
    """
    try:
        subject, message = create_campaign_error_email(error_details, user)
        return send_email(CAMPAIGN_NOTIFICATION_EMAILS, subject, message)
    except Exception as e:
        logger.error(f"Failed to send campaign error notification: {str(e)}")
        return False

# =============================================================================
# CONFIGURATION AND TESTING
# =============================================================================

def validate_email_config() -> bool:
    """
    Validate email configuration
    
    Returns:
        bool: True if configuration is valid
    """
    required_fields = [EMAIL_SENDER, SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD]
    if not all(required_fields):
        logger.error("Missing required email configuration fields")
        return False
    
    if not CAMPAIGN_NOTIFICATION_EMAILS:
        logger.error("No campaign notification email recipients configured")
        return False
    
    return True

def test_email_notification() -> bool:
    """
    Send a test email notification
    
    Returns:
        bool: True if test email sent successfully
    """
    if not validate_email_config():
        return False
    
    # Create test stratification result
    test_result = {
        'base_campaign_id': 'SC00000001',
        'theories': [
            {
                'theory_id': 'SC00000001.1',
                'group': 'A',
                'group_type': 'control',
                'users_added': 1000,
                'theory_name': 'Test Campaign - Group A'
            },
            {
                'theory_id': 'SC00000001.2',
                'group': 'B',
                'group_type': 'target',
                'users_added': 1000,
                'theory_name': 'Test Campaign - Group B'
            }
        ],
        'total_users': 2000,
        'execution_time': '2.456s'
    }
    
    return send_campaign_success_notification(test_result, 'test_user')

if __name__ == "__main__":
    # Test the email configuration and send a test email
    print("SoftCollection Email Sender Test")
    print("=" * 40)
    
    if validate_email_config():
        print("✅ Email configuration is valid")
        print(f"Recipients: {', '.join(CAMPAIGN_NOTIFICATION_EMAILS)}")
        
        # Send test email
        if test_email_notification():
            print("✅ Test email sent successfully!")
        else:
            print("❌ Failed to send test email")
    else:
        print("❌ Email configuration is invalid")
        print("Please check your email configuration and try again.") 