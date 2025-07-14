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
        """Busca product.product por default_code, si no existe crea stub y devuelve product_id"""
        product_domain = [("default_code", "=", default_code)]
        product_ids = self._execute_kw("product.product", "search", [product_domain], {"limit": 1})
        if product_ids:
            return product_ids[0]

        template_vals = {
            "name": name or default_code,
            "default_code": default_code,
            "type": "product",
        }
        template_id = self._execute_kw("product.template", "create", [[template_vals]])
        # product.product se crea automáticamente; buscarlo
        product_ids = self._execute_kw("product.product", "search", [[("product_tmpl_id", "=", template_id)]], {"limit": 1})
        return product_ids[0] if product_ids else 0

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
                    {"fields": ["name", "type_tax_use"]}
                )
                
                logger.info(f"Impuestos disponibles para la compañía {company_id}: {json.dumps(taxes, default=str)}")
                
                # Buscar impuestos de compra para esta compañía
                purchase_taxes = [tax['id'] for tax in taxes if tax.get('type_tax_use') == 'purchase'] if taxes else []
                logger.info(f"Impuestos de compra disponibles: {purchase_taxes}")
                
                # Si no hay impuestos de compra, no usaremos impuestos
                use_taxes = len(purchase_taxes) > 0
            except Exception as e:
                logger.error(f"Error al buscar impuestos: {str(e)}")
                taxes = []
                purchase_taxes = []
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
                
                # Añadir la cuenta contable explícitamente si la encontramos
                if account_id:
                    line_vals["account_id"] = account_id
                
                # Añadir impuestos de la compañía correcta si están disponibles
                if use_taxes and purchase_taxes:
                    # Usar solo el primer impuesto de compra disponible para esta compañía
                    # En un caso real, se debería seleccionar el impuesto correcto según el producto
                    line_vals["tax_ids"] = [(6, 0, [purchase_taxes[0]])]
                    logger.info(f"Añadiendo impuesto ID {purchase_taxes[0]} a la línea de factura")
                
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
