#!/usr/bin/env python3
"""
Test script for Order Assignments API endpoints
This script tests the order assignment functionality
"""

import requests
import json
import os
from pathlib import Path

# API base URLs
ASSIGNMENTS_BASE_URL = "http://localhost:8000/api/assignments"
ORDERS_BASE_URL = "http://localhost:8000/api/orders"

def test_accept_order(access_token):
    """Test accepting an order endpoint"""
    print("Testing Accept Order...")
    
    # Test data
    accept_data = {
        "order_id": 1  # Assuming order ID 1 exists
    }
    
    try:
        # Make request
        response = requests.post(
            f"{ASSIGNMENTS_BASE_URL}/acceptorder",
            json=accept_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Accept order successful!")
            return response.json().get("id")
        else:
            print("❌ Accept order failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error during accept order: {str(e)}")
        return None


def test_get_assignment(access_token, assignment_id):
    """Test getting assignment by ID endpoint"""
    print(f"\nTesting Get Assignment (ID: {assignment_id})...")
    
    try:
        # Make request
        response = requests.get(
            f"{ASSIGNMENTS_BASE_URL}/{assignment_id}",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get assignment successful!")
            return True
        else:
            print("❌ Get assignment failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during get assignment: {str(e)}")
        return False


def test_update_assignment_status(access_token, assignment_id):
    """Test updating assignment status endpoint"""
    print(f"\nTesting Update Assignment Status (ID: {assignment_id})...")
    
    # Test data
    status_data = {
        "assignment_status": "ASSIGNED"
    }
    
    try:
        # Make request
        response = requests.patch(
            f"{ASSIGNMENTS_BASE_URL}/{assignment_id}/status",
            json=status_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Update assignment status successful!")
            return True
        else:
            print("❌ Update assignment status failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during update assignment status: {str(e)}")
        return False


def test_cancel_assignment(access_token, assignment_id):
    """Test cancelling assignment endpoint"""
    print(f"\nTesting Cancel Assignment (ID: {assignment_id})...")
    
    try:
        # Make request
        response = requests.patch(
            f"{ASSIGNMENTS_BASE_URL}/{assignment_id}/cancel",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Cancel assignment successful!")
            return True
        else:
            print("❌ Cancel assignment failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during cancel assignment: {str(e)}")
        return False


def test_get_assignments_by_vehicle_owner(access_token, vehicle_owner_id):
    """Test getting assignments by vehicle owner endpoint"""
    print(f"\nTesting Get Assignments by Vehicle Owner (ID: {vehicle_owner_id})...")
    
    try:
        # Make request
        response = requests.get(
            f"{ASSIGNMENTS_BASE_URL}/vehicle_owner/{vehicle_owner_id}",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get assignments by vehicle owner successful!")
            return True
        else:
            print("❌ Get assignments by vehicle owner failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during get assignments by vehicle owner: {str(e)}")
        return False


def test_get_assignments_by_order(access_token, order_id):
    """Test getting assignments by order endpoint"""
    print(f"\nTesting Get Assignments by Order (ID: {order_id})...")
    
    try:
        # Make request
        response = requests.get(
            f"{ASSIGNMENTS_BASE_URL}/order/{order_id}",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get assignments by order successful!")
            return True
        else:
            print("❌ Get assignments by order failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during get assignments by order: {str(e)}")
        return False


def test_get_vendor_orders_with_assignments(access_token):
    """Test getting vendor orders with assignments endpoint"""
    print("\nTesting Get Vendor Orders with Assignments...")
    
    try:
        # Make request
        response = requests.get(
            f"{ORDERS_BASE_URL}/vendor/with-assignments",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get vendor orders with assignments successful!")
            return True
        else:
            print("❌ Get vendor orders with assignments failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during get vendor orders with assignments: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting Order Assignments API Tests...")
    print("=" * 50)
    
    # You need to provide a valid access token for testing
    # This should be obtained from a successful login
    access_token = input("Enter a valid access token for testing: ").strip()
    
    if not access_token:
        print("❌ No access token provided. Exiting...")
        return
    
    # Test accept order
    assignment_id = test_accept_order(access_token)
    
    if assignment_id:
        # Test get assignment
        test_get_assignment(access_token, assignment_id)
        
        # Test update assignment status
        test_update_assignment_status(access_token, assignment_id)
        
        # Test cancel assignment
        test_cancel_assignment(access_token, assignment_id)
    
    # Test other endpoints (these might fail if no assignments exist)
    # Extract vehicle_owner_id from token or use a default value
    vehicle_owner_id = "test-uuid"  # Replace with actual UUID from token
    test_get_assignments_by_vehicle_owner(access_token, vehicle_owner_id)
    
    test_get_assignments_by_order(access_token, 1)  # Assuming order ID 1 exists
    
    # Test vendor orders with assignments
    test_get_vendor_orders_with_assignments(access_token)
    
    print("\n" + "=" * 50)
    print("🏁 Order Assignments API Tests Completed!")


if __name__ == "__main__":
    main()
