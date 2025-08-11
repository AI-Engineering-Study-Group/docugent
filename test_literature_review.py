#!/usr/bin/env python3
"""
Test script for Literature Review functionality.
"""

import requests
import json
import os
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000/api/v1/literature"

def test_literature_review_endpoints():
    """Test the literature review API endpoints."""
    
    print("🧪 Testing Literature Review API Endpoints")
    print("=" * 50)
    
    # Test 1: List PDFs (should be empty initially)
    print("\n1. Testing list PDFs endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/list-pdfs")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {data.get('total_count', 0)} PDFs")
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Search PDFs (should work even with no PDFs)
    print("\n2. Testing search endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/search?query=test")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Search completed")
            print(f"   Found {data.get('total_matches', 0)} matches")
        else:
            print(f"❌ Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Ask question (should return placeholder)
    print("\n3. Testing ask question endpoint...")
    try:
        form_data = {"question": "What is this document about?"}
        response = requests.post(f"{BASE_URL}/ask-question", data=form_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Question answered")
            print(f"   Answer: {data.get('answer', 'No answer')[:100]}...")
        else:
            print(f"❌ Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Upload endpoint (test with invalid file)
    print("\n4. Testing upload endpoint with invalid file...")
    try:
        # Create a dummy file
        test_file_path = "test_dummy.txt"
        with open(test_file_path, "w") as f:
            f.write("This is not a PDF file")
        
        with open(test_file_path, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/upload-pdf", files=files)
        
        # Clean up
        os.remove(test_file_path)
        
        if response.status_code == 400:
            print("✅ Success: Correctly rejected non-PDF file")
        else:
            print(f"❌ Unexpected: Status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Literature Review API Tests Completed!")
    print("\n📝 Next Steps:")
    print("1. Start the application: docker-compose up --build")
    print("2. Access the frontend: http://localhost:2025")
    print("3. Navigate to 'Literature Review' in the sidebar")
    print("4. Upload a PDF and test the functionality")

if __name__ == "__main__":
    test_literature_review_endpoints()
