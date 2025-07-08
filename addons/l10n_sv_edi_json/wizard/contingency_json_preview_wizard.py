import json
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class ContingencyJsonPreviewWizard(models.TransientModel):
    """Wizard para previsualizar JSON de Contingencias"""
    _name = 'l10n_sv.contingency.json.preview.wizard'
    _description = 'Wizard Vista Previa JSON Contingencia'

    contingency_id = fields.Many2one(
        'l10n_sv.contingency',
        string='Contingencia',
        readonly=True,
        required=True
    )
    
    json_content = fields.Text(
        string='JSON Contingencia',
        required=True
    )
    
    def action_download_json(self):
        """Acción para descargar JSON como archivo"""
        self.ensure_one()
        
        if not self.json_content:
            raise exceptions.UserError(_('No hay contenido JSON para descargar'))
        
        filename = f"Contingencia_{self.contingency_id.name or 'DRAFT'}.json"
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=json_content&filename_field=filename&download=true',
            'target': 'self'
        }