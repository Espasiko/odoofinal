#!/usr/bin/env python3
import requests
import base64
import json

def test_mistral_chat():
    # Encode image to base64
    with open('/home/espasiko/mainmanusodoo/manusodoo-roto/ejemplos/BSH-balay.png', 'rb') as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # API request
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": "Bearer qlsBKB80fbxr7YQPg9VnMKAdIIZKA11m",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "pixtral-12b-2409",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all the text from this image using OCR."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:1000]}...")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_mistral_chat()
