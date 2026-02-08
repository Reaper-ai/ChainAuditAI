#!/usr/bin/env python3
import requests
import json
import time

# Wait for server to start
time.sleep(2)

print("Testing /test/run-test endpoint...")
print("-" * 50)

try:
    response = requests.post(
        'http://localhost:8000/test/run-test',
        json={
            'transaction_type': 'vehicle',
            'fraud_label': 'fraud'
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
    
except Exception as e:
    print(f"Error: {e}")
