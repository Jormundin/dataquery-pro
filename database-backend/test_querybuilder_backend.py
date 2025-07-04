#!/usr/bin/env python3
"""
Direct test of QueryBuilder backend functionality
Tests the /query/execute endpoint with large dataset simulation
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"  # Replace with actual username
PASSWORD = "admin123"  # Replace with actual password

def login():
    """Login to get authentication token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": USERNAME, "password": PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_query_execute_endpoint(token):
    """Test the /query/execute endpoint directly"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with 2.7M limit to trigger chunked processing
    query_data = {
        "database_id": "DSSB_APP",
        "table": "DSSB_DM.RB_CLIENTS",
        "columns": [],  # All columns
        "filters": [],
        "sort_by": None,
        "sort_order": "ASC",
        "limit": 2700000,  # 2.7M to trigger the issue
        "client_id": f"test_backend_{int(time.time())}"
    }
    
    print(f"\n🧪 Testing /query/execute endpoint directly...")
    print(f"   Limit: {query_data['limit']:,}")
    print(f"   Client ID: {query_data['client_id']}")
    print(f"   Table: {query_data['table']}")
    
    start_time = time.time()
    
    try:
        print(f"🔄 Sending request to {BASE_URL}/query/execute...")
        response = requests.post(
            f"{BASE_URL}/query/execute",
            json=query_data,
            headers=headers,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n📊 Response received after {duration:.2f} seconds")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Request successful!")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Total rows: {data.get('row_count', 0):,}")
            print(f"   Rows returned: {len(data.get('data', [])):,}")
            print(f"   Execution time: {data.get('execution_time', 'N/A')}")
            print(f"   Message: {data.get('message', 'No message')}")
            
            # Check for temp file
            if data.get('temp_file_id'):
                print(f"   📁 Temp file created: {data.get('temp_file_id')}")
            
            # Check for chunked processing indicators
            if data.get('row_count', 0) > 500000:
                print(f"   🔧 Large dataset - should have used chunked processing")
            
            return True
            
        else:
            print(f"❌ HTTP Error {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detail: {error_data.get('detail', 'No details')}")
                print(f"   Error: {error_data.get('error', 'No error info')}")
            except:
                print(f"   Raw response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after {time.time() - start_time:.2f} seconds")
        print("   This might indicate the old issue is still present")
        return False
        
    except Exception as e:
        print(f"❌ Request failed: {type(e).__name__}: {str(e)}")
        return False

def test_smaller_query(token):
    """Test with a smaller query that should work"""
    headers = {"Authorization": f"Bearer {token}"}
    
    query_data = {
        "database_id": "DSSB_APP",
        "table": "DSSB_DM.RB_CLIENTS",
        "columns": [],
        "filters": [],
        "sort_by": None,
        "sort_order": "ASC",
        "limit": 1000,  # Small limit
        "client_id": f"test_small_{int(time.time())}"
    }
    
    print(f"\n🧪 Testing with small dataset (1000 rows)...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/query/execute",
            json=query_data,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Small query successful!")
            print(f"   Rows: {len(data.get('data', []))}")
            return True
        else:
            print(f"❌ Small query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Small query error: {e}")
        return False

def check_backend_logs():
    """Remind user to check backend logs"""
    print(f"\n📋 Backend Log Checklist:")
    print(f"   🔍 Check your backend console for these log messages:")
    print(f"      - 'Setting up progress tracking for client: ...'")
    print(f"      - 'Executing query: ...'")
    print(f"      - 'Query limit from request: ...'")
    print(f"      - 'Checking query size. Max rows threshold: ...'")
    print(f"      - 'Getting row count with: ...'")
    print(f"      - 'Row count determined: ... rows'")
    print(f"      - 'Very large dataset detected (...), using chunked processing'")
    print(f"      - 'Starting chunked processing. Chunk size: ...'")
    print(f"\n   If you don't see these logs, the backend changes aren't active!")

def main():
    """Run QueryBuilder backend tests"""
    print("🚀 QueryBuilder Backend Test")
    print("=" * 50)
    
    # Login first
    print("\n🔐 Logging in...")
    token = login()
    if not token:
        print("❌ Failed to login. Please check credentials.")
        return 1
    
    print("✅ Login successful!")
    
    # Test 1: Small query (should work)
    if not test_smaller_query(token):
        print("❌ Even small queries are failing - basic backend issue")
        return 1
    
    # Test 2: Large query (the problematic one)
    success = test_query_execute_endpoint(token)
    
    # Always show log checklist
    check_backend_logs()
    
    if success:
        print("\n✅ Backend test completed successfully!")
        print("📝 If you still see 'ошибка выполнения запроса' in frontend:")
        print("   1. Check WebSocket connection in browser console")
        print("   2. Verify progress bar appears")
        print("   3. Check if temp file info is displayed")
    else:
        print("\n❌ Backend test failed!")
        print("📝 This confirms the issue is in the backend.")
        print("   Check the log messages above and backend console output.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())