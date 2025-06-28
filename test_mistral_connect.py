import requests
import os

api_key = os.getenv("MISTRAL_LLM_API_KEY", "Dn11EQcZl36z7BghhcM3mfa8mrjI5Ko2")

try:
    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistral-large-latest",
            "messages": [{"role": "user", "content": "Hola, ¿puedes responder con un JSON de ejemplo de productos?"}],
            "temperature": 0.1,
            "max_tokens": 256
        },
        timeout=30
    )
    print("Status code:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
