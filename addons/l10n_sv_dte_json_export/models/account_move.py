from odoo import models

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_open_sv_attachment_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Descargar JSON adjuntos',
            'res_model': 'sv.invoice.attachment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_ids': [(6, 0, self.ids)]
            }
        }
