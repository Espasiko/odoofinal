# Integración de Facturación con Verifactu y Automatización de Facturas

## 1. Visión General de la Integración

La integración de facturación con Verifactu y la automatización del procesamiento de facturas constituye un componente crítico del sistema. Esta integración permitirá:

- Automatizar la captura y procesamiento de facturas de proveedores
- Generar facturas electrónicas conformes a la normativa fiscal
- Validar y verificar facturas mediante servicios externos
- Mantener un registro centralizado y trazable de todas las operaciones

```
┌─────────────────┐     ┌─────────────────────────┐     ┌─────────────────┐
│                 │     │                         │     │                 │
│  Dashboard      │     │  Middleware             │     │  Odoo           │
│  (Refine)       │◄───►│  (FastAPI)             │◄───►│  (Módulos de    │
│                 │     │                         │     │   Facturación)  │
└─────────────────┘     └─────────────────────────┘     └─────────────────┘
                              ▲           ▲
                              │           │
                              ▼           ▼
                        ┌─────────┐ ┌────────────┐     ┌─────────────┐
                        │         │ │            │     │             │
                        │  OCR    │ │ Verifactu  │◄───►│  Autoridad  │
                        │ Service │ │ Connector  │     │   Fiscal    │
                        │         │ │            │     │             │
                        └─────────┘ └────────────┘     └─────────────┘
```

## 2. Componentes de la Integración

### 2.1 Servicio OCR para Facturas

#### 2.1.1 Funcionalidades
- **Captura de documentos**: Escaneo o carga de facturas en papel o PDF
- **Preprocesamiento de imágenes**: Mejora de calidad, rotación, recorte
- **Extracción de texto**: Conversión de imágenes a texto mediante Tesseract OCR
- **Identificación de campos clave**:
  - Datos del proveedor (NIF, nombre, dirección)
  - Información de factura (número, fecha, vencimiento)
  - Líneas de productos/servicios
  - Importes (base imponible, IVA, total)
- **Validación de datos**: Verificación de formatos y coherencia

#### 2.1.2 Implementación Técnica
- **Biblioteca principal**: Tesseract OCR con Python
- **Preprocesamiento**: OpenCV para mejora de imágenes
- **Análisis estructurado**: Algoritmos de ML para identificación de campos
- **Validación**: Reglas de negocio y validaciones fiscales
- **Almacenamiento temporal**: Caché de documentos procesados

### 2.2 Conector Verifactu

#### 2.2.1 Funcionalidades
- **Autenticación con Verifactu**: Gestión de credenciales y tokens
- **Envío de facturas**: Transmisión de datos estructurados a Verifactu
- **Recepción de confirmaciones**: Procesamiento de respuestas
- **Gestión de errores**: Manejo de rechazos y excepciones
- **Seguimiento de estado**: Monitorización del ciclo de vida de la factura

#### 2.2.2 Implementación Técnica
- **Cliente API**: Integración con la API REST de Verifactu
- **Serialización**: Conversión de modelos de datos a formato requerido
- **Firma digital**: Implementación de mecanismos de firma según requisitos
- **Gestión de certificados**: Almacenamiento seguro de certificados digitales
- **Registro de transacciones**: Log detallado de todas las comunicaciones

### 2.3 Módulos Personalizados de Odoo

#### 2.3.1 Funcionalidades
- **Modelo extendido de facturas**: Campos adicionales para trazabilidad
- **Flujos de trabajo personalizados**: Estados específicos para el proceso
- **Reglas de validación**: Verificaciones adicionales según normativa
- **Reportes personalizados**: Formatos específicos para facturas
- **Integración con contabilidad**: Asientos automáticos

#### 2.3.2 Implementación Técnica
- **Herencia de modelos**: Extensión de modelos estándar de Odoo
- **Vistas personalizadas**: Interfaces adaptadas al proceso
- **Acciones automatizadas**: Triggers para eventos específicos
- **Reglas de acceso**: Permisos granulares por rol
- **Hooks de integración**: Puntos de extensión para el middleware

## 3. Flujos de Trabajo

### 3.1 Procesamiento de Facturas de Proveedores

1. **Captura de la factura**:
   - El usuario sube la factura (PDF/imagen) a través del dashboard
   - Alternativamente, se configura un correo electrónico para recepción automática

2. **Procesamiento OCR**:
   - El servicio OCR analiza el documento
   - Se extraen todos los campos relevantes
   - Se genera una estructura de datos preliminar

