#!/usr/bin/env python3
"""
Test script for large dataset queries (2.7M+ users)
Tests the improvements made to handle large datasets efficiently
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

def test_large_query(token, limit=2700000):
    """Test querying large dataset"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Query for 2.7M users
    query_data = {
        "database_id": "DSSB_APP",
        "table": "DSSB_DM.RB_CLIENTS",
        "columns": [],  # Get all columns
        "filters": [],
        "sort_by": None,
        "sort_order": "asc",
        "limit": limit
    }
    
    print(f"\n🔍 Testing query for {limit:,} records...")
    print("⏳ This may take several minutes for large datasets...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/query/execute",
            json=query_data,
            headers=headers,
            timeout=600  # 10 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Query successful!")
                print(f"   Total rows: {data.get('row_count', 0):,}")
                print(f"   Rows returned: {len(data.get('data', [])):,}")
                print(f"   Execution time: {data.get('execution_time', 'N/A')}")
                print(f"   Total duration: {duration:.2f} seconds")
                print(f"   Message: {data.get('message', '')}")
                
                # Check if pagination was applied
                if data.get('row_count', 0) > len(data.get('data', [])):
                    print(f"   ℹ️  Pagination applied: Showing {len(data.get('data', [])):,} of {data.get('row_count', 0):,} rows")
                
                return True
            else:
                print(f"❌ Query failed: {data.get('message', 'Unknown error')}")
                print(f"   Error: {data.get('error', '')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detail: {error_data.get('detail', 'No details')}")
            except:
                print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after {time.time() - start_time:.2f} seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False

def test_count_query(token):
    """Test counting rows (should be fast even for large datasets)"""
    headers = {"Authorization": f"Bearer {token}"}
    
    query_data = {
        "database_id": "DSSB_APP",
        "table": "DSSB_DM.RB_CLIENTS",
        "filters": []
    }
    
    print(f"\n📊 Testing row count...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/query/count",
            json=query_data,
            headers=headers,
            timeout=60  # 1 minute timeout for count
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Count successful!")
                print(f"   Total rows: {data.get('count', 0):,}")
                print(f"   Duration: {duration:.2f} seconds")
                return data.get('count', 0)
            else:
                print(f"❌ Count failed: {data.get('message', 'Unknown error')}")
                return 0
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text[:200]}")
            return 0
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return 0

def test_progressive_limits(token):
    """Test with progressively larger limits to find breaking point"""
    limits = [1000, 10000, 100000, 500000, 1000000, 2000000, 2700000]
    
    print("\n🔄 Testing progressive query limits...")
    
    for limit in limits:
        print(f"\n--- Testing limit: {limit:,} ---")
        success = test_large_query(token, limit)
        if not success:
            print(f"⚠️  Failed at limit: {limit:,}")
            break
        time.sleep(2)  # Small delay between tests

def main():
    """Run all tests"""
    print("🚀 Large Dataset Query Test Suite")
    print("=" * 50)
    
    # Login first
    print("\n🔐 Logging in...")
    token = login()
    if not token:
        print("❌ Failed to login. Please check credentials.")
        return 1
    
    print("✅ Login successful!")
    
    # Test 1: Count query (should be fast)
    total_count = test_count_query(token)
    
    # Test 2: Large query (2.7M rows)
    if total_count > 0:
        # Use actual count if available, otherwise use 2.7M
        test_limit = min(total_count, 2700000)
        test_large_query(token, test_limit)
    
    # Test 3: Progressive limits (optional - uncomment to run)
    # test_progressive_limits(token)
    
    print("\n✅ Test suite completed!")
    print("\n📋 Summary of improvements:")
    print("- Chunked processing for large datasets (50K rows per chunk)")
    print("- Pagination: Returns max 100K rows to frontend")
    print("- Better error messages for timeout/memory issues")
    print("- Progress indicators for queries > 1M rows")
    print("- Optimized cursor array size (10K)")
    print("- Full row count reported even when paginated")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())