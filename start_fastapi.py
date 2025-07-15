#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de inicio robusto para FastAPI
Soluciona problemas de persistencia y estabilidad
"""

import uvicorn
import signal
import sys
import os
from pathlib import Path

def signal_handler(sig, frame):
    """Maneja señales de interrupción"""
    print('\n🛑 Deteniendo servidor FastAPI...')
    sys.exit(0)

def main():
    """Función principal para iniciar FastAPI"""
    # Registrar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configuración del servidor
    config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": False,  # Desactivar reload para mayor estabilidad
        "log_level": "info",
        "access_log": True,
        "workers": 1,
        "loop": "auto",
        "http": "auto"
    }
    
    print("🚀 Iniciando servidor FastAPI...")
    print(f"📍 URL: http://localhost:{config['port']}")
    print(f"📍 Documentación: http://localhost:{config['port']}/docs")
    print("⏹️  Presiona Ctrl+C para detener")
    print("-" * 50)
    
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error al iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()