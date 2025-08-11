#!/usr/bin/env python3
"""
Test script to simulate PDF upload and check response structure.
"""

import requests
import os

def test_upload():
    """Test the upload endpoint with a dummy PDF."""
    
    print("🧪 Testing PDF Upload Endpoint")
    print("=" * 40)
    
    # Create a dummy PDF file
    dummy_pdf = "test_dummy.pdf"
    with open(dummy_pdf, "wb") as f:
        # Write some dummy PDF content
        f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF\n")
    
    try:
        # Test upload
        with open(dummy_pdf, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = requests.post("http://localhost:8000/api/v1/literature/upload-pdf", files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Upload successful!")
            print(f"Response structure: {data}")
            print(f"Success field: {data.get('success')}")
            print(f"Message: {data.get('message')}")
        else:
            print(f"\n❌ Upload failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up
        if os.path.exists(dummy_pdf):
            os.remove(dummy_pdf)

if __name__ == "__main__":
    test_upload()
