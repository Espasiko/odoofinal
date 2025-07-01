#!/usr/bin/env python3
"""
Servidor FastAPI persistente para Odoo Middleware
"""

import uvicorn
import signal
import sys
import os
from pathlib import Path

def setup_signal_handlers():
    """Configurar manejadores de señales para cierre limpio"""
    def signal_handler(signum, frame):
        print("\n🛑 Recibida señal de cierre. Deteniendo servidor...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Función principal"""
    print("🚀 SERVIDOR FASTAPI PERSISTENTE")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not Path("main.py").exists():
        print("❌ Error: No se encuentra main.py en el directorio actual")
        print(f"📁 Directorio actual: {os.getcwd()}")
        return False
    
    # Configurar manejadores de señales
    setup_signal_handlers()
    
    print("📍 URL: http://localhost:8000")
    print("📍 Documentación: http://localhost:8000/docs")
    print("📍 Health Check: http://localhost:8000/health")
    print("⏹️  Presiona Ctrl+C para detener")
    print("-" * 50)
    
    try:
        # Ejecutar servidor directamente con uvicorn.run
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False,
            access_log=True,
            use_colors=True,
            loop="asyncio"
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
        return True
    except Exception as e:
        print(f"❌ Error ejecutando servidor: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()