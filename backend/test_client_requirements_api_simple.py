"""
Simple API test for client requirements endpoints
"""
import json
import requests
from io import BytesIO


def test_api_endpoints():
    """Test client requirements API endpoints"""
    base_url = "http://localhost:8000/api"
    
    try:
        # Test health check first
        health_response = requests.get("http://localhost:8000/health")
        if health_response.status_code != 200:
            print("Server not running. Please start the server first.")
            return
        
        print("Server is running, testing client requirements API...")
        
        # Test file upload
        requirements_data = {
            "requirements": [
                "Report on greenhouse gas emissions",
                "Disclose water usage metrics"
            ]
        }
        
        json_content = json.dumps(requirements_data)
        
        files = {
            "file": ("requirements.json", BytesIO(json_content.encode()), "application/json")
        }
        data = {
            "client_name": "Test Client Corp",
            "schema_type": "EU_ESRS_CSRD"
        }
        
        upload_response = requests.post(f"{base_url}/client-requirements/upload", files=files, data=data)
        
        if upload_response.status_code == 200:
            print("✓ File upload successful")
            result = upload_response.json()
            req_id = result["id"]
            print(f"  Created requirements with ID: {req_id}")
            
            # Test get requirements
            get_response = requests.get(f"{base_url}/client-requirements/{req_id}")
            if get_response.status_code == 200:
                print("✓ Get requirements successful")
            else:
                print(f"✗ Get requirements failed: {get_response.status_code}")
            
            # Test list requirements
            list_response = requests.get(f"{base_url}/client-requirements/")
            if list_response.status_code == 200:
                print("✓ List requirements successful")
                print(f"  Found {len(list_response.json())} requirements")
            else:
                print(f"✗ List requirements failed: {list_response.status_code}")
            
            # Test gap analysis
            gap_response = requests.get(f"{base_url}/client-requirements/{req_id}/gap-analysis")
            if gap_response.status_code == 200:
                print("✓ Gap analysis successful")
                gap_result = gap_response.json()
                print(f"  Coverage: {gap_result['coverage_percentage']}%")
            else:
                print(f"✗ Gap analysis failed: {gap_response.status_code}")
        
        else:
            print(f"✗ File upload failed: {upload_response.status_code}")
            print(f"  Error: {upload_response.text}")
    
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Please start the server with: python3 main.py")
    except Exception as e:
        print(f"Test failed with error: {e}")


if __name__ == "__main__":
    test_api_endpoints()