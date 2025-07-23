#!/usr/bin/env python3
"""
Script de troubleshooting completo para n8n
Verifica conectividad, credenciales, workflows y genera reporte detallado
"""
import requests
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import subprocess

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

try:
    from api.utils.n8n_config import n8n_config
    CONFIG_LOADED = True
except ImportError as e:
    print(f"⚠️ No se pudo cargar la configuración: {e}")
    CONFIG_LOADED = False

class N8nTroubleshooter:
    def __init__(self):
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            },
            "recommendations": []
        }
        
        # URLs a probar
        self.test_urls = [
            "http://localhost:5678",
            "http://n8n:5678"
        ]
        
        # Configuración por defecto si no se puede cargar
        if CONFIG_LOADED:
            self.api_key = n8n_config.N8N_API_KEY
            self.api_url = n8n_config.N8N_API_URL
            self.webhook_url = n8n_config.N8N_WEBHOOK_URL
        else:
            self.api_key = os.getenv("N8N_API_KEY", "pelotazo-n8n-api-token-seguro-2025")
            self.api_url = "http://n8n:5678/api/v1"
            self.webhook_url = "http://n8n:5678/webhook"

    def add_test_result(self, test_name: str, status: str, message: str, details: Any = None):
        """Añadir resultado de test al reporte"""
        self.report["tests"].append({
            "name": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        self.report["summary"]["total_tests"] += 1
        if status == "PASS":
            self.report["summary"]["passed"] += 1
        elif status == "FAIL":
            self.report["summary"]["failed"] += 1
        elif status == "WARN":
            self.report["summary"]["warnings"] += 1

    def add_recommendation(self, recommendation: str):
        """Añadir recomendación al reporte"""
        self.report["recommendations"].append(recommendation)

    def test_docker_container(self) -> bool:
        """Verificar si el contenedor de n8n está ejecutándose"""
        print("🐳 Verificando contenedor Docker de n8n...")
        
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=n8n", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                lines = output.split('\n')
                
                if len(lines) > 1:  # Hay contenedores (primera línea es header)
                    container_info = lines[1]
                    if "Up" in container_info:
                        self.add_test_result(
                            "Docker Container Status",
                            "PASS",
                            f"Contenedor n8n ejecutándose: {container_info}",
                            {"container_info": container_info}
                        )
                        return True
                    else:
                        self.add_test_result(
                            "Docker Container Status",
                            "FAIL",
                            f"Contenedor n8n no está ejecutándose: {container_info}",
                            {"container_info": container_info}
                        )
                        self.add_recommendation("Ejecutar: docker-compose up -d n8n")
                        return False
                else:
                    self.add_test_result(
                        "Docker Container Status",
                        "FAIL",
                        "No se encontró contenedor n8n",
                        {"output": output}
                    )
                    self.add_recommendation("Verificar docker-compose.yml y ejecutar: docker-compose up -d")
                    return False
            else:
                self.add_test_result(
                    "Docker Container Status",
                    "FAIL",
                    f"Error ejecutando docker ps: {result.stderr}",
                    {"error": result.stderr}
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.add_test_result(
                "Docker Container Status",
                "FAIL",
                "Timeout ejecutando docker ps",
                None
            )
            return False
        except FileNotFoundError:
            self.add_test_result(
                "Docker Container Status",
                "WARN",
                "Docker no está instalado o no está en PATH",
                None
            )
            return False
        except Exception as e:
            self.add_test_result(
                "Docker Container Status",
                "FAIL",
                f"Error inesperado: {str(e)}",
                {"error": str(e)}
            )
            return False

    def test_basic_connectivity(self) -> Tuple[Optional[str], bool]:
        """Probar conectividad básica con n8n"""
        print("🌐 Probando conectividad básica con n8n...")
        
        for url in self.test_urls:
            try:
                print(f"  Probando: {url}")
                response = requests.get(f"{url}/healthz", timeout=5)
                
                if response.status_code == 200:
                    self.add_test_result(
                        f"Basic Connectivity ({url})",
                        "PASS",
                        f"n8n responde correctamente en {url}",
                        {"status_code": response.status_code, "response": response.text[:200]}
                    )
                    return url, True
                else:
                    self.add_test_result(
                        f"Basic Connectivity ({url})",
                        "WARN",
                        f"n8n responde con código {response.status_code}",
                        {"status_code": response.status_code, "response": response.text[:200]}
                    )
                    
            except requests.exceptions.ConnectionError:
                self.add_test_result(
                    f"Basic Connectivity ({url})",
                    "FAIL",
                    f"No se puede conectar a {url}",
                    {"error": "Connection refused"}
                )
            except requests.exceptions.Timeout:
                self.add_test_result(
                    f"Basic Connectivity ({url})",
                    "FAIL",
                    f"Timeout conectando a {url}",
                    {"error": "Timeout"}
                )
            except Exception as e:
                self.add_test_result(
                    f"Basic Connectivity ({url})",
                    "FAIL",
                    f"Error conectando a {url}: {str(e)}",
                    {"error": str(e)}
                )
        
        self.add_recommendation("Verificar que n8n esté ejecutándose y accesible en los puertos configurados")
        return None, False

    def test_api_authentication(self, base_url: str) -> bool:
        """Probar autenticación de la API"""
        print("🔐 Probando autenticación de la API...")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Probar endpoint de workflows
            api_url = base_url.replace(":5678", ":5678/api/v1")
            response = requests.get(f"{api_url}/workflows", headers=headers, timeout=10)
            
            if response.status_code == 200:
                workflows = response.json()
                self.add_test_result(
                    "API Authentication",
                    "PASS",
                    f"Autenticación exitosa. Encontrados {len(workflows)} workflows",
                    {"workflow_count": len(workflows), "api_key_prefix": self.api_key[:10] + "..."}
                )
                return True
            elif response.status_code == 401:
                self.add_test_result(
                    "API Authentication",
                    "FAIL",
                    "Error de autenticación. API key inválida",
                    {"status_code": 401, "api_key_prefix": self.api_key[:10] + "..."}
                )
                self.add_recommendation("Verificar la API key de n8n en las variables de entorno")
                return False
            else:
                self.add_test_result(
                    "API Authentication",
                    "FAIL",
                    f"Error de API: {response.status_code}",
                    {"status_code": response.status_code, "response": response.text[:200]}
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                "API Authentication",
                "FAIL",
                f"Error probando autenticación: {str(e)}",
                {"error": str(e)}
            )
            return False

    def test_workflows(self, base_url: str) -> List[Dict]:
        """Probar workflows disponibles"""
        print("📋 Analizando workflows disponibles...")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            api_url = base_url.replace(":5678", ":5678/api/v1")
            response = requests.get(f"{api_url}/workflows", headers=headers, timeout=10)
            
            if response.status_code == 200:
                workflows = response.json()
                
                # Analizar cada workflow
                workflow_analysis = []
                active_count = 0
                
                for workflow in workflows:
                    name = workflow.get("name", "Sin nombre")
                    workflow_id = workflow.get("id", "N/A")
                    active = workflow.get("active", False)
                    
                    if active:
                        active_count += 1
                    
                    # Obtener detalles del workflow
                    try:
                        detail_response = requests.get(
                            f"{api_url}/workflows/{workflow_id}",
                            headers=headers,
                            timeout=5
                        )
                        
                        if detail_response.status_code == 200:
                            details = detail_response.json()
                            node_count = len(details.get("nodes", []))
                            
                            workflow_info = {
                                "name": name,
                                "id": workflow_id,
                                "active": active,
                                "node_count": node_count,
                                "status": "OK"
                            }
                        else:
                            workflow_info = {
                                "name": name,
                                "id": workflow_id,
                                "active": active,
                                "node_count": 0,
                                "status": f"Error {detail_response.status_code}"
                            }
                    except:
                        workflow_info = {
                            "name": name,
                            "id": workflow_id,
                            "active": active,
                            "node_count": 0,
                            "status": "Error obteniendo detalles"
                        }
                    
                    workflow_analysis.append(workflow_info)
                
                self.add_test_result(
                    "Workflow Analysis",
                    "PASS",
                    f"Analizados {len(workflows)} workflows ({active_count} activos)",
                    {
                        "total_workflows": len(workflows),
                        "active_workflows": active_count,
                        "workflows": workflow_analysis
                    }
                )
                
                if active_count == 0:
                    self.add_recommendation("No hay workflows activos. Activar workflows necesarios desde la interfaz de n8n")
                
                return workflow_analysis
                
            else:
                self.add_test_result(
                    "Workflow Analysis",
                    "FAIL",
                    f"Error obteniendo workflows: {response.status_code}",
                    {"status_code": response.status_code}
                )
                return []
                
        except Exception as e:
            self.add_test_result(
                "Workflow Analysis",
                "FAIL",
                f"Error analizando workflows: {str(e)}",
                {"error": str(e)}
            )
            return []

    def test_webhook_endpoints(self, base_url: str):
        """Probar endpoints de webhook"""
        print("🪝 Probando endpoints de webhook...")
        
        webhook_base = base_url.replace(":5678", ":5678/webhook")
        
        # Endpoints comunes de webhook
        webhook_endpoints = [
            "procesar-factura",
            "analizar-factura",
            "procesar-factura-segura"
        ]
        
        for endpoint in webhook_endpoints:
            try:
                # Solo probar GET para verificar que el endpoint existe
                response = requests.get(f"{webhook_base}/{endpoint}", timeout=5)
                
                # Los webhooks normalmente devuelven 404 para GET, pero eso significa que existen
                if response.status_code in [200, 404, 405]:  # 405 = Method Not Allowed
                    self.add_test_result(
                        f"Webhook Endpoint ({endpoint})",
                        "PASS",
                        f"Endpoint webhook accesible: {webhook_base}/{endpoint}",
                        {"status_code": response.status_code}
                    )
                else:
                    self.add_test_result(
                        f"Webhook Endpoint ({endpoint})",
                        "WARN",
                        f"Endpoint webhook responde con código {response.status_code}",
                        {"status_code": response.status_code}
                    )
                    
            except requests.exceptions.ConnectionError:
                self.add_test_result(
                    f"Webhook Endpoint ({endpoint})",
                    "FAIL",
                    f"No se puede conectar al webhook {endpoint}",
                    {"error": "Connection refused"}
                )
            except Exception as e:
                self.add_test_result(
                    f"Webhook Endpoint ({endpoint})",
                    "FAIL",
                    f"Error probando webhook {endpoint}: {str(e)}",
                    {"error": str(e)}
                )

    def check_workflow_files(self):
        """Verificar archivos de workflow locales"""
        print("📁 Verificando archivos de workflow locales...")
        
        flows_dir = Path("/home/espasiko/mainmanusodoo/manusodoo-roto/n8n/flujos")
        
        if not flows_dir.exists():
            self.add_test_result(
                "Local Workflow Files",
                "FAIL",
                f"Directorio de flujos no encontrado: {flows_dir}",
                {"directory": str(flows_dir)}
            )
            return
        
        json_files = list(flows_dir.glob("*.json"))
        
        if not json_files:
            self.add_test_result(
                "Local Workflow Files",
                "WARN",
                "No se encontraron archivos JSON de workflows",
                {"directory": str(flows_dir)}
            )
            return
        
        valid_files = 0
        invalid_files = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    workflow = json.load(f)
                
                # Verificar estructura básica
                if "name" in workflow and "nodes" in workflow:
                    valid_files += 1
                else:
                    invalid_files.append(f"{json_file.name}: Estructura inválida")
                    
            except json.JSONDecodeError as e:
                invalid_files.append(f"{json_file.name}: Error JSON - {str(e)}")
            except Exception as e:
                invalid_files.append(f"{json_file.name}: Error - {str(e)}")
        
        if invalid_files:
            self.add_test_result(
                "Local Workflow Files",
                "WARN",
                f"Encontrados {valid_files} archivos válidos y {len(invalid_files)} con problemas",
                {
                    "valid_files": valid_files,
                    "invalid_files": invalid_files,
                    "total_files": len(json_files)
                }
            )
            self.add_recommendation("Corregir archivos de workflow con problemas usando fix_n8n_workflows.py")
        else:
            self.add_test_result(
                "Local Workflow Files",
                "PASS",
                f"Todos los {valid_files} archivos de workflow son válidos",
                {"valid_files": valid_files}
            )

    def generate_report(self):
        """Generar reporte final"""
        print("\n" + "=" * 60)
        print("📊 REPORTE DE TROUBLESHOOTING N8N")
        print("=" * 60)
        
        # Resumen
        summary = self.report["summary"]
        print(f"\n📈 RESUMEN:")
        print(f"  Total de pruebas: {summary['total_tests']}")
        print(f"  ✅ Exitosas: {summary['passed']}")
        print(f"  ❌ Fallidas: {summary['failed']}")
        print(f"  ⚠️ Advertencias: {summary['warnings']}")
        
        # Estado general
        if summary['failed'] == 0:
            if summary['warnings'] == 0:
                print(f"\n🎉 ESTADO: EXCELENTE - Todos los tests pasaron")
            else:
                print(f"\n✅ ESTADO: BUENO - Sin errores críticos, algunas advertencias")
        else:
            print(f"\n❌ ESTADO: PROBLEMAS DETECTADOS - {summary['failed']} errores críticos")
        
        # Detalles de tests fallidos
        failed_tests = [t for t in self.report["tests"] if t["status"] == "FAIL"]
        if failed_tests:
            print(f"\n❌ TESTS FALLIDOS:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['message']}")
        
        # Advertencias
        warning_tests = [t for t in self.report["tests"] if t["status"] == "WARN"]
        if warning_tests:
            print(f"\n⚠️ ADVERTENCIAS:")
            for test in warning_tests:
                print(f"  - {test['name']}: {test['message']}")
        
        # Recomendaciones
        if self.report["recommendations"]:
            print(f"\n💡 RECOMENDACIONES:")
            for i, rec in enumerate(self.report["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        # Guardar reporte detallado
        report_file = Path(f"n8n_troubleshoot_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte detallado guardado en: {report_file}")
        print("=" * 60)

    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 Iniciando troubleshooting completo de n8n...")
        
        # 1. Verificar contenedor Docker
        container_running = self.test_docker_container()
        
        # 2. Probar conectividad básica
        working_url, connectivity = self.test_basic_connectivity()
        
        if working_url and connectivity:
            # 3. Probar autenticación
            auth_working = self.test_api_authentication(working_url)
            
            if auth_working:
                # 4. Analizar workflows
                workflows = self.test_workflows(working_url)
                
                # 5. Probar webhooks
                self.test_webhook_endpoints(working_url)
        
        # 6. Verificar archivos locales
        self.check_workflow_files()
        
        # 7. Generar reporte
        self.generate_report()

def main():
    """Función principal"""
    troubleshooter = N8nTroubleshooter()
    troubleshooter.run_all_tests()

if __name__ == "__main__":
    main()
