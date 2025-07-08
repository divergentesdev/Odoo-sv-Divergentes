from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import base64
import io
import zipfile
import re

class InvoiceAttachmentWizard(models.TransientModel):
    _name = 'sv.invoice.attachment.wizard'
    _description = 'Exportar adjuntos de facturas'

    date_from = fields.Date('Desde')
    date_to = fields.Date('Hasta')
    invoice_ids = fields.Many2many('account.move', string='Facturas')
    zip_file = fields.Binary('Archivo ZIP', readonly=True)
    zip_filename = fields.Char('Nombre del ZIP')

    def action_download_attachments(self):
        domain = []
        if self.invoice_ids:
            domain.append(('id', 'in', self.invoice_ids.ids))
        else:
            domain += [('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'))]
            if self.date_from:
                domain.append(('invoice_date', '>=', self.date_from))
            if self.date_to:
                domain.append(('invoice_date', '<=', self.date_to))

        invoices = self.env['account.move'].search(domain)
        if not invoices:
            raise UserError("No se encontraron facturas con los criterios especificados.")

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            for move in invoices:
                for attachment in move.attachment_ids:
                    if not attachment.datas:
                        continue
                    safe_name = re.sub(r'[^\w\-.]', '_', attachment.name)
                    filename = f"{move.name}_{safe_name}"
                    zip_file.writestr(filename, base64.b64decode(attachment.datas))

        buffer.seek(0)
        b64_zip = base64.b64encode(buffer.read())
        self.write({
            'zip_file': b64_zip,
            'zip_filename': f"Adjuntos_Facturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sv.invoice.attachment.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
        