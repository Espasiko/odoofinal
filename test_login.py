#!/usr/bin/env python3
import requests
import json

def test_login():
    url = 'http://localhost:8000/token'
    data = {
        'username': 'admin',
        'password': 'admin_password_secure'
    }
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"Token: {token_data.get('access_token', 'No token')}")
            return token_data.get('access_token')
        else:
            print("Login failed")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_dashboard_with_token(token):
    if not token:
        print("No token available")
        return
        
    url = 'http://localhost:8000/api/v1/dashboard/stats'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Dashboard Status Code: {response.status_code}")
        print(f"Dashboard Response: {response.text}")
    except Exception as e:
        print(f"Dashboard Error: {e}")

if __name__ == "__main__":
    print("Testing login...")
    token = test_login()
    
    print("\nTesting dashboard with token...")
    test_dashboard_with_token(token)