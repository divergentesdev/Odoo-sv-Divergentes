import uuid
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Extiende account.move para agregar funcionalidad EDI de El Salvador"""
    _inherit = 'account.move'

    # Campos EDI específicos de El Salvador
    l10n_sv_edi_uuid = fields.Char(
        string='UUID DTE',
        copy=False,
        help='Identificador único del DTE generado por el sistema'
    )
    
    l10n_sv_edi_numero_control = fields.Char(
        string='Número de Control',
        copy=False,
        help='Número de control DTE asignado por el sistema'
    )
    
    l10n_sv_edi_codigo_generacion = fields.Char(
        string='Código de Generación',
        copy=False,
        help='Código de generación único del DTE'
    )
    
    l10n_sv_edi_sello_recepcion = fields.Char(
        string='Sello de Recepción',
        copy=False,
        help='Sello de recepción otorgado por el MH'
    )
    
    l10n_sv_edi_fecha_recepcion = fields.Datetime(
        string='Fecha de Recepción MH',
        copy=False,
        help='Fecha y hora de recepción por parte del MH'
    )
    
    l10n_sv_edi_tipo_documento = fields.Selection([
        ('01', 'Factura'),
        ('03', 'Comprobante de Crédito Fiscal'),
        ('04', 'Nota de Remisión'),
        ('05', 'Nota de Crédito'),
        ('06', 'Nota de Débito'),
        ('07', 'Comprobante de Retención'),
        ('08', 'Comprobante de Liquidación'),
        ('09', 'Documento Contable de Liquidación'),
        ('11', 'Factura de Exportación'),
        ('14', 'Factura de Sujeto Excluido')
    ], string='Tipo de Documento DTE',
       help='Tipo de documento tributario electrónico')
    
    l10n_sv_edi_estado = fields.Selection([
        ('no_aplica', 'No Aplica'),
        ('pendiente', 'Pendiente'),
        ('generado', 'DTE Generado'),
        ('firmado', 'DTE Firmado'),
        ('enviado', 'Enviado al MH'),
        ('procesado', 'Procesado por MH'),
        ('rechazado', 'Rechazado por MH'),
        ('contingencia', 'En Contingencia')
    ], string='Estado EDI', default='no_aplica',
       help='Estado del proceso de facturación electrónica')
    
    l10n_sv_edi_json = fields.Text(
        string='JSON DTE',
        copy=False,
        help='Contenido JSON del DTE generado'
    )
    
    l10n_sv_edi_observaciones = fields.Text(
        string='Observaciones EDI',
        copy=False,
        help='Observaciones del proceso EDI'
    )
    
    l10n_sv_edi_ambiente = fields.Selection([
        ('test', 'Certificación'),
        ('production', 'Producción')
    ], string='Ambiente EDI',
       help='Ambiente en el que se procesó el DTE')
    
    l10n_sv_edi_modo_contingencia = fields.Boolean(
        string='Procesado en Contingencia',
        default=False,
        copy=False,
        help='Indica si el DTE fue procesado en modo contingencia'
    )

    @api.depends('company_id')
    def _compute_l10n_sv_edi_applicable(self):
        """Determina si EDI aplica para esta factura"""
        for move in self:
            try:
                edi_enabled = bool(getattr(move.company_id, 'l10n_sv_edi_enabled', False))
                country_code = move.company_id.country_id.code if move.company_id.country_id else ''
                move.l10n_sv_edi_applicable = bool(
                    country_code == 'SV' and
                    edi_enabled and
                    move.move_type in ('out_invoice', 'out_refund')
                )
            except Exception:
                move.l10n_sv_edi_applicable = False

    l10n_sv_edi_applicable = fields.Boolean(
        string='EDI Aplicable',
        compute='_compute_l10n_sv_edi_applicable',
        help='Determina si la facturación electrónica aplica para este documento'
    )

    def _post(self, soft=True):
        """Override para generar DTE automáticamente al confirmar factura"""
        posted = super()._post(soft)
        
        for move in posted:
            if move.l10n_sv_edi_applicable and move.l10n_sv_edi_estado == 'no_aplica':
                move._generate_dte()
        
        return posted

    def _generate_dte(self):
        """Genera el DTE para la factura"""
        self.ensure_one()
        
        if not self.l10n_sv_edi_applicable:
            return
        
        try:
            # Determinar tipo de documento
            self._determine_document_type()
            
            # Generar códigos identificadores
            self._generate_dte_identifiers()
            
            # Actualizar estado
            self.l10n_sv_edi_estado = 'generado'
            
            # Generar JSON (se implementará en el módulo l10n_sv_edi_json)
            self._generate_dte_json()
            
        except Exception as e:
            self.l10n_sv_edi_estado = 'rechazado'
            self.l10n_sv_edi_observaciones = str(e)
            raise

    def _determine_document_type(self):
        """Determina el tipo de documento DTE según el tipo de factura"""
        self.ensure_one()
        
        # Si ya hay un tipo de documento DTE asignado desde l10n_sv_document_type, usarlo
        if hasattr(self, 'l10n_sv_document_type_id') and self.l10n_sv_document_type_id:
            self.l10n_sv_document_type_id.code = self.l10n_sv_document_type_id.code
        elif self.move_type == 'out_invoice':
            # Por defecto factura, pero podría ser CCF según configuración
            self.l10n_sv_document_type_id.code = '01'
        elif self.move_type == 'out_refund':
            self.l10n_sv_document_type_id.code = '05'  # Nota de crédito
        else:
            raise exceptions.UserError(_(
                'Tipo de documento no soportado para EDI: %s'
            ) % self.move_type)

    def _generate_dte_identifiers(self):
        """Genera los identificadores únicos del DTE"""
        self.ensure_one()
        
        config = self.company_id.get_edi_configuration()
        
        # Generar UUID único
        if not self.l10n_sv_edi_uuid:
            self.l10n_sv_edi_uuid = str(uuid.uuid4()).upper()
        
        # Generar código de generación
        if not self.l10n_sv_edi_codigo_generacion:
            self.l10n_sv_edi_codigo_generacion = str(uuid.uuid4()).upper()
        
        # Generar número de control
        if not self.l10n_sv_edi_numero_control:
            # Obtener códigos de establecimiento y punto de venta
            # Los códigos deben ser alfanuméricos en mayúsculas (A-Z, 0-9)
            establecimiento_code = self.l10n_sv_establishment_id.code if hasattr(self, 'l10n_sv_establishment_id') and self.l10n_sv_establishment_id else 'A001'
            punto_venta_code = self.l10n_sv_point_of_sale_id.code if hasattr(self, 'l10n_sv_point_of_sale_id') and self.l10n_sv_point_of_sale_id else 'B001'
            
            self.l10n_sv_edi_numero_control = config.generate_numero_control(
                self.l10n_sv_document_type_id.code,
                establecimiento_code,
                punto_venta_code
            )
        
        # Establecer ambiente
        self.l10n_sv_edi_ambiente = config.environment

    def _generate_dte_json(self):
        """Genera el JSON del DTE - se implementará en módulo específico"""
        self.ensure_one()
        # Placeholder - se implementará en l10n_sv_edi_json
        pass

    def action_generate_dte(self):
        """Acción manual para generar DTE"""
        for move in self:
            if not move.l10n_sv_edi_applicable:
                raise exceptions.UserError(_(
                    'EDI no aplica para este documento'
                ))
            move._generate_dte()

    def action_send_dte(self):
        """Acción para enviar DTE al MH"""
        _logger.info(f"===== ACTION_SEND_DTE LLAMADO EN L10N_SV_EDI_BASE =====")
        _logger.info(f"Usuario: {self.env.user.name}")
        
        for move in self:
            _logger.info(f"Procesando factura: {move.name}, Estado EDI: {move.l10n_sv_edi_estado}")
            
            if move.l10n_sv_edi_estado != 'generado':
                raise exceptions.UserError(_(
                    'El DTE debe estar generado antes de enviarlo'
                ))
            # Buscar si hay implementación en el módulo API client
            if hasattr(move, 'action_send_to_mh'):
                _logger.info(f"=== DELEGANDO A action_send_to_mh ===")
                return move.action_send_to_mh()
            else:
                _logger.error(f"=== NO EXISTE action_send_to_mh ===")
                raise exceptions.UserError(_(
                    'Módulo de API client no está instalado o configurado'
                ))

    def action_view_dte_json(self):
        """Acción para ver el JSON DTE"""
        self.ensure_one()
        if not self.l10n_sv_edi_json:
            raise exceptions.UserError(_('No hay JSON DTE generado'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'JSON DTE',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': f'DTE_{self.name}.json',
                'default_datas': self.l10n_sv_edi_json.encode(),
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }