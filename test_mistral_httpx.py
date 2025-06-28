import os
import httpx

api_key = os.getenv("MISTRAL_LLM_API_KEY", "Dn11EQcZl36z7BghhcM3mfa8mrjI5Ko2")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "model": "mistral-large-latest",
    "messages": [
        {"role": "user", "content": "Hola, ¿puedes responder con un JSON de ejemplo de productos?"}
    ],
    "temperature": 0.1,
    "max_tokens": 256
}

try:
    with httpx.Client(timeout=30) as client:
        response = client.post("https://api.mistral.ai/v1/chat/completions", json=data, headers=headers)
        print("Status code:", response.status_code)
        print("Response:", response.text)
except Exception as e:
    print("Error:", e)
