from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    x_ocr_processed = fields.Boolean(
        string='Procesado por OCR',
        help='Indica si la factura ha sido procesada por el sistema OCR.'
    )
    x_ocr_data_raw = fields.Text(
        string='Datos Brutos OCR',
        help='Almacena los datos brutos extraídos por el OCR para depuración o referencia.'
    )

