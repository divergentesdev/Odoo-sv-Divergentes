import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Extiende account.move para integrar con tipos de documentos DTE y catálogos MH"""
    _inherit = 'account.move'

    # Tipo de documento DTE específico
    l10n_sv_document_type_id = fields.Many2one(
        'l10n_sv.document.type',
        string='Tipo de Documento DTE',
        help='Tipo específico de documento tributario electrónico'
    )
    
    # Establecimiento y punto de venta
    l10n_sv_establishment_id = fields.Many2one(
        'l10n_sv.establishment',
        string='Establecimiento',
        help='Establecimiento que emite el documento'
    )
    
    l10n_sv_point_of_sale_id = fields.Many2one(
        'l10n_sv.point.of.sale',
        string='Punto de Venta',
        help='Punto de venta que emite el documento'
    )
    
    # Campos para integración con catálogos existentes
    
    # Integración con l10n_sv_payment (términos de pago)
    l10n_sv_payment_term_code = fields.Selection([
        ('01', 'Días'),
        ('02', 'Meses'),
        ('03', 'Años')
    ], related='invoice_payment_term_id.plazo',
       string='Código Plazo',
       help='Código de plazo según catálogo CAT_018'
    )
    
    l10n_sv_payment_term_period = fields.Integer(
        related='invoice_payment_term_id.periodo',
        string='Período Plazo',
        help='Valor numérico del plazo'
    )
    
    # Integración con l10n_sv_incoterms (para exportaciones)
    l10n_sv_incoterm_code = fields.Char(
        related='invoice_incoterm_id.code_dgii',
        string='Código Incoterm DGII',
        help='Código DGII del Incoterm para exportaciones'
    )
    
    # Campos adicionales para DTE
    l10n_sv_operation_type = fields.Selection([
        ('1', 'Venta'),
        ('2', 'Operaciones a cuenta de terceros'),
        ('3', 'Otros'),
    ], string='Tipo de Operación', default='1',
       help='Tipo de operación según especificaciones MH')
    
    l10n_sv_payment_condition = fields.Selection([
        ('1', 'Contado'),
        ('2', 'Crédito'),
        ('3', 'Otro'),
    ], string='Condición de Operación', default='1',
       help='Condición de pago de la operación')
    
    # Montos específicos para DTE
    l10n_sv_total_no_gravado = fields.Monetary(
        string='Total No Gravado',
        currency_field='currency_id',
        help='Monto total no gravado con IVA'
    )
    
    l10n_sv_total_exento = fields.Monetary(
        string='Total Exento',
        currency_field='currency_id',
        help='Monto total exento de IVA'
    )
    
    l10n_sv_total_gravado = fields.Monetary(
        string='Total Gravado',
        currency_field='currency_id',
        help='Monto total gravado con IVA'
    )
    
    # Campos para retenciones
    l10n_sv_retention_amount = fields.Monetary(
        string='Monto Retención',
        currency_field='currency_id',
        help='Monto de retención aplicado'
    )
    
    l10n_sv_retention_rate = fields.Float(
        string='% Retención',
        help='Porcentaje de retención aplicado'
    )

    @api.depends('l10n_sv_document_type_id', 'partner_id', 'company_id')
    def _compute_l10n_sv_establishment_domain(self):
        """Computa el dominio para establecimientos según la compañía"""
        for move in self:
            move.l10n_sv_establishment_domain = [
                ('company_id', '=', move.company_id.id),
                ('active', '=', True)
            ]

    l10n_sv_establishment_domain = fields.Char(
        compute='_compute_l10n_sv_establishment_domain',
        help='Dominio para filtrar establecimientos'
    )

    @api.onchange('l10n_sv_establishment_id')
    def _onchange_establishment_id(self):
        """Actualiza el dominio de puntos de venta al cambiar establecimiento"""
        if self.l10n_sv_establishment_id:
            return {
                'domain': {
                    'l10n_sv_point_of_sale_id': [
                        ('establishment_id', '=', self.l10n_sv_establishment_id.id),
                        ('active', '=', True)
                    ]
                }
            }
        else:
            self.l10n_sv_point_of_sale_id = False
            return {'domain': {'l10n_sv_point_of_sale_id': []}}

    @api.onchange('move_type', 'partner_id')
    def _onchange_move_type_partner(self):
        """Determina automáticamente el tipo de documento DTE"""
        if self.l10n_sv_edi_applicable:
            is_export = self._is_export_operation()
            document_type = self.env['l10n_sv.document.type'].get_document_type_for_move(
                self.move_type, self.partner_id, is_export
            )
            if document_type:
                self.l10n_sv_document_type_id = document_type
                # Actualizar el tipo de documento EDI base
                self.l10n_sv_edi_tipo_documento = document_type.code

    def _is_export_operation(self):
        """Determina si es una operación de exportación"""
        if self.partner_id and self.partner_id.country_id:
            return self.partner_id.country_id.code != 'SV'
        return False

    @api.onchange('l10n_sv_document_type_id')
    def _onchange_document_type_id(self):
        """Actualiza campos relacionados al cambiar tipo de documento"""
        if self.l10n_sv_document_type_id:
            # Establecer establecimiento por defecto
            if not self.l10n_sv_establishment_id:
                default_establishment = self.env['l10n_sv.establishment'].search([
                    ('company_id', '=', self.company_id.id),
                    ('is_main', '=', True),
                    ('active', '=', True)
                ], limit=1)
                if default_establishment:
                    self.l10n_sv_establishment_id = default_establishment

    def _compute_l10n_sv_totals(self):
        """Calcula los totales específicos para DTE"""
        for move in self:
            total_no_gravado = 0.0
            total_exento = 0.0
            total_gravado = 0.0
            
            for line in move.invoice_line_ids:
                if line.display_type not in ('line_section', 'line_note'):
                    line_total = line.price_subtotal
                    
                    # Clasificar según impuestos aplicados
                    has_iva = any(tax.code_dgii == '20' for tax in line.tax_ids if hasattr(tax, 'code_dgii'))
                    is_exempt = any(tax.code_dgii == 'C3' for tax in line.tax_ids if hasattr(tax, 'code_dgii'))
                    
                    if is_exempt:
                        total_exento += line_total
                    elif has_iva:
                        total_gravado += line_total
                    else:
                        total_no_gravado += line_total
            
            move.l10n_sv_total_no_gravado = total_no_gravado
            move.l10n_sv_total_exento = total_exento
            move.l10n_sv_total_gravado = total_gravado

    @api.depends('invoice_line_ids.tax_ids', 'invoice_line_ids.price_subtotal')
    def _compute_l10n_sv_computed_totals(self):
        """Versión computada de los totales DTE"""
        self._compute_l10n_sv_totals()

    # Hacer los campos computados
    l10n_sv_total_no_gravado = fields.Monetary(
        string='Total No Gravado',
        currency_field='currency_id',
        compute='_compute_l10n_sv_computed_totals',
        store=True,
        help='Monto total no gravado con IVA'
    )
    
    l10n_sv_total_exento = fields.Monetary(
        string='Total Exento',
        currency_field='currency_id',
        compute='_compute_l10n_sv_computed_totals',
        store=True,
        help='Monto total exento de IVA'
    )
    
    l10n_sv_total_gravado = fields.Monetary(
        string='Total Gravado',
        currency_field='currency_id',
        compute='_compute_l10n_sv_computed_totals',
        store=True,
        help='Monto total gravado con IVA'
    )

    def _generate_dte_numero_control(self):
        """Genera número de control usando establecimiento y tipo de documento"""
        self.ensure_one()
        
        if not self.l10n_sv_document_type_id:
            raise exceptions.UserError(_('Debe especificar el tipo de documento DTE'))
        
        if not self.l10n_sv_establishment_id:
            raise exceptions.UserError(_('Debe especificar el establecimiento'))
        
        # Buscar configuración de secuencia para establecimiento y tipo de documento
        sequence_config = self.env['l10n_sv.establishment.sequence'].search([
            ('establishment_id', '=', self.l10n_sv_establishment_id.id),
            ('document_type_id', '=', self.l10n_sv_document_type_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not sequence_config:
            # Crear configuración automáticamente
            sequence_config = self.env['l10n_sv.establishment.sequence'].create({
                'establishment_id': self.l10n_sv_establishment_id.id,
                'document_type_id': self.l10n_sv_document_type_id.id,
            })
        
        return sequence_config.get_next_number()

    def _validate_dte_requirements(self):
        """Valida los requisitos específicos del tipo de documento DTE"""
        self.ensure_one()
        
        if not self.l10n_sv_document_type_id:
            return
        
        # Usar el método de validación del tipo de documento
        move_vals = {
            'partner_id': self.partner_id.id,
            'invoice_incoterm_id': self.invoice_incoterm_id.id if self.invoice_incoterm_id else None,
            'l10n_sv_retention_amount': self.l10n_sv_retention_amount,
        }
        
        self.l10n_sv_document_type_id.validate_document_data(move_vals)

    def _post(self, soft=True):
        """Override para validar DTE antes de confirmar"""
        for move in self:
            if move.l10n_sv_edi_applicable:
                move._validate_dte_requirements()
                # Generar número de control si no existe
                if not move.l10n_sv_edi_numero_control:
                    # move.l10n_sv_edi_numero_control = move._generate_dte_numero_control()  # Desactivado - se genera en json_generator
                    pass  # Se genera en json_generator
        
        return super()._post(soft)


class AccountMoveLine(models.Model):
    """Extiende account.move.line para integrar con catálogos MH"""
    _inherit = 'account.move.line'

    # Integración con l10n_sv_uom (unidades de medida)
    l10n_sv_uom_code = fields.Integer(
        string='Código UOM MH',
        compute='_compute_l10n_sv_uom_code',
        store=True,
        help='Código de unidad de medida según catálogo CAT_014 del MH'
    )

    @api.depends('product_id', 'product_id.uom_id')
    def _compute_l10n_sv_uom_code(self):
        """Calcula el código UOM desde el producto"""
        for line in self:
            if line.product_id and line.product_id.uom_id:
                # Verificar si la UOM tiene el campo code (del módulo l10n_sv_uom)
                if hasattr(line.product_id.uom_id, 'code'):
                    line.l10n_sv_uom_code = line.product_id.uom_id.code
                else:
                    line.l10n_sv_uom_code = 0
            else:
                line.l10n_sv_uom_code = 0
    
    # Campos específicos para líneas DTE
    l10n_sv_item_type = fields.Selection([
        ('1', 'Producto'),
        ('2', 'Servicio'),
        ('3', 'Producto y Servicio'),
        ('4', 'Otros tributos, cargos y descuentos'),
    ], string='Tipo de Item', default='1',
       help='Tipo de item según especificaciones DTE')
    
    l10n_sv_tributo_codigo = fields.Char(
        string='Código Tributo',
        help='Código del tributo aplicado a esta línea'
    )

    @api.onchange('product_id')
    def _onchange_product_dte(self):
        """Actualiza campos DTE al cambiar producto"""
        if self.product_id:
            # Determinar tipo de item según el producto
            if self.product_id.type == 'service':
                self.l10n_sv_item_type = '2'  # Servicio
            else:
                self.l10n_sv_item_type = '1'  # Producto
    
    @api.depends('tax_ids')
    def _compute_l10n_sv_tributos(self):
        """Calcula los códigos de tributos aplicados"""
        for line in self:
            tributos = []
            for tax in line.tax_ids:
                if hasattr(tax, 'code_dgii') and tax.code_dgii:
                    tributos.append(tax.code_dgii)
            line.l10n_sv_tributo_codigo = ','.join(tributos) if tributos else ''

    l10n_sv_tributo_codigo = fields.Char(
        string='Códigos Tributo',
        compute='_compute_l10n_sv_tributos',
        store=True,
        help='Códigos de tributos aplicados (separados por coma)'
    )