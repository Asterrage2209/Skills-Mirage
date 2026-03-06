import requests
import sys
import json
import time

API_URL = "http://localhost:8000/auth"

# Generate unique email per test
test_email = f"test_{int(time.time())}@example.com"

signup_payload = {
    "email": test_email,
    "name": "Test User",
    "password": "hashedpassword123",
    "job_role": "Backend Engineer",
    "city": "Mumbai",
    "years_of_experience": 5,
    "role_description": "API architect handling databases"
}

try:
    # 1. Signup
    print("Testing /auth/signup...")
    r1 = requests.post(f"{API_URL}/signup", json=signup_payload)
    print(r1.status_code, r1.text)
    if r1.status_code != 201:
        print("Signup failed.")
        sys.exit(1)

    # 2. Login
    print("\nTesting /auth/login...")
    r2 = requests.post(f"{API_URL}/login", json={"email": test_email, "password": "hashedpassword123"})
    print(r2.status_code, r2.text)
    if r2.status_code != 200:
        print("Login failed.")
        sys.exit(1)
        
    token = r2.json().get("access_token")
    
    # 3. Get Me
    print("\nTesting /auth/me...")
    headers = {"Authorization": f"Bearer {token}"}
    r3 = requests.get(f"{API_URL}/me", headers=headers)
    print(r3.status_code, json.dumps(r3.json(), indent=2))
    
    print("\nAll Auth checks passed.")
    sys.exit(0)
except Exception as e:
    print("Request failed:", str(e))
    sys.exit(1)
