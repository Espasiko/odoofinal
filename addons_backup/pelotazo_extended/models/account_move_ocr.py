from odoo import models, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_process_ocr(self):
        self.ensure_one()
        # Aquí iría la lógica para enviar el PDF adjunto a FastAPI para OCR.
        # Por ahora, solo marcaremos como procesado para demostración.
        self.x_ocr_processed = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'OCR Procesado',
                'message': 'La factura ha sido marcada como procesada por OCR (simulado).',
                'type': 'success',
                'sticky': False,
            }
        }

