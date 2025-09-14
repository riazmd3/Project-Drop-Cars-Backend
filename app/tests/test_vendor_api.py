#!/usr/bin/env python3
"""
Test script for Vendor API endpoints
This script tests the vendor signup and signin functionality
"""

import requests
import json
import os
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000/api/users"

def test_vendor_signup():
    """Test vendor signup endpoint"""
    print("Testing Vendor Signup...")
    
    # Test data
    signup_data = {
        "full_name": "Test Vendor",
        "primary_number": "9876543213",
        "secondary_number": "9876543214",
        "password": "test123",
        "address": "Test Address, Test City, Test State 123456",
        "aadhar_number": "111111111111",
        "gpay_number": "9876543215",
        "organization_id": "TEST_ORG_001"
    }
    
    # Create a dummy image file for testing
    test_image_path = "test_aadhar.jpg"
    with open(test_image_path, "wb") as f:
        f.write(b"fake image data")
    
    try:
        # Prepare form data
        files = {
            'aadhar_image': ('test_aadhar.jpg', open(test_image_path, 'rb'), 'image/jpeg')
        }
        
        # Make request
        response = requests.post(
            f"{BASE_URL}/vendor/signup",
            data=signup_data,
            files=files
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Vendor signup successful!")
            return response.json().get("access_token")
        else:
            print("❌ Vendor signup failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error during signup: {str(e)}")
        return None
    finally:
        # Clean up test file
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

def test_vendor_signin():
    """Test vendor signin endpoint"""
    print("\nTesting Vendor Signin...")
    
    # Test data
    signin_data = {
        "primary_number": "9876543213",
        "password": "test123"
    }
    
    try:
        # Make request
        response = requests.post(
            f"{BASE_URL}/vendor/signin",
            json=signin_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Vendor signin successful!")
            return response.json().get("access_token")
        else:
            print("❌ Vendor signin failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error during signin: {str(e)}")
        return None

def test_vendor_signup_without_image():
    """Test vendor signup without image"""
    print("\nTesting Vendor Signup (without image)...")
    
    # Test data
    signup_data = {
        "full_name": "Test Vendor No Image",
        "primary_number": "9876543216",
        "secondary_number": "9876543217",
        "password": "test123",
        "address": "Test Address No Image, Test City, Test State 123456",
        "aadhar_number": "222222222222",
        "gpay_number": "9876543218",
        "organization_id": "TEST_ORG_002"
    }
    
    try:
        # Make request without image
        response = requests.post(
            f"{BASE_URL}/vendor/signup",
            data=signup_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Vendor signup without image successful!")
            return True
        else:
            print("❌ Vendor signup without image failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during signup without image: {str(e)}")
        return False

def test_duplicate_vendor():
    """Test duplicate vendor registration"""
    print("\nTesting Duplicate Vendor Registration...")
    
    # Test data (same as first test)
    signup_data = {
        "full_name": "Test Vendor Duplicate",
        "primary_number": "9876543213",  # Same number as first test
        "password": "test123",
        "address": "Test Address Duplicate, Test City, Test State 123456",
        "aadhar_number": "333333333333",
        "gpay_number": "9876543219",
        "organization_id": "TEST_ORG_003"
    }
    
    try:
        # Make request
        response = requests.post(
            f"{BASE_URL}/vendor/signup",
            data=signup_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("✅ Duplicate vendor detection working!")
            return True
        else:
            print("❌ Duplicate vendor detection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during duplicate test: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Vendor API Tests...\n")
    
    # Test 1: Vendor signup with image
    token1 = test_vendor_signup()
    
    # Test 2: Vendor signin
    token2 = test_vendor_signin()
    
    # Test 3: Vendor signup without image
    test_vendor_signup_without_image()
    
    # Test 4: Duplicate vendor registration
    test_duplicate_vendor()
    
    print("\n🎉 Vendor API Tests Completed!")
    
    if token1 and token2:
        print("✅ All core functionality working!")
    else:
        print("❌ Some tests failed. Check the server logs.")

if __name__ == "__main__":
    main()
