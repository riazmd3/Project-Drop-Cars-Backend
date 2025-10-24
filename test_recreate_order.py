#!/usr/bin/env python3
"""
Test script for the recreate order API functionality.
This script tests the recreate order endpoint with different scenarios.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on different port
API_ENDPOINT = f"{BASE_URL}/api/v1/new-orders/recreate"

def test_recreate_order():
    """Test the recreate order API endpoint"""
    
    # Test data - you'll need to replace these with actual values from your database
    test_cases = [
        {
            "name": "Test recreate with valid order ID",
            "order_id": 1,  # Replace with actual auto_cancelled order ID
            "expected_status": 201
        },
        {
            "name": "Test recreate with non-existent order ID",
            "order_id": 99999,
            "expected_status": 400
        },
        {
            "name": "Test recreate with order not belonging to vendor",
            "order_id": 2,  # Replace with order ID from different vendor
            "expected_status": 400
        },
        {
            "name": "Test recreate with non-auto_cancelled order",
            "order_id": 3,  # Replace with order ID that's not auto_cancelled
            "expected_status": 400
        }
    ]
    
    print("Testing Recreate Order API")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Order ID: {test_case['order_id']}")
        
        # Prepare request payload
        payload = {
            "order_id": test_case['order_id']
        }
        
        try:
            # Make API request
            # Note: You'll need to include proper authentication headers
            headers = {
                "Content-Type": "application/json",
                # Add your authentication token here
                # "Authorization": "Bearer YOUR_TOKEN_HERE"
            }
            
            response = requests.post(
                API_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Expected: {test_case['expected_status']}")
            
            if response.status_code == test_case['expected_status']:
                print("✅ PASS")
            else:
                print("❌ FAIL")
            
            # Print response details
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response Text: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ REQUEST ERROR: {e}")
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
        
        print("-" * 30)

def test_api_structure():
    """Test the API structure and validate the endpoint exists"""
    print("\nTesting API Structure")
    print("=" * 50)
    
    try:
        # Test if the endpoint exists (without authentication)
        response = requests.post(
            API_ENDPOINT,
            json={"order_id": 1},
            timeout=5
        )
        
        print(f"Endpoint Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Endpoint exists (authentication required)")
        elif response.status_code == 422:
            print("✅ Endpoint exists (validation error)")
        else:
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Endpoint not accessible: {e}")

if __name__ == "__main__":
    print("Recreate Order API Test Suite")
    print("=" * 50)
    print(f"Testing endpoint: {API_ENDPOINT}")
    print(f"Timestamp: {datetime.now()}")
    
    # Test API structure first
    test_api_structure()
    
    # Test recreate order functionality
    test_recreate_order()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    print("\nNote: To run actual tests, you need to:")
    print("1. Start your FastAPI server")
    print("2. Replace test order IDs with actual values from your database")
    print("3. Add proper authentication headers")
    print("4. Ensure you have auto_cancelled orders in your database")
