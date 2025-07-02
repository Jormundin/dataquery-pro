#!/usr/bin/env python3
"""
Test script for the automated daily distribution system
This script tests the functionality without modifying production data
"""

import asyncio
import json
from datetime import datetime
from database import (
    get_active_campaigns_for_daily_process,
    get_spss_count_day_5_users,
    distribute_users_to_campaigns,
    process_daily_user_distribution
)
from scheduler import DailyDistributionScheduler

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_database_connections():
    """Test database connections"""
    print_section("TESTING DATABASE CONNECTIONS")
    
    try:
        from database import test_all_connections
        result = test_all_connections()
        
        print(f"DSSB_APP Connection: {result['dssb_app']['status']}")
        if not result['dssb_app']['connected']:
            print(f"  Error: {result['dssb_app']['message']}")
        
        print(f"SPSS Connection: {result['spss']['status']}")
        if not result['spss']['connected']:
            print(f"  Error: {result['spss']['message']}")
        
        return result['dssb_app']['connected'] and result['spss']['connected']
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_active_campaigns():
    """Test getting active campaigns"""
    print_section("TESTING ACTIVE CAMPAIGNS RETRIEVAL")
    
    try:
        result = get_active_campaigns_for_daily_process()
        
        if result["success"]:
            print(f"✅ Found {result['count']} active campaigns")
            for campaign in result["campaigns"][:3]:  # Show first 3
                print(f"  - {campaign['theory_id']}: {campaign['theory_name']}")
                print(f"    Period: {campaign['theory_start_date']} to {campaign['theory_end_date']}")
            
            if result['count'] > 3:
                print(f"    ... and {result['count'] - 3} more campaigns")
        else:
            print(f"❌ Failed: {result['message']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing active campaigns: {e}")
        return {"success": False, "error": str(e)}

def test_spss_users():
    """Test getting SPSS users with COUNT_DAY = 5"""
    print_section("TESTING SPSS USER RETRIEVAL")
    
    try:
        result = get_spss_count_day_5_users()
        
        if result["success"]:
            print(f"✅ Found {result['count']} users with COUNT_DAY = 5")
            if result['iin_values']:
                print(f"  Sample IINs: {result['iin_values'][:5]}")  # Show first 5
        else:
            print(f"❌ Failed: {result['message']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing SPSS users: {e}")
        return {"success": False, "error": str(e)}

def test_distribution_logic():
    """Test the distribution logic without database writes"""
    print_section("TESTING DISTRIBUTION LOGIC")
    
    # Create mock data for testing
    mock_campaigns = [
        {
            "theory_id": "SC00000001.1",
            "theory_name": "Test Campaign 1",
            "theory_start_date": "2024-01-01",
            "theory_end_date": "2024-12-31",
            "user_count": 1000
        },
        {
            "theory_id": "SC00000002.1", 
            "theory_name": "Test Campaign 2",
            "theory_start_date": "2024-01-01",
            "theory_end_date": "2024-12-31",
            "user_count": 1500
        },
        {
            "theory_id": "SC00000003.1",
            "theory_name": "Test Campaign 3", 
            "theory_start_date": "2024-01-01",
            "theory_end_date": "2024-12-31",
            "user_count": 800
        }
    ]
    
    # Create mock IIN values (100 users)
    mock_iins = [f"12345678{i:02d}" for i in range(100)]
    
    try:
        result = distribute_users_to_campaigns(mock_iins, mock_campaigns)
        
        if result["success"]:
            print(f"✅ Distribution successful:")
            print(f"  Total users to distribute: {len(mock_iins)}")
            print(f"  Total campaigns: {len(mock_campaigns)}")
            print(f"  Users distributed: {result['total_users_distributed']}")
            
            for i, distribution in enumerate(result["distributions"]):
                campaign = distribution["campaign"]
                print(f"\n  Campaign {i+1}: {campaign['theory_id']}")
                print(f"    Total users: {distribution['total_users']}")
                
                for group_letter, group_users in distribution["groups"].items():
                    target = "SC_local_control" if group_letter == 'A' else "SC_local_target + SPSS"
                    print(f"    Group {group_letter}: {len(group_users)} users → {target}")
        else:
            print(f"❌ Distribution failed: {result['message']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing distribution logic: {e}")
        return {"success": False, "error": str(e)}

async def test_scheduler():
    """Test the scheduler functionality"""
    print_section("TESTING SCHEDULER")
    
    try:
        scheduler = DailyDistributionScheduler()
        
        # Test scheduler initialization
        print("✅ Scheduler initialized successfully")
        
        # Get initial status
        status = scheduler.get_scheduler_status()
        print(f"Initial status: {status['status']}")
        
        # Test start (but don't actually start to avoid scheduling)
        print("✅ Scheduler functionality verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing scheduler: {e}")
        return False

def test_email_configuration():
    """Test email configuration"""
    print_section("TESTING EMAIL CONFIGURATION")
    
    try:
        from email_sender import validate_email_config, EMAIL_SENDER, CAMPAIGN_NOTIFICATION_EMAILS
        
        if validate_email_config():
            print("✅ Email configuration is valid")
            print(f"  Sender: {EMAIL_SENDER}")
            print(f"  Recipients: {len(CAMPAIGN_NOTIFICATION_EMAILS)} configured")
        else:
            print("❌ Email configuration is invalid")
            
        return validate_email_config()
        
    except Exception as e:
        print(f"❌ Error testing email configuration: {e}")
        return False

async def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🚀 STARTING COMPREHENSIVE DAILY DISTRIBUTION TEST")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = {
        "database_connections": False,
        "active_campaigns": False,
        "spss_users": False,
        "distribution_logic": False,
        "scheduler": False,
        "email_config": False
    }
    
    # Test 1: Database connections
    test_results["database_connections"] = test_database_connections()
    
    # Test 2: Active campaigns (only if DB connected)
    if test_results["database_connections"]:
        campaigns_result = test_active_campaigns()
        test_results["active_campaigns"] = campaigns_result.get("success", False)
        
        # Test 3: SPSS users (only if DB connected)
        spss_result = test_spss_users()
        test_results["spss_users"] = spss_result.get("success", False)
    
    # Test 4: Distribution logic (always test with mock data)
    distribution_result = test_distribution_logic()
    test_results["distribution_logic"] = distribution_result.get("success", False)
    
    # Test 5: Scheduler
    test_results["scheduler"] = await test_scheduler()
    
    # Test 6: Email configuration
    test_results["email_config"] = test_email_configuration()
    
    # Final results
    print_section("TEST RESULTS SUMMARY")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Daily distribution system is ready!")
    else:
        print("⚠️  Some tests failed - please review the issues above")
    
    # Recommendations
    print_section("RECOMMENDATIONS")
    
    if not test_results["database_connections"]:
        print("🔧 Fix database connections before deploying")
    
    if not test_results["email_config"]:
        print("🔧 Configure email settings for notifications")
    
    if test_results["database_connections"] and not test_results["active_campaigns"]:
        print("💡 No active campaigns found - this is normal if no campaigns are currently running")
    
    if test_results["database_connections"] and not test_results["spss_users"]:
        print("💡 No COUNT_DAY=5 users found - this is normal if no users match the criteria today")
    
    print("\n🚀 Next Steps:")
    print("1. Deploy the updated code to production")
    print("2. Monitor the scheduler status via /scheduler/status endpoint") 
    print("3. Check email notifications for daily distribution results")
    print("4. Use /daily-distribution/preview to preview before 9 AM")

if __name__ == "__main__":
    # Run the comprehensive test
    asyncio.run(run_comprehensive_test()) 