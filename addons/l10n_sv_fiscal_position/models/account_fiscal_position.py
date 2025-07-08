import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class AccountFiscalPosition(models.Model):
    """Extensión de posiciones fiscales para El Salvador"""
    _inherit = 'account.fiscal.position'

    # Campos específicos para El Salvador
    code = fields.Char(
        string='Código',
        help='Código único para identificar la posición fiscal'
    )
    
    l10n_sv_document_type_id = fields.Many2one(
        'l10n_sv.document.type',
        string='Tipo de Documento DTE',
        help='Tipo de documento DTE que se genera automáticamente con esta posición fiscal'
    )
    
    l10n_sv_is_export = fields.Boolean(
        string='Es Exportación',
        default=False,
        help='Indica si esta posición fiscal es para operaciones de exportación'
    )
    
    l10n_sv_is_final_consumer = fields.Boolean(
        string='Es Consumidor Final',
        default=False,
        help='Indica si esta posición fiscal es para consumidores finales'
    )
    
    l10n_sv_is_taxpayer = fields.Boolean(
        string='Es Contribuyente',
        default=False,
        help='Indica si esta posición fiscal es para contribuyentes con NIT'
    )
    
    l10n_sv_is_excluded_subject = fields.Boolean(
        string='Es Sujeto Excluido',
        default=False,
        help='Indica si esta posición fiscal es para sujetos excluidos'
    )
    
    l10n_sv_is_withholding_agent = fields.Boolean(
        string='Es Agente Retenedor',
        default=False,
        help='Indica si aplica retenciones automáticas'
    )
    
    l10n_sv_withholding_type = fields.Selection([
        ('income', 'Retención de Renta'),
        ('vat', 'Retención de IVA'),
        ('both', 'Ambas Retenciones')
    ], string='Tipo de Retención',
       help='Tipo de retención que aplica esta posición fiscal')
    
    l10n_sv_auto_apply = fields.Boolean(
        string='Aplicar Automáticamente',
        default=True,
        help='Se aplica automáticamente según criterios del partner'
    )

    @api.model
    def get_fiscal_position_for_partner(self, partner_id, delivery_id=None):
        """
        Determina la posición fiscal automáticamente para un partner según
        las reglas tributarias de El Salvador
        """
        if not partner_id:
            return super().get_fiscal_position_for_partner(partner_id, delivery_id)
        
        partner = self.env['res.partner'].browse(partner_id)
        
        # 1. Verificar si el partner ya tiene posición fiscal manual
        if partner.property_account_position_id:
            return partner.property_account_position_id.id
        
        # 2. Aplicar reglas automáticas según normativa salvadoreña
        fiscal_position = self._determine_fiscal_position_sv(partner)
        
        if fiscal_position:
            return fiscal_position.id
        
        # 3. Fallback a lógica estándar de Odoo
        return super().get_fiscal_position_for_partner(partner_id, delivery_id)

    def _determine_fiscal_position_sv(self, partner):
        """
        Determina posición fiscal según reglas específicas validadas de El Salvador
        """
        # 1. Verificar si es consumidor final (lógica validada)
        if self._es_consumidor_final(partner):
            return self.search([
                ('l10n_sv_is_final_consumer', '=', True),
                ('l10n_sv_auto_apply', '=', True)
            ], limit=1)
        
        # 2. Operaciones de exportación
        if partner.country_id and partner.country_id.code != 'SV':
            return self.search([
                ('l10n_sv_is_export', '=', True),
                ('l10n_sv_auto_apply', '=', True)
            ], limit=1)
        
        # 3. Sujetos excluidos del IVA
        if hasattr(partner, 'l10n_sv_is_excluded_subject') and partner.l10n_sv_is_excluded_subject:
            return self.search([
                ('l10n_sv_is_excluded_subject', '=', True),
                ('l10n_sv_auto_apply', '=', True)
            ], limit=1)
        
        # 4. Contribuyentes con NIT válido
        if partner.vat and self._is_valid_nit(partner.vat):
            return self.search([
                ('l10n_sv_is_taxpayer', '=', True),
                ('l10n_sv_auto_apply', '=', True)
            ], limit=1)
        
        # 5. Por defecto: consumidor final
        return self.search([
            ('l10n_sv_is_final_consumer', '=', True),
            ('l10n_sv_auto_apply', '=', True)
        ], limit=1)

    def map_tax(self, tax_id, product=None, partner=None):
        """
        Mapeo de impuestos específico para El Salvador
        """
        result = super().map_tax(tax_id)
        
        # Aplicar lógica específica de mapeo de impuestos para El Salvador
        if self.country_id and self.country_id.code == 'SV':
            result = self._map_tax_sv(tax_id, product, partner, result)
        
        return result

    def _map_tax_sv(self, tax_id, product, partner, original_result):
        """
        Lógica específica de mapeo de impuestos para El Salvador
        """
        if not tax_id:
            return original_result
        
        tax = self.env['account.tax'].browse(tax_id)
        
        # Para exportaciones: remover IVA
        if self.l10n_sv_is_export and 'IVA' in (tax.name or ''):
            return self.env['account.tax']
        
        # Para sujetos excluidos: remover IVA
        if self.l10n_sv_is_excluded_subject and 'IVA' in (tax.name or ''):
            return self.env['account.tax']
        
        # Aplicar retenciones si es agente retenedor
        if self.l10n_sv_is_withholding_agent:
            return self._apply_withholding_taxes(tax_id, original_result)
        
        return original_result

    def _apply_withholding_taxes(self, original_tax_id, mapped_taxes):
        """
        Aplica impuestos de retención según el tipo configurado
        """
        withholding_taxes = mapped_taxes
        
        if self.l10n_sv_withholding_type in ['income', 'both']:
            # Buscar retención de renta
            income_withholding = self.env['account.tax'].search([
                ('l10n_sv_tax_code', 'like', 'RENT_%'),
                ('type_tax_use', '=', 'purchase'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            
            if income_withholding:
                withholding_taxes |= income_withholding
        
        if self.l10n_sv_withholding_type in ['vat', 'both']:
            # Buscar retención de IVA
            vat_withholding = self.env['account.tax'].search([
                ('l10n_sv_tax_code', '=', 'RET_IVA'),
                ('type_tax_use', '=', 'purchase'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            
            if vat_withholding:
                withholding_taxes |= vat_withholding
        
        return withholding_taxes

    @api.model
    def create_default_fiscal_positions_sv(self):
        """
        Crea las posiciones fiscales por defecto para El Salvador
        """
        country_sv = self.env.ref('base.sv')
        
        # Datos de posiciones fiscales predefinidas
        fiscal_positions_data = [
            {
                'name': 'El Salvador - Consumidor Final',
                'code': 'SV_FINAL_CONSUMER',
                'country_id': country_sv.id,
                'l10n_sv_is_final_consumer': True,
                'l10n_sv_document_type_id': self.env.ref('l10n_sv_document_type.document_type_01_factura').id,
                'note': 'Para ventas a consumidores finales sin NIT. Genera Factura (01).'
            },
            {
                'name': 'El Salvador - Contribuyente con NIT',
                'code': 'SV_TAXPAYER',
                'country_id': country_sv.id,
                'l10n_sv_is_taxpayer': True,
                'l10n_sv_document_type_id': self.env.ref('l10n_sv_document_type.document_type_03_ccf').id,
                'note': 'Para ventas a contribuyentes con NIT. Genera CCF (03).'
            },
            {
                'name': 'El Salvador - Exportación',
                'code': 'SV_EXPORT',
                'country_id': country_sv.id,
                'l10n_sv_is_export': True,
                'l10n_sv_document_type_id': self.env.ref('l10n_sv_document_type.document_type_11_exportacion').id,
                'note': 'Para operaciones de exportación. Genera Factura de Exportación (11). Exento de IVA.'
            },
            {
                'name': 'El Salvador - Sujeto Excluido',
                'code': 'SV_EXCLUDED',
                'country_id': country_sv.id,
                'l10n_sv_is_excluded_subject': True,
                'l10n_sv_document_type_id': self.env.ref('l10n_sv_document_type.document_type_14_sujeto_excluido').id,
                'note': 'Para sujetos excluidos del IVA. Genera Factura de Sujeto Excluido (14).'
            },
            {
                'name': 'El Salvador - Agente Retenedor',
                'code': 'SV_WITHHOLDING_AGENT',
                'country_id': country_sv.id,
                'l10n_sv_is_withholding_agent': True,
                'l10n_sv_withholding_type': 'both',
                'note': 'Para agentes retenedores. Aplica retenciones de renta e IVA automáticamente.'
            }
        ]
        
        created_positions = []
        for data in fiscal_positions_data:
            existing = self.search([('code', '=', data['code'])], limit=1)
            if not existing:
                position = self.create(data)
                created_positions.append(position)
                _logger.info(f'Posición fiscal creada: {position.name}')
        
        return created_positions

    def apply_taxes_to_fiscal_position(self):
        """
        Configura los mapeos de impuestos para esta posición fiscal
        """
        self.ensure_one()
        
        if self.l10n_sv_is_export:
            self._setup_export_tax_mapping()
        elif self.l10n_sv_is_excluded_subject:
            self._setup_excluded_subject_tax_mapping()
        elif self.l10n_sv_is_withholding_agent:
            self._setup_withholding_agent_tax_mapping()

    def _setup_export_tax_mapping(self):
        """Configura mapeo de impuestos para exportación"""
        # Remover IVA para exportaciones
        iva_tax = self.env['account.tax'].search([
            ('l10n_sv_tax_code', '=', 'IVA'),
            ('type_tax_use', '=', 'sale'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if iva_tax:
            self.env['account.fiscal.position.tax'].create({
                'position_id': self.id,
                'tax_src_id': iva_tax.id,
                'tax_dest_id': False  # Sin impuesto destino = exento
            })

    def _setup_excluded_subject_tax_mapping(self):
        """Configura mapeo de impuestos para sujetos excluidos"""
        # Similar a exportación, remover IVA
        self._setup_export_tax_mapping()

    def _setup_withholding_agent_tax_mapping(self):
        """Configura mapeo de impuestos para agentes retenedores"""
        # Agregar retenciones automáticas
        if self.l10n_sv_withholding_type in ['income', 'both']:
            self._add_income_withholding_mapping()
        
        if self.l10n_sv_withholding_type in ['vat', 'both']:
            self._add_vat_withholding_mapping()

    def _add_income_withholding_mapping(self):
        """Agrega mapeo de retención de renta"""
        # Implementar lógica de retención de renta
        pass

    def _add_vat_withholding_mapping(self):
        """Agrega mapeo de retención de IVA"""
        # Implementar lógica de retención de IVA
        pass

    def _es_consumidor_final(self, partner):
        """Determinar si el partner es consumidor final - LÓGICA VALIDADA"""
        return (
            not partner.vat or 
            not self._is_valid_nit(partner.vat) or
            (hasattr(partner, 'l10n_sv_is_final_consumer') and partner.l10n_sv_is_final_consumer) or
            partner.name == 'Consumidor final'
        )

    def _is_valid_nit(self, vat):
        """Validar formato de NIT salvadoreño"""
        if not vat:
            return False
        
        # Limpiar NIT
        nit = ''.join(filter(str.isdigit, vat))
        
        # NIT debe tener 14 dígitos
        return len(nit) == 14