3. **Validación inicial**:
   - Verificación de formato y completitud
   - Validación de datos fiscales (NIF, importes, impuestos)
   - Identificación del proveedor en el sistema

4. **Enriquecimiento de datos**:
   - Asociación con órdenes de compra existentes
   - Verificación de precios y condiciones acordadas
   - Clasificación contable automática

5. **Aprobación (opcional)**:
   - Notificación a responsables para revisión
   - Interfaz de aprobación con comparativa de datos
   - Registro de aprobaciones y comentarios

6. **Registro en Odoo**:
   - Creación de la factura en el sistema
   - Generación de asientos contables
   - Programación de pagos según vencimiento

7. **Archivo digital**:
   - Almacenamiento del documento original
   - Vinculación con el registro en el sistema
   - Indexación para búsqueda futura

### 3.2 Emisión de Facturas a Clientes

1. **Creación de factura**:
   - Generación manual desde ventas
   - Creación automática desde pedidos
   - Facturación periódica programada

2. **Validación fiscal**:
   - Verificación de datos del cliente
   - Cálculo correcto de impuestos
   - Aplicación de retenciones si procede

3. **Generación de factura electrónica**:
   - Preparación de datos para Verifactu
   - Conversión al formato requerido
   - Firma digital según normativa

4. **Envío a Verifactu**:
   - Transmisión segura de datos
   - Recepción de acuse de recibo
   - Gestión de errores y reintentos

5. **Actualización de estado**:
   - Registro de confirmaciones oficiales
   - Actualización del estado en Odoo
   - Notificación a usuarios relevantes

6. **Distribución al cliente**:
   - Envío automático por email
   - Disponibilidad en portal de clientes
   - Opciones de descarga en múltiples formatos

7. **Seguimiento y conciliación**:
   - Monitorización de pagos recibidos
   - Conciliación automática con extractos bancarios
   - Gestión de impagos y recordatorios

## 4. Integración con Verifactu

### 4.1 Requisitos Técnicos

- **API Key**: Credenciales de acceso a la API de Verifactu
- **Certificado digital**: Para firma de facturas electrónicas
- **Endpoints**: URLs de producción y pruebas
- **Formatos**: Especificaciones de formato XML/JSON requerido
- **Límites**: Consideraciones de cuotas y volumen de transacciones

### 4.2 Implementación del Conector

```python
# Ejemplo conceptual del conector Verifactu en FastAPI

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
import httpx
import json
import logging
from typing import Dict, Any, Optional

# Configuración
VERIFACTU_API_URL = "https://api.verifactu.com/v1"
VERIFACTU_API_KEY = "your_api_key_here"

# Modelos
class FacturaRequest(BaseModel):
    emisor_nif: str
    emisor_nombre: str
    receptor_nif: str
    receptor_nombre: str
    numero: str
    fecha: str
    importe_total: float
    base_imponible: float
    iva: float
    lineas: list
    # Otros campos necesarios

class FacturaResponse(BaseModel):
    id_factura: str
    estado: str
    url_pdf: Optional[str] = None
    mensaje: Optional[str] = None

# Cliente API
class VerifactuClient:
    def __init__(self):
        self.base_url = VERIFACTU_API_URL
        self.api_key = VERIFACTU_API_KEY
        self.logger = logging.getLogger("verifactu")
    
    async def enviar_factura(self, factura: FacturaRequest) -> FacturaResponse:
        """Envía una factura a Verifactu para su procesamiento"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/facturas",
                    headers=headers,
                    json=factura.model_dump()
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return FacturaResponse(
                        id_factura=data["id"],
                        estado="ENVIADA",
                        url_pdf=data.get("pdf_url"),
                        mensaje="Factura enviada correctamente"
                    )
                else:
                    self.logger.error(f"Error al enviar factura: {response.text}")
                    return FacturaResponse(
                        id_factura="",
                        estado="ERROR",
                        mensaje=f"Error: {response.text}"
                    )
        except Exception as e:
            self.logger.exception("Excepción al comunicar con Verifactu")
            return FacturaResponse(
                id_factura="",
                estado="ERROR",
                mensaje=f"Excepción: {str(e)}"
            )
    
    async def consultar_estado(self, id_factura: str) -> Dict[str, Any]:
        """Consulta el estado de una factura en Verifactu"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/facturas/{id_factura}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.error(f"Error al consultar factura: {response.text}")
                    return {"estado": "ERROR", "mensaje": response.text}
        except Exception as e:
            self.logger.exception("Excepción al consultar estado en Verifactu")
            return {"estado": "ERROR", "mensaje": str(e)}

# Endpoints FastAPI
app = FastAPI()

@app.post("/api/facturas/enviar", response_model=FacturaResponse)
async def enviar_factura(factura: FacturaRequest):
    client = VerifactuClient()
    resultado = await client.enviar_factura(factura)
    
    if resultado.estado == "ERROR":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.mensaje
        )
    
    return resultado

@app.get("/api/facturas/{id_factura}/estado")
async def consultar_estado_factura(id_factura: str):
    client = VerifactuClient()
    resultado = await client.consultar_estado(id_factura)
    
    if resultado.get("estado") == "ERROR":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje")
        )
    
    return resultado
```

