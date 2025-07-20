from typing import List, Dict, Any, Optional
import logging
import json
from .odoo_base_service import OdooBaseService

logger = logging.getLogger("odoo_invoice_service")

class OdooInvoiceService(OdooBaseService):
    """Servicio para creación y consulta de facturas de proveedor (account.move)"""

    def __init__(self):
        super().__init__()
        # Obtener impuesto compra 21 %
        tax_ids = self._execute_kw(
            "account.tax",
            "search",
            [[["type_tax_use", "=", "purchase"], ["amount", "=", 21]]],
            {"limit": 1}
        )
        self.INVOICE_TAX_ID = tax_ids[0] if tax_ids else 0
        re_ids = self._execute_kw("account.tax", "search", [[["type_tax_use","=","purchase"],["amount","=",5.2]]], {"limit":1})
        self.RE_TAX_ID = re_ids[0] if re_ids else 0

    def find_supplier_invoice(self, partner_id: int, ref: str) -> Optional[int]:
        """Devuelve el ID de la factura si existe ya."""
        domain = [
            ("partner_id", "=", partner_id),
            ("move_type", "=", "in_invoice"),
            ("ref", "=", ref)
        ]
        ids = self._execute_kw("account.move", "search", [domain], {"limit": 1})
        return ids[0] if ids else None

    def _ensure_product(self, default_code: str, name: str) -> int:
        """Busca product.product por default_code o nombre, si no existe crea stub y devuelve product_id"""
        logger.info(f"Buscando producto con código '{default_code}' o nombre '{name}'")
        
        # Paso 1: Buscar por default_code exacto
        if default_code:
            product_domain = [("default_code", "=", default_code)]
            product_ids = self._execute_kw("product.product", "search", [product_domain], {"limit": 1})
            if product_ids:
                logger.info(f"Producto encontrado por código exacto: {product_ids[0]}")
                return product_ids[0]
        
        # Paso 2: Buscar por nombre exacto si tenemos nombre
        if name and len(name) > 3:  # Evitar búsquedas con nombres muy cortos
            name_domain = [("name", "=", name)]
            product_ids = self._execute_kw("product.product", "search", [name_domain], {"limit": 1})
            if product_ids:
                logger.info(f"Producto encontrado por nombre exacto: {product_ids[0]}")
                return product_ids[0]
            
            # Paso 3: Buscar por nombre parcial (contiene)
            name_like_domain = [("name", "ilike", name[:30])]  # Usar los primeros 30 caracteres
            product_ids = self._execute_kw("product.product", "search", [name_like_domain], {"limit": 1})
            if product_ids:
                logger.info(f"Producto encontrado por nombre parcial: {product_ids[0]}")
                return product_ids[0]
        
        # Paso 4: Si no se encuentra, crear un nuevo producto
        logger.info(f"No se encontró producto, creando uno nuevo con nombre: {name or default_code}")
        
        # Generar un código por defecto si no existe
        if not default_code and name:
            import hashlib
            default_code = f"OCR-{hashlib.md5(name.encode()).hexdigest()[:8]}"
            logger.info(f"Generando código para nuevo producto: {default_code}")
        
        template_vals = {
            "name": name or default_code,
            "default_code": default_code or f"OCR-{int(time.time())}",
            "type": "consu",  # Usar 'consu' en lugar de 'product' para Odoo 18
        }
        
        try:
            template_id = self._execute_kw("product.template", "create", [template_vals])
            logger.info(f"Plantilla de producto creada con ID: {template_id}")
            
            # product.product se crea automáticamente; buscarlo
            product_ids = self._execute_kw("product.product", "search", [["product_tmpl_id", "=", template_id]], {"limit": 1})
            if product_ids:
                logger.info(f"Producto creado con ID: {product_ids[0]}")
                return product_ids[0]
            else:
                logger.error("No se pudo encontrar el producto recién creado")
                return 0
        except Exception as e:
            logger.error(f"Error al crear producto: {str(e)}")
            return 0

    def _get_purchase_journal_id(self, company_id: int = 1) -> int:
        """
        Obtiene el ID del diario de compras para la compañía especificada.
        
        Args:
            company_id: ID de la compañía
            
        Returns:
            ID del diario de compras
        """
        logger.info(f"Buscando diario de compras para la compañía {company_id}")
        
        # Para la compañía 1 (El pelotazo), sabemos que el diario de compras es el ID 9
        if company_id == 1:
            logger.info("Usando diario de compras conocido para compañía 1: ID 9")
            return 9  # ID conocido para la compañía 1
            
        try:
            # Para otras compañías, buscamos el diario de compras
            journals = self._execute_kw(
                "account.journal",
                "search_read",
                [[('type', '=', 'purchase'), ('company_id', '=', company_id)]],
                {"fields": ["id", "name"]}
            )
            
            if journals:
                journal_id = journals[0]["id"]
                logger.info(f"Diario de compras encontrado para compañía {company_id}: {journals[0]['name']} (ID: {journal_id})")
                return journal_id
            else:
                # Si no se encuentra un diario para la compañía, intentamos con el diario de compras por defecto
                logger.warning(f"No se encontró diario de compras para la compañía {company_id}. Buscando diario por defecto.")
                default_journals = self._execute_kw(
                    "account.journal",
                    "search_read",
                    [[('type', '=', 'purchase')]],
                    {"fields": ["id", "name"], "limit": 1}
                )
                
                if default_journals:
                    journal_id = default_journals[0]["id"]
                    logger.info(f"Usando diario de compras por defecto: {default_journals[0]['name']} (ID: {journal_id})")
                    return journal_id
                else:
                    # Si no hay ningún diario de compras, usamos un ID conocido
                    logger.warning("No se encontró ningún diario de compras. Usando ID por defecto.")
                    return 9  # ID conocido para la compañía 1
        except Exception as e:
            logger.error(f"Error al obtener diario de compras: {e}")
            return 9  # ID conocido para la compañía 1
            
    def _get_account_id(self, company_id: int = 1) -> int:
        """
        Obtiene el ID de una cuenta contable válida para facturas de proveedor para la compañía especificada.
        
        Args:
            company_id: ID de la compañía
            
        Returns:
            ID de la cuenta contable o None si no se encuentra ninguna válida
        """
        logger.info(f"Buscando cuenta contable válida para la compañía {company_id}")
        
        # En Odoo 18, las cuentas contables se relacionan con las compañías a través de la tabla account_account_res_company_rel
        try:
            # Para la compañía 1 (El pelotazo), sabemos que existen cuentas de gastos con IDs conocidos
            if company_id == 1:
                # Usar directamente una cuenta de gastos conocida para la compañía 1
                # ID 986: "Compras de mercaderías" (600000)
                logger.info(f"Usando cuenta de gastos conocida para compañía 1: Compras de mercaderías (ID: 986)")
                return 986  # Compras de mercaderías
            
            # Para otras compañías o como fallback, buscamos cuentas válidas
            # Consultar la tabla de relación entre cuentas y compañías
            account_company_rel = self._execute_kw(
                "account.account.res.company.rel",
                "search_read",
                [[('res_company_id', '=', company_id)]],
                {"fields": ["account_account_id"]}
            )
            
            if not account_company_rel:
                logger.warning(f"No se encontraron relaciones entre cuentas y la compañía {company_id}")
                if company_id == 1:
                    return 986  # Cuenta conocida para compañía 1
                return None
            
            # Obtener los IDs de las cuentas asociadas a la compañía
            account_ids = [rel['account_account_id'][0] for rel in account_company_rel if 'account_account_id' in rel and rel['account_account_id']]
            logger.info(f"Encontradas {len(account_ids)} cuentas asociadas a la compañía {company_id}")
            
            if not account_ids:
                logger.warning(f"No se encontraron cuentas para la compañía {company_id}")
                if company_id == 1:
                    return 986  # Cuenta conocida para compañía 1
                return None
            
            # Obtener detalles de las cuentas
            company_accounts = self._execute_kw(
                "account.account",
                "read",
                [account_ids],
                {"fields": ["id", "name", "code_store", "account_type"]}
            )
            
            logger.info(f"Obtenidos detalles de {len(company_accounts)} cuentas")
            
            # Filtrar las cuentas válidas (las que tienen los datos necesarios)
            valid_accounts = [acc for acc in company_accounts if 'id' in acc and 'account_type' in acc]
            
            logger.info(f"Encontradas {len(valid_accounts)} cuentas válidas para la compañía {company_id}")
            
            # En Odoo 18, buscamos cuentas adecuadas para facturas de proveedor
            # Primero intentamos con cuentas de tipo expense (gastos)
            expense_accounts = [acc for acc in valid_accounts if acc.get('account_type') == 'expense']
            if expense_accounts:
                account_id = expense_accounts[0]['id']
                logger.info(f"Usando cuenta de gastos: {expense_accounts[0].get('name', '')} (ID: {account_id})")
                return account_id
            
            # Luego buscamos cuentas con códigos típicos de gastos o compras
            if valid_accounts:
                # Extraer códigos de las cuentas (en Odoo 18 están en code_store)
                accounts_with_codes = []
                for acc in valid_accounts:
                    if 'code_store' in acc and acc['code_store']:
                        # En Odoo 18, code_store es un diccionario con el formato {"company_id": "code"}
                        try:
                            if isinstance(acc['code_store'], dict) and str(company_id) in acc['code_store']:
                                code = acc['code_store'][str(company_id)]
                                accounts_with_codes.append((acc, code))
                        except Exception as e:
                            logger.warning(f"Error al procesar code_store: {e}")
                
                # Códigos comunes para cuentas de gastos en plan contable español
                expense_codes = ['600', '601', '602', '606', '607', '608', '609', '610', '620', '621', '622', '623', '624', '625', '626', '627', '628', '629']
                code_accounts = [acc_tuple[0] for acc_tuple in accounts_with_codes if any(acc_tuple[1].startswith(code) for code in expense_codes)]
                
                if code_accounts:
                    account_id = code_accounts[0]['id']
                    logger.info(f"Usando cuenta por código: {code_accounts[0].get('name', '')} (ID: {account_id})")
                    return account_id
            
            # Si no encontramos ninguna cuenta adecuada, usamos la cuenta conocida para la compañía 1
            if company_id == 1:
                logger.info("No se encontró cuenta adecuada, usando cuenta de gastos conocida (ID: 986)")
                return 986  # Compras de mercaderías
            
            # Si hay cuentas válidas pero ninguna es adecuada, usamos la primera
            if valid_accounts:
                account_id = valid_accounts[0]['id']
                logger.info(f"Usando primera cuenta válida: {valid_accounts[0].get('name', '')} (ID: {account_id})")
                return account_id
            
            # Si no hay cuentas válidas, devolvemos None
            logger.warning(f"No se encontraron cuentas válidas para la compañía {company_id}")
            return None
            
        except Exception as e:
            logger.warning(f"Error al buscar cuentas para la compañía {company_id}: {e}")
            # En caso de error, usar una cuenta conocida para la compañía 1
            if company_id == 1:
                logger.info("Usando cuenta de gastos conocida (ID: 986) debido a error")
                return 986  # Compras de mercaderías
            return None

    def create_supplier_invoice(
        self,
        partner_id: int,
        invoice_number: str,
        invoice_date: str,
        lines: List[Dict[str, Any]],
        due_date: str = None,
        journal_id: int = None,
        move_type: str = "in_invoice",
        currency_id: int = 1,
        ref: str = None,
        narration: str = None
    ) -> Dict[str, Any]:
        """
        Crea factura de proveedor si no existe.
        
        Args:
            partner_id: ID del proveedor
            invoice_number: Número de factura
            invoice_date: Fecha de factura en formato ISO (YYYY-MM-DD)
            lines: Lista de líneas de factura
            due_date: Fecha de vencimiento en formato ISO (opcional)
            journal_id: ID del diario de compras (opcional)
            move_type: Tipo de movimiento (por defecto "in_invoice")
            currency_id: ID de la moneda (por defecto 1, EUR)
            ref: Referencia externa (opcional)
            narration: Notas adicionales (opcional)
            
        Returns:
            Dict con created, duplicate y id o error
        """
        try:
            # Verificar si la factura ya existe
            existing_id = self.find_supplier_invoice(partner_id, invoice_number)
            if existing_id:
                logger.info(f"Factura ya existe con ID: {existing_id}")
                return {"created": False, "duplicate": True, "id": existing_id, "success": True, "invoice_id": existing_id}

            # Verificar que el proveedor existe y obtener su compañía
            partner_data = self._execute_kw(
                "res.partner",
                "read",
                [[partner_id]],
                {"fields": ["name", "vat", "company_id"]}
            )
            
            if not partner_data:
                raise ValueError(f"El proveedor con ID {partner_id} no existe en Odoo")
                
            logger.info(f"Proveedor verificado: {partner_data[0]['name']} (ID: {partner_id})")
            
            # Determinar la compañía a usar
            # Si el proveedor no tiene compañía, usamos la compañía principal (ID 1)
            company_id = 1
            if partner_data[0].get('company_id'):
                company_id = partner_data[0]['company_id'][0]
                
            logger.info(f"Usando compañía con ID: {company_id}")
            
            # Usar el journal_id proporcionado o buscar uno adecuado para la compañía
            purchase_journal_id = None
            
            # Si se proporciona journal_id, verificar que sea válido
            if journal_id:
                logger.info(f"Usando diario de compras proporcionado con ID: {journal_id}")
                journal_data = self._execute_kw(
                    "account.journal",
                    "read",
                    [[journal_id]],
                    {"fields": ["name", "type", "code", "company_id"]}
                )
                
                if journal_data and journal_data[0].get('type') == 'purchase':
                    purchase_journal_id = journal_id
                    logger.info(f"Diario de compras verificado: {journal_data[0]['name']} (ID: {purchase_journal_id})")
                else:
                    logger.warning(f"El diario proporcionado con ID {journal_id} no es válido o no es de tipo compra")
            
            # Si no se proporcionó journal_id o no es válido, buscar uno para la compañía
            if not purchase_journal_id:
                logger.info(f"Buscando diario de compras para la compañía {company_id}")
                
                # Primero intentar con el diario de compras con ID 9 que sabemos que existe para la compañía 1
                if company_id == 1:
                    logger.info("Intentando obtener el diario de compras con ID 9 directamente")
                    journal_id_9 = self._execute_kw(
                        "account.journal",
                        "read",
                        [[9]],
                        {"fields": ["name", "company_id", "type", "code"]}
                    )
                    
                    if journal_id_9 and journal_id_9[0].get('type') == 'purchase' and journal_id_9[0].get('company_id')[0] == company_id:
                        logger.info(f"Usando diario de compras encontrado directamente con ID 9: {journal_id_9[0]['name']}")
                        purchase_journal_id = 9
                
                # Si no encontramos el diario con ID 9, buscar cualquier diario de compra para esta compañía
                if not purchase_journal_id:
                    purchase_journals = self._execute_kw(
                        "account.journal",
                        "search_read",
                        [["type", "=", "purchase"], ["company_id", "=", company_id]],
                        {"fields": ["name", "company_id", "code"], "limit": 1}
                    )
                    
                    if purchase_journals:
                        purchase_journal_id = purchase_journals[0]['id']
                        logger.info(f"Usando diario de compras: {purchase_journals[0]['name']} (ID: {purchase_journal_id}) de la compañía {company_id}")
                    else:
                        # Listar todos los diarios de compra para depurar
                        all_purchase_journals = self._execute_kw(
                            "account.journal",
                            "search_read",
                            [["type", "=", "purchase"]],
                            {"fields": ["name", "company_id", "code"]}
                        )
                        logger.info(f"Diarios de compra disponibles: {all_purchase_journals}")
                        raise ValueError(f"No existe un diario de compras para la compañía {company_id}")
            
            # Verificar que tenemos un diario de compras válido
            if not purchase_journal_id:
                raise ValueError(f"No se pudo encontrar un diario de compras válido para la compañía {company_id}")

            
            # Verificar los impuestos disponibles para esta compañía
            try:
                taxes = self._execute_kw(
                    "account.tax",
                    "search_read",
                    [["company_id", "=", company_id]],
                    {"fields": ["name", "type_tax_use", "amount", "description"]}
                )
                
                logger.info(f"Impuestos disponibles para la compañía {company_id}: {json.dumps(taxes, default=str)}")
                
                # Buscar impuestos de compra para esta compañía
                purchase_taxes = [tax for tax in taxes if tax.get('type_tax_use') == 'purchase'] if taxes else []
                logger.info(f"Impuestos de compra disponibles: {json.dumps([{tax['id']: tax['name']} for tax in purchase_taxes], default=str)}")
                
                # Identificar impuestos específicos por nombre, descripción o porcentaje
                iva_21_id = None
                iva_10_id = None
                iva_4_id = None
                recargo_equivalencia_id = None
                
                # Buscar impuestos específicos por nombre, descripción o porcentaje
                for tax in purchase_taxes:
                    name = str(tax.get('name', '')).lower() if tax.get('name') else ''
                    if isinstance(name, dict) and 'en_US' in name:
                        name = str(name.get('en_US', '')).lower()
                    
                    description = str(tax.get('description', '')).lower() if tax.get('description') else ''
                    if isinstance(description, dict) and 'es_ES' in description:
                        description = str(description.get('es_ES', '')).lower()
                    
                    amount = float(tax.get('amount', 0))
                    
                    logger.info(f"Analizando impuesto: {name} / {description} / {amount}%")
                    
                    # Identificar IVA 21%
                    if (('21' in name or '21' in description) and ('iva' in name or 'iva' in description)) or \
                       (amount == 21.0 and tax.get('type_tax_use') == 'purchase'):
                        iva_21_id = tax['id']
                        logger.info(f"Identificado impuesto IVA 21%: {name} (ID: {tax['id']})")
                    
                    # Identificar IVA 10%
                    elif (('10' in name or '10' in description) and ('iva' in name or 'iva' in description)) or \
                         (amount == 10.0 and tax.get('type_tax_use') == 'purchase'):
                        iva_10_id = tax['id']
                        logger.info(f"Identificado impuesto IVA 10%: {name} (ID: {tax['id']})")
                    
                    # Identificar IVA 4%
                    elif (('4' in name or '4' in description) and ('iva' in name or 'iva' in description)) or \
                         (amount == 4.0 and tax.get('type_tax_use') == 'purchase'):
                        iva_4_id = tax['id']
                        logger.info(f"Identificado impuesto IVA 4%: {name} (ID: {tax['id']})")
                    
                    # Identificar Recargo de Equivalencia (5.2% o similar)
                    elif ('recargo' in name or 'equivalencia' in name or 'r.e.' in name or 
                          'recargo' in description or 'equivalencia' in description or 'r.e.' in description) or \
                         (amount > 5.0 and amount < 5.5 and tax.get('type_tax_use') == 'purchase'):  # Aproximadamente 5.2%
                        recargo_equivalencia_id = tax['id']
                        logger.info(f"Identificado Recargo de Equivalencia: {name} (ID: {tax['id']})")
                
                # Si no se encontraron impuestos específicos, buscar por porcentaje
                if not iva_21_id:
                    for tax in purchase_taxes:
                        if float(tax.get('amount', 0)) == 21.0:
                            iva_21_id = tax['id']
                            logger.info(f"Identificado IVA 21% por porcentaje: {tax['id']}")
                            break
                
                if not iva_10_id:
                    for tax in purchase_taxes:
                        if float(tax.get('amount', 0)) == 10.0:
                            iva_10_id = tax['id']
                            logger.info(f"Identificado IVA 10% por porcentaje: {tax['id']}")
                            break
                
                if not iva_4_id:
                    for tax in purchase_taxes:
                        if float(tax.get('amount', 0)) == 4.0:
                            iva_4_id = tax['id']
                            logger.info(f"Identificado IVA 4% por porcentaje: {tax['id']}")
                            break
                
                # Guardar los IDs de impuestos identificados para uso posterior
                tax_mapping = {
                    'iva_21': iva_21_id,
                    'iva_10': iva_10_id,
                    'iva_4': iva_4_id,
                    'recargo_equivalencia': recargo_equivalencia_id
                }
                
                logger.info(f"Mapeo de impuestos identificados: {json.dumps(tax_mapping, default=str)}")
                
                # Si no hay impuestos de compra, no usaremos impuestos
                use_taxes = len(purchase_taxes) > 0
                
                # Convertir a lista de IDs para uso posterior
                purchase_tax_ids = [tax['id'] for tax in purchase_taxes]
                
            except Exception as e:
                logger.error(f"Error al buscar impuestos: {str(e)}", exc_info=True)
                taxes = []
                purchase_tax_ids = []
                tax_mapping = {}
                use_taxes = False
            
            # Obtener cuenta contable válida para la factura
            logger.info(f"Buscando cuenta contable válida para factura de proveedor para la compañía {company_id}")
            account_id = self._get_account_id(company_id)
            
            if not account_id:
                raise ValueError(f"No se pudo encontrar una cuenta contable válida para la compañía {company_id}")
                
            logger.info(f"Usando cuenta contable con ID: {account_id} para la factura de proveedor")


            
            # Preparar invoice_line_ids
            invoice_line_ids = []
            for l in lines:
                product_id = 0
                default_code = l.get("default_code")
                if default_code:
                    product_id = self._ensure_product(default_code, l.get("name"))
                
                line_vals = {
                    "product_id": product_id or False,
                    "name": l.get("name"),
                    "quantity": l.get("quantity", 1.0),
                    "price_unit": l.get("price_unit", 0.0),
                }
                
                # Añadir descuento si está presente en los datos
                if "discount" in l and l["discount"] is not None:
                    try:
                        # Intentar convertir el descuento a float, manejando diferentes formatos
                        discount_str = str(l["discount"]).replace('%', '').strip()
                        discount = float(discount_str)
                        if 0 <= discount <= 100:  # Validar que el descuento esté en un rango válido
                            line_vals["discount"] = discount
                            logger.info(f"Aplicando descuento de {discount}% a la línea de factura")
                        else:
                            logger.warning(f"Descuento fuera de rango válido: {discount}%")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error al convertir descuento '{l.get('discount')}' a float: {e}")
                
                # Intentar extraer descuento del nombre si no está explícitamente en el campo discount
                elif "name" in l and l["name"]:
                    name = l["name"]
                    # Buscar patrones comunes de descuento en el nombre (ej: "Producto XYZ -10%" o "Descuento: 15%")
                    import re
                    discount_patterns = [
                        r'\s-\s?(\d+)\s?%',  # Formato: "Producto - 10%"
                        r'\s(\d+)\s?%\s+dto',  # Formato: "Producto 10% dto"
                        r'descuento[:\s]+(\d+)\s?%',  # Formato: "Descuento: 10%"
                        r'dto\.?[:\s]+(\d+)\s?%',  # Formato: "Dto.: 10%"
                        r'(\d+)\s?%\s+descuento',  # Formato: "10% descuento"
                    ]
                    
                    for pattern in discount_patterns:
                        match = re.search(pattern, name.lower())
                        if match:
                            try:
                                discount = float(match.group(1))
                                if 0 < discount <= 100:  # Solo aplicar si es un descuento válido
                                    line_vals["discount"] = discount
                                    logger.info(f"Descuento de {discount}% extraído del nombre del producto")
                                    break
                            except (ValueError, IndexError):
                                pass
                
                
                # Añadir la cuenta contable explícitamente si la encontramos
                if account_id:
                    line_vals["account_id"] = account_id
                
                # Añadir impuestos de la compañía correcta si están disponibles
                if use_taxes:
                    # Determinar qué impuestos aplicar basándonos en la información de la línea
                    tax_ids_to_apply = []
                    
                    # Verificar si la línea tiene información específica de impuestos
                    tax_type = l.get("tax_type", "")
                    apply_recargo = l.get("apply_recargo_equivalencia", False)
                    
                    # Si no hay tax_type explícito, intentar inferirlo del nombre o descripción
                    if not tax_type and "name" in l:
                        name_lower = l["name"].lower() if l["name"] else ""
                        if "iva 21" in name_lower or "21%" in name_lower:
                            tax_type = "iva_21"
                            logger.info(f"Tipo de impuesto inferido del nombre: IVA 21%")
                        elif "iva 10" in name_lower or "10%" in name_lower:
                            tax_type = "iva_10"
                            logger.info(f"Tipo de impuesto inferido del nombre: IVA 10%")
                        elif "iva 4" in name_lower or "4%" in name_lower:
                            tax_type = "iva_4"
                            logger.info(f"Tipo de impuesto inferido del nombre: IVA 4%")
                        
                        # Detectar recargo de equivalencia en el nombre
                        if "recargo" in name_lower or "r.e." in name_lower or "equivalencia" in name_lower:
                            apply_recargo = True
                            logger.info(f"Recargo de equivalencia inferido del nombre")
                    
                    # Aplicar impuesto según el tipo especificado o usar IVA 21% por defecto
                    if tax_type == "iva_21" and tax_mapping.get("iva_21"):
                        tax_ids_to_apply.append(tax_mapping["iva_21"])
                        logger.info(f"Aplicando IVA 21% (ID: {tax_mapping['iva_21']}) a la línea de factura")
                    elif tax_type == "iva_10" and tax_mapping.get("iva_10"):
                        tax_ids_to_apply.append(tax_mapping["iva_10"])
                        logger.info(f"Aplicando IVA 10% (ID: {tax_mapping['iva_10']}) a la línea de factura")
                    elif tax_type == "iva_4" and tax_mapping.get("iva_4"):
                        tax_ids_to_apply.append(tax_mapping["iva_4"])
                        logger.info(f"Aplicando IVA 4% (ID: {tax_mapping['iva_4']}) a la línea de factura")
                    elif tax_mapping.get("iva_21"):  # Si no se especifica, usar IVA 21% como predeterminado
                        tax_ids_to_apply.append(tax_mapping["iva_21"])
                        logger.info(f"Aplicando IVA 21% por defecto (ID: {tax_mapping['iva_21']}) a la línea de factura")
                    elif purchase_tax_ids:  # Si no hay IVA 21%, usar el primer impuesto disponible
                        default_tax_id = purchase_tax_ids[0]
                        tax_ids_to_apply.append(default_tax_id)
                        logger.info(f"Aplicando impuesto por defecto (ID: {default_tax_id}) a la línea de factura")
                    
                    # Añadir Recargo de Equivalencia si está indicado y disponible
                    if apply_recargo and tax_mapping.get("recargo_equivalencia"):
                        tax_ids_to_apply.append(tax_mapping["recargo_equivalencia"])
                        logger.info(f"Aplicando Recargo de Equivalencia (ID: {tax_mapping['recargo_equivalencia']}) a la línea de factura")
                    
                    # Si se encontraron impuestos para aplicar, añadirlos a la línea
                    if tax_ids_to_apply:
                        line_vals["tax_ids"] = [(6, 0, tax_ids_to_apply)]
                        logger.info(f"Añadiendo impuestos IDs {tax_ids_to_apply} a la línea de factura")
                    else:
                        # Forzar la aplicación de al menos un impuesto si hay impuestos disponibles
                        if purchase_tax_ids:
                            # Primero intentar encontrar IVA 21% (el más común)
                            default_tax_id = None
                            iva_21_id = None
                            iva_10_id = None
                            iva_4_id = None
                            recargo_21_id = None
                            recargo_10_id = None
                            recargo_4_id = None
                            
                            # Buscar impuestos por porcentaje y tipo
                            for tax in purchase_taxes:
                                amount = float(tax.get('amount', 0))
                                name = tax.get('name', '').lower()
                                
                                # Identificar impuestos IVA
                                if amount == 21.0 and 'iva' in name and 'recargo' not in name:
                                    iva_21_id = tax['id']
                                elif amount == 10.0 and 'iva' in name and 'recargo' not in name:
                                    iva_10_id = tax['id']
                                elif amount == 4.0 and 'iva' in name and 'recargo' not in name:
                                    iva_4_id = tax['id']
                                # Identificar recargos de equivalencia
                                elif (amount == 5.2 or amount == 5.0) and ('recargo' in name or 'r.e.' in name or 'equivalencia' in name):
                                    recargo_21_id = tax['id']
                                elif (amount == 1.4 or amount == 1.5) and ('recargo' in name or 'r.e.' in name or 'equivalencia' in name):
                                    recargo_10_id = tax['id']
                                elif (amount == 0.5 or amount == 0.6) and ('recargo' in name or 'r.e.' in name or 'equivalencia' in name):
                                    recargo_4_id = tax['id']
                                # Cualquier impuesto positivo como respaldo
                                elif amount > 0 and 'iva' in name and 'recargo' not in name:  
                                    if not default_tax_id:
                                        default_tax_id = tax['id']
                            
                            # Si no encontramos impuestos por nombre, buscar solo por porcentaje
                            if not (iva_21_id or iva_10_id or iva_4_id):
                                for tax in purchase_taxes:
                                    amount = float(tax.get('amount', 0))
                                    if amount == 21.0:
                                        iva_21_id = tax['id']
                                    elif amount == 10.0:
                                        iva_10_id = tax['id']
                                    elif amount == 4.0:
                                        iva_4_id = tax['id']
                                    elif amount > 0:  # Cualquier impuesto positivo como respaldo
                                        if not default_tax_id:
                                            default_tax_id = tax['id']
                            
                            # Priorizar IVA 21%, luego 10%, luego 4%, luego cualquier impuesto positivo
                            tax_to_apply = iva_21_id or iva_10_id or iva_4_id or default_tax_id or purchase_tax_ids[0]
                            
                            if tax_to_apply:
                                # Determinar el recargo correspondiente al impuesto seleccionado
                                recargo_to_apply = None
                                recargo_rate = line.get('recargo_rate', None)
                                
                                if apply_recargo:
                                    # Si tenemos una tasa de recargo específica, buscar el impuesto correspondiente
                                    if recargo_rate is not None:
                                        logger.info(f"Buscando recargo con tasa específica: {recargo_rate}%")
                                        # Buscar el recargo más cercano a la tasa especificada
                                        closest_recargo = None
                                        min_diff = float('inf')
                                        
                                        for tax in purchase_taxes:
                                            if 'recargo' in tax.get('name', '').lower() or 'r.e.' in tax.get('name', '').lower() or 'equivalencia' in tax.get('name', '').lower():
                                                amount = float(tax.get('amount', 0))
                                                diff = abs(amount - recargo_rate)
                                                if diff < min_diff:
                                                    min_diff = diff
                                                    closest_recargo = tax['id']
                                        
                                        if closest_recargo:
                                            recargo_to_apply = closest_recargo
                                            logger.info(f"Recargo encontrado con tasa más cercana a {recargo_rate}%: ID {closest_recargo}")
                                    
                                    # Si no encontramos por tasa específica o no teníamos tasa, usar la lógica anterior
                                    if not recargo_to_apply:
                                        if tax_to_apply == iva_21_id and recargo_21_id:
                                            recargo_to_apply = recargo_21_id
                                        elif tax_to_apply == iva_10_id and recargo_10_id:
                                            recargo_to_apply = recargo_10_id
                                        elif tax_to_apply == iva_4_id and recargo_4_id:
                                            recargo_to_apply = recargo_4_id
                                        elif tax_mapping.get("recargo_equivalencia"):
                                            recargo_to_apply = tax_mapping["recargo_equivalencia"]
                                
                                # Aplicar impuesto y recargo si corresponde
                                if recargo_to_apply:
                                    line_vals["tax_ids"] = [(6, 0, [tax_to_apply, recargo_to_apply])]
                                    logger.info(f"Aplicando impuesto ID {tax_to_apply} con recargo de equivalencia ID {recargo_to_apply}")
                                else:
                                    line_vals["tax_ids"] = [(6, 0, [tax_to_apply])]
                                    logger.info(f"Forzando aplicación de impuesto ID {tax_to_apply} a la línea de factura")
                        else:
                            logger.warning("No se encontraron impuestos aplicables para esta línea de factura")
                            # Intentar buscar impuestos de compra nuevamente con criterios más amplios
                            fallback_tax_ids = self._execute_kw(
                                "account.tax",
                                "search",
                                [[['type_tax_use', '=', 'purchase'], ['active', '=', True]]],
                                {"limit": 5}
                            )
                            if fallback_tax_ids:
                                line_vals["tax_ids"] = [(6, 0, [fallback_tax_ids[0]])]
                                logger.info(f"Usando impuesto de respaldo ID {fallback_tax_ids[0]} como último recurso")
                
                invoice_line_ids.append((0, 0, line_vals))
            
            # Verificar que hay al menos una línea de factura
            if not invoice_line_ids:
                raise ValueError("No se proporcionaron líneas de factura válidas")
                
            # Construir valores para la factura con todos los campos obligatorios
            vals = {
                "move_type": "in_invoice",  # Siempre in_invoice para facturas de proveedores
                "partner_id": partner_id,
                "invoice_date": invoice_date,
                "ref": ref or invoice_number,
                "invoice_line_ids": invoice_line_ids,
                "journal_id": purchase_journal_id,  # Usar el diario de proveedores fijo
                "currency_id": currency_id,
                "company_id": company_id  # Usar la compañía determinada anteriormente
            }
            
            # Añadir campos opcionales si están presentes
            if due_date:
                vals["invoice_date_due"] = due_date
            if narration:
                vals["narration"] = narration
                
            # Añadir log detallado de los valores que se envían a Odoo
            logger.info(f"Creando factura en Odoo con valores: {json.dumps(vals, default=str, indent=2)}")
            
            # Intentar crear la factura
            invoice_id_result = self._execute_kw("account.move", "create", [[vals]])
            logger.info(f"Resultado de la creación de factura: {invoice_id_result}")
            
            if not invoice_id_result:
                raise ValueError("Odoo devolvió ID vacío al crear la factura")
            
            # Extraer el ID como entero si viene como lista
            invoice_id = invoice_id_result[0] if isinstance(invoice_id_result, list) else invoice_id_result
            logger.info(f"ID de factura normalizado: {invoice_id}")
                
            # Verificar que la factura se creó correctamente
            invoice_data = self._execute_kw("account.move", "read", [[invoice_id]], {"fields": ["name", "state", "move_type", "journal_id"]})
            logger.info(f"Datos de la factura creada: {json.dumps(invoice_data, default=str)}")
            
            # Intentar publicar la factura (opcional)
            # self._execute_kw("account.move", "action_post", [[invoice_id]])
            # logger.info(f"Factura publicada con éxito")
            
            return {
                "created": True, 
                "duplicate": False, 
                "id": invoice_id, 
                "success": True, 
                "invoice_id": invoice_id,
                "invoice_data": invoice_data[0] if invoice_data else {}
            }
                
        except Exception as e:
            logger.error(f"Error al crear factura de proveedor: {e}", exc_info=True)
            return {"created": False, "duplicate": False, "error": str(e), "success": False}

            logger.error(f"Error creando factura: {e}", exc_info=True)
            return {"success": False, "created": False, "error": str(e)}
