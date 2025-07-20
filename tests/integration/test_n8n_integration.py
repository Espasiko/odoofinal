#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests de integración para la comunicación entre FastAPI y n8n.
Estos tests pueden ejecutarse como parte del pipeline CI/CD para verificar
que la integración funciona correctamente después de cambios en el código.
"""

import os
import sys
import unittest
import requests
import json
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración para los tests
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://localhost:5678")
API_TOKEN = os.getenv("API_TEST_TOKEN", "")  # Token para autenticación en FastAPI
N8N_API_TOKEN = os.getenv("N8N_API_KEY", "pelotazo-n8n-api-token-seguro-2025")

# Headers para las solicitudes
api_headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

n8n_headers = {
    "Authorization": f"Bearer {N8N_API_TOKEN}",
    "Content-Type": "application/json"
}

class TestN8nIntegration(unittest.TestCase):
    """Tests de integración para la comunicación entre FastAPI y n8n"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para los tests"""
        # Verificar que los servicios están disponibles
        cls._check_services_availability()
        
        # Obtener IDs de flujos de trabajo
        cls.workflow_ids = cls._get_workflow_ids()
    
    @classmethod
    def _check_services_availability(cls):
        """Verificar que los servicios están disponibles"""
        # Verificar FastAPI
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            assert response.status_code == 200, "FastAPI no está disponible"
            print("✅ FastAPI está disponible")
        except Exception as e:
            print(f"❌ Error al conectar con FastAPI: {str(e)}")
            sys.exit(1)
        
        # Verificar n8n
        try:
            response = requests.get(
                f"{N8N_BASE_URL}/api/v1/workflows", 
                headers=n8n_headers,
                timeout=5
            )
            assert response.status_code == 200, "n8n no está disponible o el token es inválido"
            print("✅ n8n está disponible")
        except Exception as e:
            print(f"❌ Error al conectar con n8n: {str(e)}")
            sys.exit(1)
    
    @classmethod
    def _get_workflow_ids(cls):
        """Obtener IDs de flujos de trabajo"""
        workflow_ids = {
            "ocr_mejorado": None,
            "llm_mcp_factura": None,
            "servidor_mcp": None
        }
        
        try:
            response = requests.get(
                f"{N8N_BASE_URL}/api/v1/workflows",
                headers=n8n_headers
            )
            
            if response.status_code == 200:
                workflows = response.json()
                
                for workflow in workflows:
                    name = workflow.get("name", "").lower()
                    
                    if "ocr mejorado" in name or "procesar_factura_ocr_mejorado" in name:
                        workflow_ids["ocr_mejorado"] = workflow.get("id")
                        print(f"✅ Flujo OCR mejorado encontrado: {workflow.get('id')}")
                    
                    elif ("llm" in name and "mcp" in name and "factura" in name) or "llm_mcp_client_factura" in name:
                        workflow_ids["llm_mcp_factura"] = workflow.get("id")
                        print(f"✅ Flujo LLM-MCP encontrado: {workflow.get('id')}")
                    
                    elif "servidor mcp" in name or "servidor_mcp_herramientas" in name:
                        workflow_ids["servidor_mcp"] = workflow.get("id")
                        print(f"✅ Flujo Servidor MCP encontrado: {workflow.get('id')}")
        
        except Exception as e:
            print(f"❌ Error al obtener IDs de flujos de trabajo: {str(e)}")
        
        return workflow_ids
    
    def test_01_api_connection(self):
        """Verificar la conexión entre FastAPI y n8n"""
        response = requests.get(
            f"{API_BASE_URL}/api/v1/n8n/status",
            headers=api_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "connected")
        print("✅ Test de conexión API-n8n superado")
    
    def test_02_list_workflows(self):
        """Verificar que se pueden listar los flujos de trabajo"""
        response = requests.get(
            f"{API_BASE_URL}/api/v1/n8n/workflows",
            headers=api_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("workflows", data)
        self.assertGreaterEqual(len(data["workflows"]), 1)
        print("✅ Test de listado de flujos superado")
    
    def test_03_execute_ocr_workflow(self):
        """Verificar que se puede ejecutar el flujo OCR"""
        # Omitir si no se encontró el flujo OCR
        if not self.workflow_ids["ocr_mejorado"]:
            self.skipTest("Flujo OCR no encontrado")
        
        # Datos de prueba para el flujo OCR
        test_data = {
            "supplier_name": "NEVIR",
            "supplier_vat": "B84201219",
            "test_mode": True  # Indicar que es un test para evitar crear facturas reales
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/n8n/execute/ocr",
            headers=api_headers,
            json=test_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        print("✅ Test de ejecución de flujo OCR superado")
    
    def test_04_execute_llm_mcp_workflow(self):
        """Verificar que se puede ejecutar el flujo LLM-MCP"""
        # Omitir si no se encontró el flujo LLM-MCP
        if not self.workflow_ids["llm_mcp_factura"]:
            self.skipTest("Flujo LLM-MCP no encontrado")
        
        # Datos de prueba para el flujo LLM-MCP
        test_data = {
            "invoice_text": "Factura NEVIR\nNúmero: NVR-12345\nFecha: 19/07/2025\nCIF: B84201219\nBase Imponible: 100€\nIVA (21%): 21€\nTotal: 121€",
            "test_mode": True  # Indicar que es un test para evitar crear facturas reales
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/n8n/execute/llm-mcp",
            headers=api_headers,
            json=test_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        print("✅ Test de ejecución de flujo LLM-MCP superado")
    
    def test_05_get_executions(self):
        """Verificar que se pueden obtener las ejecuciones"""
        response = requests.get(
            f"{API_BASE_URL}/api/v1/n8n/executions",
            headers=api_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("executions", data)
        print("✅ Test de obtención de ejecuciones superado")
    
    def test_06_activate_deactivate_workflow(self):
        """Verificar que se puede activar y desactivar un flujo de trabajo"""
        # Omitir si no se encontró el flujo OCR
        if not self.workflow_ids["ocr_mejorado"]:
            self.skipTest("Flujo OCR no encontrado")
        
        # Activar flujo
        response = requests.post(
            f"{API_BASE_URL}/api/v1/n8n/workflows/{self.workflow_ids['ocr_mejorado']}/activate",
            headers=api_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        
        # Esperar un momento para que se aplique el cambio
        time.sleep(1)
        
        # Desactivar flujo
        response = requests.post(
            f"{API_BASE_URL}/api/v1/n8n/workflows/{self.workflow_ids['ocr_mejorado']}/deactivate",
            headers=api_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        
        print("✅ Test de activación/desactivación de flujo superado")

def run_tests():
    """Ejecutar los tests"""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    print("=== Iniciando tests de integración FastAPI-n8n ===")
    run_tests()
    print("=== Tests de integración completados ===")
