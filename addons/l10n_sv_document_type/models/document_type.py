import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class L10nSvDocumentType(models.Model):
    """Tipos de documentos tributarios electrónicos según CAT_002_Tipo_de_Documento del MH"""
    _name = 'l10n_sv.document.type'
    _description = 'Tipo de Documento DTE El Salvador'
    _order = 'code'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre del tipo de documento'
    )
    
    code = fields.Selection([
        ('01', 'Factura'),
        ('03', 'Comprobante de Crédito Fiscal'),
        ('04', 'Nota de Remisión'),
        ('05', 'Nota de Crédito'),
        ('06', 'Nota de Débito'),
        ('07', 'Comprobante de Retención'),
        ('08', 'Comprobante de Liquidación'),
        ('09', 'Documento Contable de Liquidación'),
        ('11', 'Factura de Exportación'),
        ('14', 'Factura de Sujeto Excluido'),
        ('15', 'Comprobante de Donación'),
    ], string='Código DTE', required=True,
       help='Código según catálogo CAT_002_Tipo_de_Documento del MH')
    
    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia',
        help='Secuencia para numeración automática'
    )
    
    is_invoice = fields.Boolean(
        string='Es Factura',
        help='Indica si este tipo corresponde a una factura de venta'
    )
    
    is_credit_note = fields.Boolean(
        string='Es Nota de Crédito',
        help='Indica si este tipo corresponde a una nota de crédito'
    )
    
    is_debit_note = fields.Boolean(
        string='Es Nota de Débito',
        help='Indica si este tipo corresponde a una nota de débito'
    )
    
    is_export = fields.Boolean(
        string='Es Exportación',
        help='Indica si este tipo es para operaciones de exportación'
    )
    
    requires_incoterms = fields.Boolean(
        string='Requiere Incoterms',
        help='Indica si este tipo de documento requiere términos comerciales internacionales'
    )
    
    requires_retention = fields.Boolean(
        string='Requiere Retención',
        help='Indica si este tipo de documento maneja retenciones'
    )
    
    journal_type = fields.Selection([
        ('sale', 'Venta'),
        ('purchase', 'Compra'),
        ('general', 'General'),
    ], string='Tipo de Diario',
       help='Tipo de diario contable asociado')
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Determina si este tipo de documento está activo'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción detallada del tipo de documento'
    )
    
    validation_rules = fields.Text(
        string='Reglas de Validación',
        help='Reglas específicas de validación para este tipo de documento'
    )

    def action_show_code(self):
        """Acción para mostrar información del código"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Código DTE: {self.code}',
            'view_mode': 'form',
            'res_model': 'l10n_sv.document.type',
            'res_id': self.id,
            'target': 'new',
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Crear secuencia automáticamente al crear tipo de documento"""
        document_types = super().create(vals_list)
        for doc_type in document_types:
            if not doc_type.sequence_id:
                doc_type._create_sequence()
        return document_types

    def _create_sequence(self):
        """Crea secuencia automática para el tipo de documento"""
        self.ensure_one()
        sequence_vals = {
            'name': f'DTE {self.name} ({self.code})',
            'code': f'l10n_sv.dte.{self.code}',
            'prefix': f'DTE-{self.code}-',
            'suffix': '',
            'padding': 15,  # 15 dígitos según especificación MH
            'number_next': 1,
            'number_increment': 1,
            'implementation': 'standard',
            'company_id': False,  # Disponible para todas las compañías
        }
        self.sequence_id = self.env['ir.sequence'].create(sequence_vals)

    def get_next_number(self, company_id=None):
        """Obtiene el siguiente número de la secuencia"""
        self.ensure_one()
        if not self.sequence_id:
            self._create_sequence()
        return self.sequence_id.next_by_id()

    def validate_document_data(self, move_vals):
        """Valida los datos del documento según el tipo DTE"""
        self.ensure_one()
        errors = []
        
        # Validaciones específicas por tipo de documento
        if self.code == '11' and self.requires_incoterms:  # Factura de Exportación
            if not move_vals.get('invoice_incoterm_id'):
                errors.append(_('Las facturas de exportación requieren Incoterms'))
        
        if self.code == '07' and self.requires_retention:  # Comprobante de Retención
            if not move_vals.get('l10n_sv_retention_amount'):
                errors.append(_('Los comprobantes de retención requieren monto de retención'))
        
        # Validación de partner según tipo documento
        partner_id = move_vals.get('partner_id')
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if self.is_export and partner.country_id.code == 'SV':
                errors.append(_('Las facturas de exportación no pueden ser para clientes nacionales'))
        
        if errors:
            raise exceptions.ValidationError('\n'.join(errors))
        
        return True

    @api.depends('code')
    def name_get(self):
        """Personaliza la visualización del nombre"""
        result = []
        for doc_type in self:
            name = f"[{doc_type.code}] {doc_type.name}"
            result.append((doc_type.id, name))
        return result

    @api.model
    def get_document_type_for_move(self, move_type, partner=None, is_export=False):
        """Determina el tipo de documento DTE según el tipo de asiento contable"""
        domain = [('active', '=', True)]
        
        if move_type == 'out_invoice':
            if is_export:
                domain.append(('code', '=', '11'))  # Factura de Exportación
            elif partner and partner.l10n_sv_document_type_code == '36':  # NIT
                domain.append(('code', '=', '03'))  # CCF
            else:
                domain.append(('code', '=', '01'))  # Factura
        elif move_type == 'out_refund':
            domain.append(('code', '=', '05'))  # Nota de Crédito
        elif move_type == 'in_invoice':
            domain.append(('journal_type', '=', 'purchase'))
        else:
            return None
        
        return self.search(domain, limit=1)

    def generate_json_dte(self, move_id):
        """Método puente para generar JSON DTE usando el generador apropiado"""
        self.ensure_one()
        
        # Buscar generador apropiado para este tipo de documento
        generator = self.env['l10n_sv.json.generator'].search([
            ('document_type_id', '=', self.id),
            ('active', '=', True)
        ], limit=1)
        
        if not generator:
            raise exceptions.UserError(_(
                'No se encontró un generador JSON activo para el tipo de documento %s'
            ) % self.name)
        
        # Generar JSON usando el generador
        json_data = generator.generate_json_dte(move_id)
        
        # Formatear la salida usando el método del generador
        document_type_code = self.code
        formatted_json = generator.format_json_output(json_data, document_type_code)
        
        return formatted_json

    def validate_json(self, json_data, move):
        """Método puente para validar JSON DTE usando el generador apropiado"""
        self.ensure_one()
        
        # Buscar generador apropiado para este tipo de documento
        generator = self.env['l10n_sv.json.generator'].search([
            ('document_type_id', '=', self.id),
            ('active', '=', True)
        ], limit=1)
        
        if not generator:
            raise exceptions.UserError(_(
                'No se encontró un generador JSON activo para el tipo de documento %s'
            ) % self.name)
        
        # Delegar al generador
        return generator.validate_json(json_data, move)


class L10nSvDocumentTypeCategory(models.Model):
    """Categorías de documentos DTE para mejor organización"""
    _name = 'l10n_sv.document.type.category'
    _description = 'Categoría de Documentos DTE'
    
    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre de la categoría'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción de la categoría'
    )
    
    document_type_ids = fields.One2many(
        'l10n_sv.document.type',
        'category_id',
        string='Tipos de Documento'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )


# Extender el modelo de tipos de documento para agregar categoría
class L10nSvDocumentTypeWithCategory(models.Model):
    _inherit = 'l10n_sv.document.type'
    
    category_id = fields.Many2one(
        'l10n_sv.document.type.category',
        string='Categoría',
        help='Categoría del tipo de documento'
    )
