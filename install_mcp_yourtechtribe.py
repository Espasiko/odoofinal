#!/usr/bin/env python3
"""
Script de instalación para el servidor MCP-Odoo de yourtechtribe
Este script configura e instala las dependencias necesarias para integrar
las funcionalidades de contabilidad y facturación de Odoo con agentes de IA.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Ejecuta un comando y maneja errores"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True, cwd=cwd)
        print(f"✓ {command}")
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error ejecutando: {command}")
        print(f"  Error: {e.stderr}")
        return False

def main():
    print("🚀 Instalando servidor MCP-Odoo de yourtechtribe...")
    
    # Directorio del proyecto
    project_dir = Path("/home/espasiko/mainmanusodoo/manusodoo-roto")
    mcp_dir = project_dir / "mcp-odoo-yourtechtribe"
    
    if not mcp_dir.exists():
        print(f"❌ Directorio {mcp_dir} no encontrado")
        return False
    
    print(f"📁 Trabajando en: {mcp_dir}")
    
    # Instalar dependencias de Python
    print("\n📦 Instalando dependencias de Python...")
    if not run_command("pip install -r requirements.txt", cwd=mcp_dir):
        print("❌ Error instalando dependencias")
        return False
    
    # Verificar archivo .env
    env_file = mcp_dir / ".env"
    if not env_file.exists():
        print("❌ Archivo .env no encontrado")
        print("   Asegúrate de configurar las credenciales de Odoo en .env")
        return False
    
    print("✓ Archivo .env encontrado")
    
    # Verificar que Odoo esté ejecutándose
    print("\n🔍 Verificando conexión a Odoo...")
    test_script = """
import sys
sys.path.append('.')
from odoo.client import OdooClient
from config import Config

try:
    config = Config()
    client = OdooClient(config)
    client.connect()
    version = client.get_server_version()
    print(f"✓ Conectado a Odoo versión: {version}")
    client.disconnect()
except Exception as e:
    print(f"❌ Error conectando a Odoo: {e}")
    sys.exit(1)
"""
    
    test_file = mcp_dir / "test_connection.py"
    with open(test_file, "w") as f:
        f.write(test_script)
    
    if not run_command("python test_connection.py", cwd=mcp_dir):
        print("❌ No se pudo conectar a Odoo")
        print("   Verifica que Odoo esté ejecutándose y las credenciales sean correctas")
        return False
    
    # Limpiar archivo de prueba
    test_file.unlink()
    
    print("\n🎉 ¡Instalación completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Iniciar el servidor MCP:")
    print(f"   cd {mcp_dir}")
    print("   python server.py")
    print("\n2. El servidor estará disponible en http://localhost:3001")
    print("\n3. Herramientas disponibles:")
    print("   - list_vendor_bills: Listar facturas de proveedores")
    print("   - list_customer_invoices: Listar facturas de clientes")
    print("   - list_payments: Listar pagos")
    print("   - get_invoice_details: Obtener detalles de factura")
    print("   - reconcile_invoices_and_payments: Reconciliar facturas y pagos")
    print("   - list_accounting_entries: Listar asientos contables")
    print("   - list_suppliers: Listar proveedores")
    print("   - list_customers: Listar clientes")
    print("   - find_entries_by_account: Buscar por cuenta contable")
    print("   - trace_account_flow: Rastrear flujo entre cuentas")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)