### 4.3 Configuración en Odoo

Para integrar el conector con Odoo, se requiere un módulo personalizado que:

1. **Extienda el modelo de facturas**:
   ```python
   class AccountInvoice(models.Model):
       _inherit = 'account.move'
       
       verifactu_id = fields.Char(string='ID Verifactu', readonly=True)
       verifactu_estado = fields.Selection([
           ('pendiente', 'Pendiente'),
           ('enviada', 'Enviada'),
           ('aceptada', 'Aceptada'),
           ('rechazada', 'Rechazada'),
           ('error', 'Error')
       ], string='Estado Verifactu', default='pendiente')
       verifactu_url_pdf = fields.Char(string='URL PDF Verifactu')
       verifactu_mensaje = fields.Text(string='Mensaje Verifactu')
       verifactu_fecha_envio = fields.Datetime(string='Fecha de envío')
   ```

2. **Implemente métodos de integración**:
   ```python
   def action_enviar_verifactu(self):
       """Envía la factura a Verifactu a través del middleware"""
       for record in self:
           # Preparar datos
           data = {
               'emisor_nif': record.company_id.vat,
               'emisor_nombre': record.company_id.name,
               'receptor_nif': record.partner_id.vat,
               'receptor_nombre': record.partner_id.name,
               'numero': record.name,
               'fecha': record.invoice_date.isoformat(),
               'importe_total': record.amount_total,
               'base_imponible': record.amount_untaxed,
               'iva': record.amount_tax,
               'lineas': [{
                   'descripcion': line.name,
                   'cantidad': line.quantity,
                   'precio_unitario': line.price_unit,
                   'importe': line.price_subtotal,
                   'tipo_iva': line.tax_ids[0].amount if line.tax_ids else 0
               } for line in record.invoice_line_ids]
           }
           
           # Llamar al middleware
           try:
               response = requests.post(
                   'http://localhost:8000/api/facturas/enviar',
                   json=data,
                   headers={'Content-Type': 'application/json'}
               )
               
               if response.status_code == 200:
                   result = response.json()
                   record.write({
                       'verifactu_id': result['id_factura'],
                       'verifactu_estado': 'enviada' if result['estado'] == 'ENVIADA' else 'error',
                       'verifactu_url_pdf': result.get('url_pdf', ''),
                       'verifactu_mensaje': result.get('mensaje', ''),
                       'verifactu_fecha_envio': fields.Datetime.now()
                   })
               else:
                   record.write({
                       'verifactu_estado': 'error',
                       'verifactu_mensaje': f"Error: {response.text}"
                   })
           except Exception as e:
               record.write({
                   'verifactu_estado': 'error',
                   'verifactu_mensaje': f"Excepción: {str(e)}"
               })
   ```

3. **Añada vistas y menús**:
   ```xml
   <record id="view_account_invoice_verifactu_form" model="ir.ui.view">
       <field name="name">account.move.verifactu.form</field>
       <field name="model">account.move</field>
       <field name="inherit_id" ref="account.view_move_form"/>
       <field name="arch" type="xml">
           <xpath expr="//header" position="inside">
               <button name="action_enviar_verifactu" 
                       string="Enviar a Verifactu" 
                       type="object" 
                       attrs="{'invisible': [('verifactu_estado', 'in', ['enviada', 'aceptada'])]}"
                       class="oe_highlight"/>
           </xpath>
           <xpath expr="//page[@name='other_info']" position="after">
               <page string="Verifactu" name="verifactu">
                   <group>
                       <field name="verifactu_id"/>
                       <field name="verifactu_estado"/>
                       <field name="verifactu_fecha_envio"/>
                       <field name="verifactu_url_pdf" widget="url"/>
                       <field name="verifactu_mensaje"/>
                   </group>
               </page>
           </xpath>
       </field>
   </record>
   ```

