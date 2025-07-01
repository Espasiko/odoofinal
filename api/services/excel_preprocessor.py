import pandas as pd
from typing import List, Dict, Any, Optional
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelPreprocessor:
    """
    Pre-procesador robusto para archivos Excel de tarifas de proveedores.
    Utiliza el motor 'openpyxl' explícitamente para máxima compatibilidad.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path

    def process_file(self) -> Dict[str, Any]:
        logger.info(f"Iniciando pre-procesamiento para el archivo: {self.file_path}")
        
        try:
            # Forzamos el uso del motor 'openpyxl' para resolver ambigüedades
            xls = pd.ExcelFile(self.file_path, engine='openpyxl')
        except Exception as e:
            logger.error(f"No se pudo abrir el archivo Excel con el motor 'openpyxl'. Error: {e}")
            # Relanzamos el error para que la API devuelva un 500 claro.
            raise ValueError("El archivo no pudo ser procesado como un fichero Excel válido.") from e

        all_sheets_data = []
        sheet_names = xls.sheet_names
        rule_sheet_name = self._find_rule_sheet(sheet_names)
        business_rules = self._extract_rules(rule_sheet_name) if rule_sheet_name else {}
        
        product_sheet_names = [name for name in sheet_names if name != rule_sheet_name]

        for sheet_name in product_sheet_names:
            logger.info(f"Procesando hoja: '{sheet_name}'")
            df_probe = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            header_row = self._find_header_row(df_probe)
            
            if header_row is not None:
                df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
                all_sheets_data.extend(self._clean_and_extract_data(df))
            else:
                logger.warning(f"No se encontró cabecera en la hoja '{sheet_name}', se omitirá.")

        logger.info(f"Pre-procesamiento completado. {len(all_sheets_data)} filas de datos extraídas.")
        return {
            "provider_name": "(detectado o inferido)",
            "raw_data": all_sheets_data,
            "business_rules": business_rules
        }

    def _clean_and_extract_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Limpia un DataFrame, reemplaza NaN por None y extrae sus datos."""
        df.dropna(axis='columns', how='all', inplace=True)
        df.rename(columns=lambda c: str(c).strip(), inplace=True)
        df.columns = [f'columna_sin_nombre_{i+1}' if 'Unnamed' in str(col) else col for i, col in enumerate(df.columns)]
        df.dropna(how='all', inplace=True)

        # Reemplazar np.nan con None. Pandas usa np.nan para valores numéricos faltantes.
        # .replace es a menudo más directo que .where para este caso de uso.
        df_cleaned = df.replace(np.nan, None)

        return df_cleaned.to_dict('records')

    def _find_rule_sheet(self, sheet_names: List[str]) -> Optional[str]:
        """Busca una hoja que contenga reglas de negocio."""
        for sheet_name in sheet_names:
            if any(keyword in sheet_name.lower() for keyword in ['reglas', 'calculo', 'tarifa']):
                logger.info(f"Hoja de reglas encontrada: '{sheet_name}'")
                return sheet_name
        return None

    def _extract_rules(self, sheet_name: str) -> Dict[str, Any]:
        """Extrae las reglas de negocio de la hoja especificada (Placeholder)."""
        logger.info(f"Extrayendo reglas de la hoja: '{sheet_name}'")
        return {"description": "Reglas extraídas de la hoja", "details": "(implementación pendiente)"}

    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """Encuentra dinámicamente el ÍNDICE de la fila de la cabecera."""
        for i in range(min(20, len(df))):
            row = df.iloc[i]
            potential_headers = sum(1 for item in row if isinstance(item, str) and item.strip())
            if potential_headers >= 3:
                logger.info(f"Fila de cabecera candidata encontrada en el índice: {i}")
                return i
        logger.warning("No se pudo detectar una fila de cabecera clara.")
        return None
