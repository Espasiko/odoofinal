from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_notas_inventario = fields.Text(
        string='Notas de Inventario',
        help='Notas adicionales sobre el estado o características del producto en inventario.'
    )
    x_estado_fisico = fields.Selection(
        [
            ('ok', 'OK'),
            ('roto', 'Roto'),
            ('para_reparar', 'Para Reparar'),
            ('devuelto', 'Devuelto'),
        ],
        string='Estado Físico',
        default='ok',
        help='Estado físico actual del producto en el inventario.'
    )

