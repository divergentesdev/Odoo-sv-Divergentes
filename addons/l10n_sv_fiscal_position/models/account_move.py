import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Extensión de facturas para integración con posiciones fiscales salvadoreñas"""
    _inherit = 'account.move'

    l10n_sv_fiscal_position_applied = fields.Boolean(
        string='Posición Fiscal Aplicada',
        readonly=True,
        help='Indica si se aplicó automáticamente una posición fiscal'
    )
    
    l10n_sv_withholding_applied = fields.Boolean(
        string='Retenciones Aplicadas',
        readonly=True,
        help='Indica si se aplicaron retenciones automáticamente'
    )
    
    l10n_sv_suggested_fiscal_position = fields.Many2one(
        'account.fiscal.position',
        string='Posición Fiscal Sugerida',
        compute='_compute_suggested_fiscal_position',
        help='Posición fiscal sugerida según criterios automáticos'
    )
    
    # Campos relacionados del partner para facilitar acceso en vistas
    partner_l10n_sv_taxpayer_type = fields.Selection(
        related='partner_id.l10n_sv_taxpayer_type',
        string='Tipo de Contribuyente',
        readonly=True
    )
    
    partner_l10n_sv_is_export_customer = fields.Boolean(
        related='partner_id.l10n_sv_is_export_customer',
        string='Cliente Exportación',
        readonly=True
    )
    
    partner_l10n_sv_is_excluded_subject = fields.Boolean(
        related='partner_id.l10n_sv_is_excluded_subject',
        string='Sujeto Excluido',
        readonly=True
    )
    
    partner_l10n_sv_is_withholding_agent = fields.Boolean(
        related='partner_id.l10n_sv_is_withholding_agent',
        string='Agente Retenedor',
        readonly=True
    )

    @api.depends('partner_id', 'move_type')
    def _compute_suggested_fiscal_position(self):
        """
        Calcula la posición fiscal sugerida según el partner y tipo de documento
        """
        for move in self:
            suggested = False
            
            if move.partner_id and move.move_type in ['out_invoice', 'out_refund']:
                # Usar la posición fiscal automática del partner
                suggested = move.partner_id.l10n_sv_fiscal_position_auto
                
                # Si no hay automática, intentar determinar por criterios
                if not suggested:
                    suggested = move._determine_fiscal_position_by_criteria()
            
            move.l10n_sv_suggested_fiscal_position = suggested

    def _determine_fiscal_position_by_criteria(self):
        """
        Determina posición fiscal basada en criterios específicos de la factura
        """
        # Si es factura de exportación (partner en el extranjero)
        if self.partner_id.country_id and self.partner_id.country_id.code != 'SV':
            return self.env['account.fiscal.position'].search([
                ('l10n_sv_is_export', '=', True),
                ('l10n_sv_auto_apply', '=', True)
            ], limit=1)
        
        # Si el partner tiene NIT
        if self.partner_id.vat and self.partner_id.l10n_latam_identification_type_id:
            id_type = self.partner_id.l10n_latam_identification_type_id.name or ''
            if 'NIT' in id_type.upper():
                return self.env['account.fiscal.position'].search([
                    ('l10n_sv_is_taxpayer', '=', True),
                    ('l10n_sv_auto_apply', '=', True)
                ], limit=1)
        
        # Por defecto: consumidor final
        return self.env['account.fiscal.position'].search([
            ('l10n_sv_is_final_consumer', '=', True),
            ('l10n_sv_auto_apply', '=', True)
        ], limit=1)

    @api.onchange('partner_id')
    def _onchange_partner_fiscal_position(self):
        """
        Aplica automáticamente la posición fiscal cuando cambia el partner
        """
        super()._onchange_partner_id()
        
        if self.partner_id and self.move_type in ['out_invoice', 'out_refund']:
            # Aplicar posición fiscal automática
            if self.partner_id.property_account_position_id:
                self.fiscal_position_id = self.partner_id.property_account_position_id
                self.l10n_sv_fiscal_position_applied = True
            elif self.l10n_sv_suggested_fiscal_position:
                self.fiscal_position_id = self.l10n_sv_suggested_fiscal_position
                self.l10n_sv_fiscal_position_applied = True
            
            # Determinar tipo de documento DTE automáticamente
            self._set_document_type_by_fiscal_position()

    def _set_document_type_by_fiscal_position(self):
        """
        Establece el tipo de documento DTE según la posición fiscal
        """
        if self.fiscal_position_id and self.fiscal_position_id.l10n_sv_document_type_id:
            self.l10n_sv_document_type_id = self.fiscal_position_id.l10n_sv_document_type_id

    @api.onchange('fiscal_position_id')
    def _onchange_fiscal_position_document_type(self):
        """
        Actualiza el tipo de documento cuando cambia la posición fiscal
        """
        if self.fiscal_position_id and self.fiscal_position_id.l10n_sv_document_type_id:
            self.l10n_sv_document_type_id = self.fiscal_position_id.l10n_sv_document_type_id

    def action_apply_suggested_fiscal_position(self):
        """
        Acción para aplicar la posición fiscal sugerida
        """
        self.ensure_one()
        
        if self.l10n_sv_suggested_fiscal_position:
            self.fiscal_position_id = self.l10n_sv_suggested_fiscal_position
            self.l10n_sv_fiscal_position_applied = True
            self._set_document_type_by_fiscal_position()
            
            # Recalcular impuestos
            self._recompute_tax_lines()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Posición Fiscal Aplicada'),
                    'message': _('Se aplicó la posición fiscal sugerida y se recalcularon los impuestos'),
                    'type': 'success'
                }
            }

    def action_apply_withholding_taxes(self):
        """
        Acción para aplicar retenciones automáticamente
        """
        self.ensure_one()
        
        if not self.fiscal_position_id or not self.fiscal_position_id.l10n_sv_is_withholding_agent:
            raise exceptions.UserError(_('Esta posición fiscal no requiere retenciones'))
        
        withholding_lines = self._calculate_withholding_taxes()
        
        if withholding_lines:
            self.l10n_sv_withholding_applied = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Retenciones Aplicadas'),
                    'message': _('Se aplicaron las retenciones automáticamente'),
                    'type': 'success'
                }
            }

    def _calculate_withholding_taxes(self):
        """
        Calcula y aplica retenciones según la posición fiscal
        """
        if not self.fiscal_position_id or not self.fiscal_position_id.l10n_sv_is_withholding_agent:
            return []
        
        withholding_lines = []
        withholding_type = self.fiscal_position_id.l10n_sv_withholding_type
        
        if withholding_type in ['income', 'both']:
            withholding_lines.extend(self._apply_income_withholding())
        
        if withholding_type in ['vat', 'both']:
            withholding_lines.extend(self._apply_vat_withholding())
        
        return withholding_lines

    def _apply_income_withholding(self):
        """
        Aplica retención de renta
        """
        # Buscar retención de renta apropiada
        income_withholding_tax = self.env['account.tax'].search([
            ('l10n_sv_tax_code', 'like', 'RENT_%'),
            ('type_tax_use', '=', 'purchase'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if income_withholding_tax:
            # Aplicar retención a las líneas que corresponda
            for line in self.invoice_line_ids:
                if line.price_total > 0:  # Solo en líneas con monto positivo
                    line.tax_ids = [(4, income_withholding_tax.id)]
        
        return []  # Retornar líneas de retención si se crean independientemente

    def _apply_vat_withholding(self):
        """
        Aplica retención de IVA
        """
        # Buscar retención de IVA
        vat_withholding_tax = self.env['account.tax'].search([
            ('l10n_sv_tax_code', '=', 'RET_IVA'),
            ('type_tax_use', '=', 'purchase'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if vat_withholding_tax:
            # Aplicar retención de IVA solo si hay IVA en la factura
            has_vat = any('IVA' in (tax.name or '') for line in self.invoice_line_ids for tax in line.tax_ids)
            
            if has_vat:
                for line in self.invoice_line_ids:
                    line.tax_ids = [(4, vat_withholding_tax.id)]
        
        return []

    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        """
        Override para incluir lógica específica de El Salvador
        """
        result = super()._recompute_tax_lines(recompute_tax_base_amount)
        
        # Aplicar lógica específica después del recálculo estándar
        if self.fiscal_position_id and self.move_type in ['out_invoice', 'out_refund']:
            self._apply_fiscal_position_sv_logic()
        
        return result

    def _apply_fiscal_position_sv_logic(self):
        """
        Aplica lógica específica de El Salvador después del recálculo de impuestos
        """
        fiscal_position = self.fiscal_position_id
        
        # Para exportaciones: verificar que no haya IVA
        if fiscal_position.l10n_sv_is_export:
            self._ensure_no_vat_on_export()
        
        # Para sujetos excluidos: verificar que no haya IVA
        elif fiscal_position.l10n_sv_is_excluded_subject:
            self._ensure_no_vat_on_excluded()
        
        # Para agentes retenedores: aplicar retenciones
        elif fiscal_position.l10n_sv_is_withholding_agent:
            self._apply_automatic_withholdings()

    def _ensure_no_vat_on_export(self):
        """
        Asegura que las exportaciones no tengan IVA
        """
        for line in self.line_ids:
            if line.tax_line_id and 'IVA' in (line.tax_line_id.name or ''):
                # Eliminar línea de IVA en exportaciones
                line.unlink()

    def _ensure_no_vat_on_excluded(self):
        """
        Asegura que sujetos excluidos no tengan IVA
        """
        self._ensure_no_vat_on_export()  # Misma lógica

    def _apply_automatic_withholdings(self):
        """
        Aplica retenciones automáticas si están configuradas
        """
        if not self.l10n_sv_withholding_applied:
            self._calculate_withholding_taxes()

    def action_post(self):
        """
        Override para validar configuración fiscal antes de confirmar
        """
        # Validar que las facturas de venta tengan posición fiscal
        for move in self:
            if move.move_type in ['out_invoice', 'out_refund'] and move.partner_id:
                if not move.fiscal_position_id and move.l10n_sv_suggested_fiscal_position:
                    # Aplicar automáticamente si hay sugerencia
                    move.fiscal_position_id = move.l10n_sv_suggested_fiscal_position
                    move.l10n_sv_fiscal_position_applied = True
                    move._set_document_type_by_fiscal_position()
        
        return super().action_post()

    @api.model
    def create(self, vals):
        """
        Override create para aplicar posición fiscal automáticamente
        """
        # Si es factura de venta y tiene partner, aplicar posición fiscal
        if vals.get('move_type') in ['out_invoice', 'out_refund'] and vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            
            if partner.property_account_position_id and not vals.get('fiscal_position_id'):
                vals['fiscal_position_id'] = partner.property_account_position_id.id
                vals['l10n_sv_fiscal_position_applied'] = True
        
        return super().create(vals)