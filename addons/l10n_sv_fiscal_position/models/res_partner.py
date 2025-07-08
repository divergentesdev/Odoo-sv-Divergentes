import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Extensión de partners para clasificación fiscal salvadoreña"""
    _inherit = 'res.partner'

    # Campos de clasificación fiscal específicos para El Salvador
    l10n_sv_is_export_customer = fields.Boolean(
        string='Cliente de Exportación',
        default=False,
        help='Indica si este cliente realiza compras para exportación'
    )
    
    l10n_sv_is_excluded_subject = fields.Boolean(
        string='Sujeto Excluido',
        default=False,
        help='Indica si este partner está excluido del pago de IVA'
    )
    
    l10n_sv_is_withholding_agent = fields.Boolean(
        string='Agente Retenedor',
        default=False,
        help='Indica si este partner es agente de retención'
    )
    
    l10n_sv_withholding_type = fields.Selection([
        ('income', 'Retención de Renta'),
        ('vat', 'Retención de IVA'),
        ('both', 'Ambas Retenciones')
    ], string='Tipo de Retención',
       help='Tipo de retención que aplica a este partner')
    
    l10n_sv_taxpayer_type = fields.Selection([
        ('final_consumer', 'Consumidor Final'),
        ('taxpayer', 'Contribuyente'),
        ('export', 'Exportación'),
        ('excluded', 'Sujeto Excluido'),
        ('government', 'Entidad Gubernamental')
    ], string='Tipo de Contribuyente',
       compute='_compute_taxpayer_type',
       store=True,
       help='Clasificación automática del tipo de contribuyente')
    
    l10n_sv_fiscal_position_auto = fields.Many2one(
        'account.fiscal.position',
        string='Posición Fiscal Automática',
        compute='_compute_fiscal_position_auto',
        help='Posición fiscal determinada automáticamente'
    )

    @api.depends('vat', 'l10n_latam_identification_type_id', 'l10n_sv_is_export_customer', 
                 'l10n_sv_is_excluded_subject', 'country_id')
    def _compute_taxpayer_type(self):
        """
        Determina automáticamente el tipo de contribuyente según criterios salvadoreños
        """
        for partner in self:
            taxpayer_type = 'final_consumer'  # Por defecto
            
            # Verificar si es de exportación
            if partner.l10n_sv_is_export_customer:
                taxpayer_type = 'export'
            
            # Verificar si es sujeto excluido
            elif partner.l10n_sv_is_excluded_subject:
                taxpayer_type = 'excluded'
            
            # Verificar si tiene NIT (contribuyente)
            elif partner.vat and partner.l10n_latam_identification_type_id:
                id_type_name = partner.l10n_latam_identification_type_id.name or ''
                if 'NIT' in id_type_name.upper():
                    taxpayer_type = 'taxpayer'
                elif 'GOBIERNO' in id_type_name.upper() or 'ENTIDAD' in id_type_name.upper():
                    taxpayer_type = 'government'
            
            partner.l10n_sv_taxpayer_type = taxpayer_type

    @api.depends('l10n_sv_taxpayer_type', 'country_id')
    def _compute_fiscal_position_auto(self):
        """
        Determina automáticamente la posición fiscal según el tipo de contribuyente
        """
        for partner in self:
            fiscal_position = False
            
            if partner.country_id and partner.country_id.code == 'SV':
                # Buscar posición fiscal según tipo de contribuyente
                if partner.l10n_sv_taxpayer_type == 'export':
                    fiscal_position = self.env['account.fiscal.position'].search([
                        ('l10n_sv_is_export', '=', True),
                        ('l10n_sv_auto_apply', '=', True)
                    ], limit=1)
                
                elif partner.l10n_sv_taxpayer_type == 'excluded':
                    fiscal_position = self.env['account.fiscal.position'].search([
                        ('l10n_sv_is_excluded_subject', '=', True),
                        ('l10n_sv_auto_apply', '=', True)
                    ], limit=1)
                
                elif partner.l10n_sv_taxpayer_type == 'taxpayer':
                    fiscal_position = self.env['account.fiscal.position'].search([
                        ('l10n_sv_is_taxpayer', '=', True),
                        ('l10n_sv_auto_apply', '=', True)
                    ], limit=1)
                
                elif partner.l10n_sv_taxpayer_type == 'final_consumer':
                    fiscal_position = self.env['account.fiscal.position'].search([
                        ('l10n_sv_is_final_consumer', '=', True),
                        ('l10n_sv_auto_apply', '=', True)
                    ], limit=1)
            
            partner.l10n_sv_fiscal_position_auto = fiscal_position

    @api.onchange('l10n_sv_taxpayer_type')
    def _onchange_taxpayer_type(self):
        """
        Actualiza la posición fiscal cuando cambia el tipo de contribuyente
        """
        if self.l10n_sv_fiscal_position_auto and not self.property_account_position_id:
            self.property_account_position_id = self.l10n_sv_fiscal_position_auto

    @api.onchange('l10n_sv_is_export_customer')
    def _onchange_export_customer(self):
        """Actualiza clasificación cuando se marca como cliente de exportación"""
        if self.l10n_sv_is_export_customer:
            self.l10n_sv_is_excluded_subject = False

    @api.onchange('l10n_sv_is_excluded_subject')
    def _onchange_excluded_subject(self):
        """Actualiza clasificación cuando se marca como sujeto excluido"""
        if self.l10n_sv_is_excluded_subject:
            self.l10n_sv_is_export_customer = False

    def action_apply_automatic_fiscal_position(self):
        """
        Acción para aplicar automáticamente la posición fiscal
        """
        for partner in self:
            if partner.l10n_sv_fiscal_position_auto:
                partner.property_account_position_id = partner.l10n_sv_fiscal_position_auto
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Posición Fiscal Aplicada'),
                'message': _('Se ha aplicado automáticamente la posición fiscal'),
                'type': 'success'
            }
        }

    def get_fiscal_position_for_invoice(self, invoice_type='out_invoice'):
        """
        Obtiene la posición fiscal específica según el tipo de factura
        """
        self.ensure_one()
        
        # Si ya tiene posición fiscal manual, usarla
        if self.property_account_position_id:
            return self.property_account_position_id
        
        # Determinar automáticamente según reglas salvadoreñas
        return self.l10n_sv_fiscal_position_auto

    @api.model
    def create(self, vals):
        """Override create para aplicar posición fiscal automáticamente"""
        partner = super().create(vals)
        
        # Aplicar posición fiscal automática si está en El Salvador
        if partner.country_id and partner.country_id.code == 'SV':
            if partner.l10n_sv_fiscal_position_auto and not partner.property_account_position_id:
                partner.property_account_position_id = partner.l10n_sv_fiscal_position_auto
        
        return partner

    def write(self, vals):
        """Override write para actualizar posición fiscal cuando cambian datos relevantes"""
        result = super().write(vals)
        
        # Campos que pueden afectar la posición fiscal
        fiscal_relevant_fields = [
            'vat', 'l10n_latam_identification_type_id', 'l10n_sv_is_export_customer',
            'l10n_sv_is_excluded_subject', 'country_id'
        ]
        
        if any(field in vals for field in fiscal_relevant_fields):
            for partner in self:
                if partner.country_id and partner.country_id.code == 'SV':
                    # Actualizar posición fiscal automática si no tiene una manual
                    if partner.l10n_sv_fiscal_position_auto and not partner.property_account_position_id:
                        partner.property_account_position_id = partner.l10n_sv_fiscal_position_auto
        
        return result

    @api.model
    def get_partner_tax_configuration(self, partner_id):
        """
        Obtiene la configuración de impuestos específica para un partner
        """
        partner = self.browse(partner_id)
        
        config = {
            'apply_vat': True,
            'apply_withholding': False,
            'withholding_type': False,
            'document_type': 'factura',
            'fiscal_position_id': False
        }
        
        if partner.l10n_sv_taxpayer_type == 'export':
            config.update({
                'apply_vat': False,
                'document_type': 'export_invoice'
            })
        
        elif partner.l10n_sv_taxpayer_type == 'excluded':
            config.update({
                'apply_vat': False,
                'document_type': 'excluded_subject_invoice'
            })
        
        elif partner.l10n_sv_taxpayer_type == 'taxpayer':
            config.update({
                'document_type': 'ccf'
            })
        
        if partner.l10n_sv_is_withholding_agent:
            config.update({
                'apply_withholding': True,
                'withholding_type': partner.l10n_sv_withholding_type
            })
        
        if partner.property_account_position_id:
            config['fiscal_position_id'] = partner.property_account_position_id.id
        
        return config
    
    @api.model
    def apply_fiscal_positions_bulk(self, partner_ids=None):
        """
        Método para aplicar posiciones fiscales de forma masiva
        """
        if partner_ids:
            partners = self.browse(partner_ids)
        else:
            # Si no se especifican IDs, aplicar a todos los partners de El Salvador sin posición fiscal
            partners = self.search([
                ('country_id.code', '=', 'SV'),
                ('property_account_position_id', '=', False),
                ('l10n_sv_fiscal_position_auto', '!=', False)
            ])
        
        applied_count = 0
        for partner in partners:
            if partner.l10n_sv_fiscal_position_auto and not partner.property_account_position_id:
                partner.property_account_position_id = partner.l10n_sv_fiscal_position_auto
                applied_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Aplicación Masiva Completada'),
                'message': _('Se aplicaron posiciones fiscales a %d partners') % applied_count,
                'type': 'success'
            }
        }
    
    def action_apply_fiscal_position_sv_only(self):
        """
        Acción específica para partners de El Salvador con validaciones
        """
        sv_partners = self.filtered(lambda p: p.country_id and p.country_id.code == 'SV')
        applied_count = 0
        skipped_count = 0
        
        for partner in sv_partners:
            if partner.l10n_sv_fiscal_position_auto and not partner.property_account_position_id:
                partner.property_account_position_id = partner.l10n_sv_fiscal_position_auto
                applied_count += 1
            else:
                skipped_count += 1
        
        if applied_count > 0:
            message = _('Se aplicaron posiciones fiscales a %d partners') % applied_count
            if skipped_count > 0:
                message += _('. Se omitieron %d partners (ya tenían posición fiscal o no es aplicable)') % skipped_count
            msg_type = 'success'
        else:
            message = _('No se pudo aplicar ninguna posición fiscal automática')
            msg_type = 'warning'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Aplicación de Posiciones Fiscales'),
                'message': message,
                'type': msg_type
            }
        }