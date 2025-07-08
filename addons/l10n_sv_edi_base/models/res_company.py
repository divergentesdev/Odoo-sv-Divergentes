from odoo import models, fields, api


class ResCompany(models.Model):
    """Extiende res.company para agregar configuración EDI"""
    _inherit = 'res.company'

    # Configuración EDI
    l10n_sv_edi_enabled = fields.Boolean(
        string='Facturación Electrónica Habilitada',
        default=False,
        help='Habilita la facturación electrónica para El Salvador'
    )
    
    l10n_sv_edi_configuration_id = fields.Many2one(
        'l10n_sv.edi.configuration',
        string='Configuración EDI',
        help='Configuración de facturación electrónica'
    )
    
    # Datos del emisor para DTE
    l10n_sv_nit = fields.Char(
        string='NIT',
        help='Número de Identificación Tributaria'
    )
    
    l10n_sv_nrc = fields.Char(
        string='NRC',
        help='Número de Registro de Contribuyente'
    )
    
    l10n_sv_codigo_actividad = fields.Char(
        string='Código de Actividad Económica',
        help='Código de actividad económica según catálogo del MH'
    )
    
    l10n_sv_desc_actividad = fields.Char(
        string='Descripción de Actividad',
        help='Descripción de la actividad económica principal'
    )
    
    # Información geográfica usando módulos existentes
    l10n_sv_departamento = fields.Char(
        string='Código Departamento',
        help='Código del departamento según catálogo del MH'
    )
    
    l10n_sv_municipio = fields.Char(
        string='Código Municipio',
        help='Código del municipio según catálogo del MH'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Crear configuración EDI automáticamente para compañías de El Salvador"""
        companies = super().create(vals_list)
        for company in companies:
            if company.country_id and company.country_id.code == 'SV':
                company._create_edi_configuration()
        return companies

    def _create_edi_configuration(self):
        """Crea configuración EDI por defecto para la compañía"""
        self.ensure_one()
        if not self.l10n_sv_edi_configuration_id:
            config = self.env['l10n_sv.edi.configuration'].create({
                'company_id': self.id,
                'nit_emisor': self.l10n_sv_nit or '',
                'nrc_emisor': self.l10n_sv_nrc or '',
                'codigo_actividad': self.l10n_sv_codigo_actividad or '',
                'desc_actividad': self.l10n_sv_desc_actividad or '',
            })
            self.l10n_sv_edi_configuration_id = config.id

    def action_configure_edi(self):
        """Acción para abrir la configuración EDI"""
        self.ensure_one()
        if not self.l10n_sv_edi_configuration_id:
            self._create_edi_configuration()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configuración EDI',
            'res_model': 'l10n_sv.edi.configuration',
            'res_id': self.l10n_sv_edi_configuration_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def get_edi_configuration(self):
        """Obtiene la configuración EDI de la compañía"""
        self.ensure_one()
        if not self.l10n_sv_edi_configuration_id:
            self._create_edi_configuration()
        return self.l10n_sv_edi_configuration_id