"""
Test signup endpoint directly
"""
import requests
import json

url = "http://localhost:8001/api/v1/auth/signup"
payload = {
    "email": "test@example.com",
    "password": "testpassword123",
    "first_name": "Test",
    "last_name": "User"
}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
