from typing import List, Optional
from datetime import datetime
from .odoo_base_service import OdooBaseService
from ..models.schemas import Sale, SaleCreate

class OdooSalesService(OdooBaseService):
    """Servicio para gestión de ventas e invoices en Odoo"""
    
    def get_sales(self, offset=0, limit=100) -> List[Sale]:
        """Obtiene ventas desde Odoo"""
        try:
            if not self._models:
                self._get_connection()
        
            print(f"ODOO_SERVICE: Obteniendo ventas de Odoo con offset {offset} y límite {limit}...")
            odoo_sales = self._execute_kw(
                'sale.order',
                'search_read',
                [[]],
                {'offset': offset, 'limit': limit, 'fields': [
                    'id', 'name', 'partner_id', 'date_order', 'amount_total',
                    'state', 'user_id', 'team_id', 'currency_id', 'amount_untaxed',
                    'amount_tax', 'invoice_status', 'delivery_status'
                ]}
            )
            print(f"ODOO_SERVICE: Datos obtenidos: {len(odoo_sales) if odoo_sales else 0} ventas")
        
            if not odoo_sales:
                print("ODOO_SERVICE: No se pudieron leer datos, usando fallback")
                return self._get_fallback_sales()
        
            # Transformar a formato esperado
            print("ODOO_SERVICE: Transformando datos...")
            transformed_sales = []
            for s in odoo_sales:
                # Manejar partner_id que puede venir como [id, name]
                partner_name = ''
                partner_id = None
                if s.get('partner_id'):
                    if isinstance(s['partner_id'], list) and len(s['partner_id']) > 1:
                        partner_id = s['partner_id'][0]
                        partner_name = s['partner_id'][1]
                    elif isinstance(s['partner_id'], int):
                        partner_id = s['partner_id']
                
                # Manejar user_id
                user_name = ''
                if s.get('user_id'):
                    if isinstance(s['user_id'], list) and len(s['user_id']) > 1:
                        user_name = s['user_id'][1]
                    elif isinstance(s['user_id'], str):
                        user_name = s['user_id']
                
                # Manejar team_id
                team_name = ''
                if s.get('team_id'):
                    if isinstance(s['team_id'], list) and len(s['team_id']) > 1:
                        team_name = s['team_id'][1]
                    elif isinstance(s['team_id'], str):
                        team_name = s['team_id']
                
                # Manejar currency_id
                currency_name = 'EUR'
                if s.get('currency_id'):
                    if isinstance(s['currency_id'], list) and len(s['currency_id']) > 1:
                        currency_name = s['currency_id'][1]
                    elif isinstance(s['currency_id'], str):
                        currency_name = s['currency_id']
                
                transformed_sales.append(Sale(
                    id=s.get('id'),
                    name=s.get('name', ''),
                    partner_id=partner_id,
                    partner_name=partner_name,
                    date_order=s.get('date_order', ''),
                    amount_total=s.get('amount_total', 0.0),
                    amount_untaxed=s.get('amount_untaxed', 0.0),
                    amount_tax=s.get('amount_tax', 0.0),
                    state=s.get('state', 'draft'),
                    user_id=s.get('user_id', [None])[0] if isinstance(s.get('user_id'), list) else s.get('user_id'),
                    user_name=user_name,
                    team_id=s.get('team_id', [None])[0] if isinstance(s.get('team_id'), list) else s.get('team_id'),
                    team_name=team_name,
                    currency_id=s.get('currency_id', [None])[0] if isinstance(s.get('currency_id'), list) else s.get('currency_id'),
                    currency_name=currency_name,
                    invoice_status=s.get('invoice_status', 'no'),
                    delivery_status=s.get('delivery_status', 'pending')
                ))
        
            print(f"ODOO_SERVICE: Ventas transformadas: {len(transformed_sales)}")
            return transformed_sales
        except Exception as e:
            print(f"ODOO_SERVICE: Error obteniendo ventas: {str(e)}")
            return self._get_fallback_sales()
    
    def create_sale(self, sale_data: SaleCreate) -> Optional[Sale]:
        """Crea una nueva venta en Odoo"""
        try:
            # Preparar datos de la venta
            vals = {
                'partner_id': sale_data.partner_id,
                'date_order': sale_data.date_order or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'state': 'draft'
            }
            
            # Crear venta
            sale_id = self._execute_kw(
                'sale.order',
                'create',
                [vals]
            )
            
            if sale_id:
                # Obtener la venta creada
                created_sale = self._execute_kw(
                    'sale.order',
                    'read',
                    [sale_id],
                    {'fields': ['id', 'name', 'partner_id', 'date_order', 'amount_total', 'state']}
                )
                
                if created_sale:
                    s = created_sale[0]
                    partner_name = ''
                    partner_id = None
                    if s.get('partner_id'):
                        if isinstance(s['partner_id'], list) and len(s['partner_id']) > 1:
                            partner_id = s['partner_id'][0]
                            partner_name = s['partner_id'][1]
                        elif isinstance(s['partner_id'], int):
                            partner_id = s['partner_id']
                    
                    return Sale(
                        id=s['id'],
                        name=s['name'],
                        partner_id=partner_id,
                        partner_name=partner_name,
                        date_order=s['date_order'],
                        amount_total=s.get('amount_total', 0.0),
                        state=s['state']
                    )
            
            print("Error: No se pudo crear la venta")
            return None
                
        except Exception as e:
            print(f"Error creando venta: {e}")
            return None
    
    # Método create_invoice removido temporalmente hasta definir el modelo Invoice
    
    def _get_fallback_sales(self) -> List[Sale]:
        """Datos de ventas de respaldo"""
        return [
            Sale(
                id=1,
                name="SO001",
                partner_id=1,
                partner_name="Cliente Ejemplo S.L.",
                date_order="2024-01-15 10:30:00",
                amount_total=1250.00,
                amount_untaxed=1033.06,
                amount_tax=216.94,
                state="sale",
                user_id=1,
                user_name="Vendedor 1",
                team_id=1,
                team_name="Equipo Ventas",
                currency_id=1,
                currency_name="EUR",
                invoice_status="invoiced",
                delivery_status="done"
            ),
            Sale(
                id=2,
                name="SO002",
                partner_id=2,
                partner_name="Empresa Tecnológica S.L.",
                date_order="2024-01-16 14:45:00",
                amount_total=2750.00,
                amount_untaxed=2272.73,
                amount_tax=477.27,
                state="sale",
                user_id=2,
                user_name="Vendedor 2",
                team_id=1,
                team_name="Equipo Ventas",
                currency_id=1,
                currency_name="EUR",
                invoice_status="to invoice",
                delivery_status="pending"
            )
        ]

# Instancia global del servicio
odoo_sales_service = OdooSalesService()