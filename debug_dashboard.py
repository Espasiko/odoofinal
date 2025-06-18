#!/usr/bin/env python3
import requests
import json
import traceback

def debug_dashboard():
    # Primero hacer login
    login_url = 'http://localhost:8001/token'
    login_data = {
        'username': 'admin',
        'password': 'admin_password_secure'
    }
    
    try:
        response = requests.post(login_url, data=login_data)
        if response.status_code != 200:
            print(f"Login failed: {response.status_code} - {response.text}")
            return
            
        token_data = response.json()
        token = token_data.get('access_token')
        print(f"Login successful, token: {token[:50]}...")
        
        # Ahora probar el dashboard
        dashboard_url = 'http://localhost:8001/api/v1/dashboard/stats'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        print("\nTesting dashboard...")
        response = requests.get(dashboard_url, headers=headers)
        print(f"Dashboard Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Dashboard data received successfully:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Dashboard error: {response.text}")
            
            # Intentar obtener más detalles del error
            try:
                error_data = response.json()
                print(f"Error detail: {error_data.get('detail', 'No detail available')}")
            except:
                print("Could not parse error response as JSON")
                
    except Exception as e:
        print(f"Exception occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_dashboard()