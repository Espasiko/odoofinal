#!/bin/bash
echo "Testing all endpoints with authentication..."
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin_password_secure" | jq -r '.access_token')

echo "Token obtained: ${TOKEN:0:20}..."

echo "\n1. Testing providers endpoint:"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/providers/all | jq 'length'

echo "\n2. Testing products endpoint:"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/products/all | jq 'length'

echo "\n3. Available OCR endpoints:"
curl -s http://localhost:8000/docs | grep -o 'mistral-ocr[^"]*' | head -5

echo "\nDone."