## 5. Automatización del Procesamiento de Facturas

### 5.1 Captura Automática

#### 5.1.1 Fuentes de Entrada
- **Email dedicado**: Configuración de cuenta para recepción de facturas
- **Carpeta compartida**: Monitorización de directorio para nuevos archivos
- **Portal web**: Interfaz para carga manual de documentos
- **Aplicación móvil**: Captura mediante cámara del dispositivo

#### 5.1.2 Procesamiento Programado
- **Tareas periódicas**: Ejecución de jobs cada X minutos/horas
- **Procesamiento en tiempo real**: Para entradas críticas
- **Cola de prioridad**: Gestión de documentos según urgencia
- **Balanceo de carga**: Distribución entre múltiples workers

### 5.2 Validación y Aprobación

#### 5.2.1 Niveles de Validación
- **Validación automática**: Para facturas que cumplen criterios predefinidos
- **Validación de primer nivel**: Por personal administrativo
- **Aprobación de segundo nivel**: Por responsables de departamento
- **Aprobación final**: Por dirección financiera según importe

#### 5.2.2 Flujo de Aprobación
- **Notificaciones**: Alertas a responsables de aprobación
- **Interfaz de revisión**: Comparativa de datos extraídos vs. documento
- **Comentarios y ajustes**: Posibilidad de corregir datos
- **Registro de auditoría**: Trazabilidad completa del proceso

### 5.3 Integración con Contabilidad

#### 5.3.1 Asientos Contables
- **Generación automática**: Basada en reglas predefinidas
- **Distribución analítica**: Asignación a centros de coste
- **Periodificación**: Para facturas recurrentes o de largo plazo
- **Conciliación**: Con pagos y extractos bancarios

#### 5.3.2 Gestión de Pagos
- **Programación**: Según vencimientos y condiciones
- **Agrupación**: Por proveedor o fecha
- **Generación de remesas**: Para pagos bancarios
- **Seguimiento**: De estado de pagos y confirmaciones

## 6. Consideraciones de Implementación

### 6.1 Seguridad y Cumplimiento

- **Cifrado de datos**: Para información sensible
- **Firma digital**: Conforme a requisitos legales
- **Trazabilidad**: Registro inmutable de todas las operaciones
- **Retención de documentos**: Según normativa fiscal
- **Acceso controlado**: Permisos granulares por rol y función

### 6.2 Rendimiento y Escalabilidad

- **Procesamiento asíncrono**: Para operaciones largas
- **Caché inteligente**: Para datos frecuentemente accedidos
- **Arquitectura distribuida**: Para alta disponibilidad
- **Monitorización**: De tiempos de respuesta y cuellos de botella
- **Escalado horizontal**: Capacidad de añadir nodos según demanda

### 6.3 Mantenimiento y Evolución

- **Versionado de API**: Para cambios compatibles
- **Configuración externalizada**: Para ajustes sin despliegue
- **Pruebas automatizadas**: Cobertura completa de funcionalidades
- **Documentación técnica**: Actualizada y accesible
- **Plan de actualización**: Para nuevas versiones de Odoo y Verifactu

## 7. Métricas y KPIs

- **Tiempo de procesamiento**: Desde recepción hasta registro
- **Tasa de reconocimiento**: Precisión del OCR
- **Tasa de validación automática**: Facturas que no requieren intervención
- **Tiempo de aprobación**: Para facturas que requieren revisión
- **Tasa de errores**: Facturas con problemas de procesamiento
- **Ahorro de tiempo**: Comparado con proceso manual

## 8. Próximos Pasos

1. **Desarrollo del conector Verifactu**:
   - Implementación de la integración API
   - Pruebas con entorno de sandbox
   - Validación de formatos y respuestas

2. **Implementación del servicio OCR**:
   - Configuración de Tesseract y bibliotecas auxiliares
   - Entrenamiento para tipos específicos de facturas
   - Validación con conjunto de pruebas reales

3. **Desarrollo del módulo Odoo**:
   - Extensión de modelos y vistas
   - Implementación de flujos de trabajo
   - Configuración de reglas y automatizaciones

4. **Integración con el dashboard**:
   - Desarrollo de interfaces de usuario en Refine
   - Implementación de formularios de captura
   - Visualización de estados y estadísticas
