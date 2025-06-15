#!/usr/bin/env python3
import os
import sys
import traceback

# Configurar variables de entorno
os.environ['ODOO_URL'] = 'http://localhost:8069'
os.environ['ODOO_DB'] = 'postgres'
os.environ['ODOO_USERNAME'] = 'admin'
os.environ['ODOO_PASSWORD'] = 'admin'

print("=== TESTING ODOO MCP SERVER ===")
print(f"Python version: {sys.version}")
print("Environment variables:")
for key, value in os.environ.items():
    if key.startswith("ODOO_"):
        if key == "ODOO_PASSWORD":
            print(f"  {key}: ***hidden***")
        else:
            print(f"  {key}: {value}")

try:
    print("\n1. Importing odoo_mcp.server...")
    from odoo_mcp.server import mcp
    print("✓ Import successful")
    
    print("\n2. Checking MCP server object...")
    print(f"MCP object type: {type(mcp)}")
    print(f"Available methods: {[m for m in dir(mcp) if not m.startswith('_')]}")
    
    print("\n3. Testing Odoo client initialization...")
    from odoo_mcp.odoo_client import get_odoo_client
    odoo_client = get_odoo_client()
    print(f"✓ Odoo client created: {type(odoo_client)}")
    
    print("\n4. Testing Odoo connection...")
    # Intentar conectar manualmente
    odoo_client._connect()
    print(f"✓ Odoo connection successful, UID: {odoo_client.uid}")
    
    print("\n5. Testing MCP server run method...")
    print("This will start the MCP server (use Ctrl+C to stop)")
    mcp.run()
    
except KeyboardInterrupt:
    print("\n✓ Server stopped by user")
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()