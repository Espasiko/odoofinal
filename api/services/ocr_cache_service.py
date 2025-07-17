"""
Servicio de caché para OCR
Este módulo proporciona funciones para cachear resultados de OCR y evitar reprocesamiento
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import datetime

logger = logging.getLogger(__name__)

class OCRCacheService:
    """Clase para gestionar el caché de resultados OCR"""
    
    def __init__(self, cache_dir: Union[str, Path] = None):
        """
        Inicializa el servicio de caché
        
        Args:
            cache_dir: Directorio para almacenar el caché, por defecto usa api/ocr_cache
        """
        if cache_dir is None:
            # Usar directorio por defecto
            self.cache_dir = Path(__file__).parent.parent / 'ocr_cache'
        else:
            self.cache_dir = Path(cache_dir)
            
        # Crear directorio si no existe
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Servicio de caché OCR inicializado en {self.cache_dir}")
        
    def generate_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Genera un hash único para un archivo
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            str: Hash SHA-256 del archivo
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe")
            
        # Generar hash SHA-256 del contenido del archivo
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Leer en bloques de 4K para archivos grandes
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return sha256_hash.hexdigest()
        
    def get_cache_path(self, file_hash: str) -> Path:
        """
        Obtiene la ruta al archivo de caché para un hash
        
        Args:
            file_hash: Hash del archivo
            
        Returns:
            Path: Ruta al archivo de caché
        """
        return self.cache_dir / f"{file_hash}.json"
        
    def is_in_cache(self, file_path: Union[str, Path]) -> bool:
        """
        Verifica si un archivo ya está en caché
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            bool: True si el archivo está en caché
        """
        try:
            file_hash = self.generate_file_hash(file_path)
            cache_path = self.get_cache_path(file_hash)
            return cache_path.exists()
        except Exception as e:
            logger.error(f"Error verificando caché para {file_path}: {e}")
            return False
            
    def get_from_cache(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Obtiene los resultados OCR desde el caché
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Optional[Dict[str, Any]]: Datos del caché o None si no existe
        """
        try:
            file_hash = self.generate_file_hash(file_path)
            cache_path = self.get_cache_path(file_hash)
            
            if not cache_path.exists():
                return None
                
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            logger.info(f"Datos recuperados del caché para {file_path}")
            return cache_data
        except Exception as e:
            logger.error(f"Error obteniendo datos del caché para {file_path}: {e}")
            return None
            
    def save_to_cache(self, file_path: Union[str, Path], ocr_data: Dict[str, Any]) -> bool:
        """
        Guarda resultados OCR en el caché
        
        Args:
            file_path: Ruta al archivo original
            ocr_data: Datos OCR a guardar
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            file_hash = self.generate_file_hash(file_path)
            cache_path = self.get_cache_path(file_hash)
            
            # Añadir metadatos de caché
            cache_data = ocr_data.copy()
            cache_data['cache_metadata'] = {
                'original_file': str(file_path),
                'file_hash': file_hash,
                'cached_at': datetime.datetime.now().isoformat(),
                'cache_version': '1.0'
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Datos guardados en caché para {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error guardando datos en caché para {file_path}: {e}")
            return False
            
    def invalidate_cache(self, file_path: Union[str, Path]) -> bool:
        """
        Invalida el caché para un archivo
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            bool: True si se invalidó correctamente
        """
        try:
            file_hash = self.generate_file_hash(file_path)
            cache_path = self.get_cache_path(file_hash)
            
            if cache_path.exists():
                os.remove(cache_path)
                logger.info(f"Caché invalidado para {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error invalidando caché para {file_path}: {e}")
            return False
            
    def clear_cache(self) -> int:
        """
        Limpia todo el caché
        
        Returns:
            int: Número de archivos eliminados
        """
        try:
            count = 0
            for cache_file in self.cache_dir.glob("*.json"):
                os.remove(cache_file)
                count += 1
                
            logger.info(f"Caché limpiado: {count} archivos eliminados")
            return count
        except Exception as e:
            logger.error(f"Error limpiando caché: {e}")
            return 0

# Instancia global del servicio de caché
ocr_cache_service = OCRCacheService()
