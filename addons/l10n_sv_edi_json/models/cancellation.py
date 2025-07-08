import uuid
import json
from datetime import datetime
from odoo import models, fields, api, exceptions, _


class L10nSvCancellation(models.Model):
    """Modelo para manejar anulaciones/invalidaciones DTE"""
    _name = 'l10n_sv.cancellation'
    _description = 'Anulación/Invalidación DTE'
    _order = 'create_date desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Campos básicos
    name = fields.Char(
        string='Número de Anulación',
        readonly=True,
        copy=False,
        help='Número consecutivo de la anulación'
    )
    
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('pending', 'Pendiente Envío'),
        ('sent', 'Enviado'),
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado'),
        ('error', 'Error')
    ], string='Estado', default='draft', required=True, tracking=True)
    
    # Identificación de la anulación
    codigo_generacion = fields.Char(
        string='Código de Generación',
        copy=False,
        help='UUID único para esta anulación'
    )
    
    fecha_anulacion = fields.Datetime(
        string='Fecha/Hora Anulación',
        required=True,
        default=fields.Datetime.now,
        help='Fecha y hora de la anulación'
    )
    
    # Tipo de anulación
    tipo_anulacion = fields.Selection([
        ('1', 'Anulación por emisor'),
        ('2', 'Anulación por receptor'),
        ('3', 'Anulación por tercero autorizado')
    ], string='Tipo de Anulación', required=True, default='1')
    
    motivo_anulacion = fields.Text(
        string='Motivo de Anulación',
        required=True,
        help='Descripción detallada del motivo de anulación'
    )
    
    # Documento a anular
    move_id = fields.Many2one(
        'account.move',
        string='Documento a Anular',
        required=True,
        domain=[('l10n_sv_edi_codigo_generacion', '!=', False)],
        help='Documento contable que se desea anular'
    )
    
    documento_codigo_generacion = fields.Char(
        string='Código Generación Documento',
        required=True,
        help='Código de generación del documento a anular'
    )
    
    documento_tipo_dte = fields.Selection([
        ('01', 'Factura'),
        ('03', 'Comprobante de Crédito Fiscal'),
        ('04', 'Nota de Remisión'),
        ('05', 'Nota de Crédito'),
        ('06', 'Nota de Débito'),
        ('07', 'Comprobante de Retención'),
        ('08', 'Comprobante de Liquidación'),
        ('09', 'Documento Contable de Liquidación'),
        ('10', 'Comprobante de Donación'),
        ('11', 'Factura de Exportación'),
        ('14', 'Factura de Sujeto Excluido'),
        ('15', 'Comprobante de Donación')
    ], string='Tipo DTE Documento', required=True)
    
    documento_numero_control = fields.Char(
        string='Número Control Documento',
        required=True,
        help='Número de control del documento a anular'
    )
    
    documento_sello_recibido = fields.Char(
        string='Sello Recibido MH',
        help='Sello de recepción otorgado por el MH al documento original'
    )
    
    documento_fecha_emision = fields.Date(
        string='Fecha Emisión Documento',
        required=True,
        help='Fecha de emisión del documento a anular'
    )
    
    documento_monto_iva = fields.Float(
        string='Monto IVA',
        digits='Account',
        help='Monto de IVA del documento a anular'
    )
    
    # Documento de reemplazo (opcional)
    codigo_generacion_reemplazo = fields.Char(
        string='Código Generación Reemplazo',
        help='UUID del documento que reemplaza al anulado (opcional)'
    )
    
    # Responsables
    responsable_nombre = fields.Char(
        string='Nombre del Responsable',
        required=True,
        help='Nombre del responsable de la anulación'
    )
    
    responsable_tipo_doc = fields.Selection([
        ('36', 'NIT'),
        ('13', 'DUI'),
        ('02', 'Carnet de Residente'),
        ('03', 'Pasaporte'),
        ('37', 'Otro')
    ], string='Tipo Documento Responsable', required=True)
    
    responsable_numero_doc = fields.Char(
        string='Número Documento Responsable',
        required=True,
        help='Número de documento del responsable'
    )
    
    solicitante_nombre = fields.Char(
        string='Nombre del Solicitante',
        help='Nombre de quien solicita la anulación'
    )
    
    solicitante_tipo_doc = fields.Selection([
        ('36', 'NIT'),
        ('13', 'DUI'),
        ('02', 'Carnet de Residente'),
        ('03', 'Pasaporte'),
        ('37', 'Otro')
    ], string='Tipo Documento Solicitante')
    
    solicitante_numero_doc = fields.Char(
        string='Número Documento Solicitante',
        help='Número de documento del solicitante'
    )
    
    # JSON generado
    json_content = fields.Text(
        string='JSON Anulación',
        readonly=True,
        help='JSON de la anulación generado'
    )
    
    # Respuesta del MH
    response_code = fields.Char(
        string='Código Respuesta MH',
        readonly=True
    )
    
    response_message = fields.Text(
        string='Mensaje Respuesta MH',
        readonly=True
    )
    
    # Relaciones
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    
    # Campo comentado temporalmente hasta resolver dependencias circulares
    # api_log_id = fields.Many2one(
    #     'l10n_sv.api.log',
    #     string='Log API',
    #     readonly=True,
    #     help='Log de la comunicación con el MH'
    # )

    @api.depends('name', 'move_id', 'tipo_anulacion')
    def _compute_display_name(self):
        for record in self:
            if record.name and record.move_id:
                record.display_name = f"{record.name} - {record.move_id.name}"
            elif record.name:
                record.display_name = record.name
            else:
                record.display_name = 'Nueva Anulación'

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('l10n_sv.cancellation') or '/'
        if not vals.get('codigo_generacion'):
            vals['codigo_generacion'] = str(uuid.uuid4()).upper()
        return super().create(vals)

    @api.onchange('move_id')
    def _onchange_move_id(self):
        """Autocompleta campos desde el documento a anular"""
        if self.move_id:
            self.documento_codigo_generacion = self.move_id.l10n_sv_edi_codigo_generacion or ''
            self.documento_numero_control = self.move_id.l10n_sv_edi_numero_control or ''
            self.documento_sello_recibido = self.move_id.l10n_sv_edi_sello_recepcion or ''
            self.documento_fecha_emision = self.move_id.invoice_date or self.move_id.date
            
            # Determinar tipo de documento
            if hasattr(self.move_id, 'l10n_sv_document_type_id') and self.move_id.l10n_sv_document_type_id:
                self.documento_tipo_dte = self.move_id.l10n_sv_document_type_id.code
            
            # Calcular monto IVA
            self._calculate_iva_amount()

    def _calculate_iva_amount(self):
        """Calcula el monto de IVA del documento"""
        if self.move_id:
            iva_lines = self.move_id.line_ids.filtered(
                lambda l: l.tax_line_id and 'iva' in l.tax_line_id.name.lower()
            )
            self.documento_monto_iva = sum(iva_lines.mapped('balance'))

    def action_generate_json(self):
        """Genera el JSON de la anulación"""
        self.ensure_one()
        
        # Validaciones
        if not self.documento_codigo_generacion:
            raise exceptions.UserError(_('Debe especificar el código de generación del documento a anular'))
        
        # Obtener datos del emisor desde la compañía
        emisor_data = self._get_emisor_data()
        
        # Generar JSON según esquema v2
        cancellation_json = {
            "identificacion": {
                "version": 2,
                "ambiente": self._get_environment(),
                "codigoGeneracion": self.codigo_generacion,
                "fecAnula": self.fecha_anulacion.strftime('%Y-%m-%d'),
                "horAnula": self.fecha_anulacion.strftime('%H:%M:%S')
            },
            "emisor": emisor_data,
            "documento": {
                "tipoDte": self.documento_tipo_dte,
                "codigoGeneracion": self.documento_codigo_generacion,
                "selloRecibido": self.documento_sello_recibido or '',
                "numeroControl": self.documento_numero_control,
                "fecEmi": self.documento_fecha_emision.strftime('%Y-%m-%d'),
                "montoIva": self.documento_monto_iva,
                "codigoGeneracionR": self.codigo_generacion_reemplazo or '',
                "tipoAnulacion": int(self.tipo_anulacion)
            },
            "motivo": {
                "tipoAnulacion": int(self.tipo_anulacion),
                "motivoAnulacion": self.motivo_anulacion,
                "nombreResponsable": self.responsable_nombre,
                "tipDocResponsable": self.responsable_tipo_doc,
                "numDocResponsable": self.responsable_numero_doc,
                "nombreSolicita": self.solicitante_nombre or '',
                "tipDocSolicita": self.solicitante_tipo_doc or '',
                "numDocSolicita": self.solicitante_numero_doc or ''
            }
        }
        
        self.json_content = json.dumps(cancellation_json, indent=4, ensure_ascii=False)
        self.state = 'pending'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('JSON Generado'),
                'message': _('El JSON de la anulación ha sido generado exitosamente'),
                'type': 'success'
            }
        }

    def _get_emisor_data(self):
        """Obtiene datos del emisor desde la compañía"""
        company = self.company_id
        
        return {
            "nit": company.vat or '',
            "nombre": company.name,
            "tipoEstablecimiento": company.l10n_sv_tipo_establecimiento or "01",
            "nomEstablecimiento": company.name,
            "codEstableMH": company.l10n_sv_codigo_establecimiento_mh,
            "codEstable": company.l10n_sv_codigo_establecimiento,
            "codPuntoVentaMH": company.l10n_sv_codigo_punto_venta_mh,
            "codPuntoVenta": company.l10n_sv_codigo_punto_venta,
            "telefono": company.phone,
            "correo": company.email or ''
        }

    def _get_environment(self):
        """Determina el ambiente (certificación/producción)"""
        # Implementar lógica para determinar ambiente
        # Por ahora retornamos certificación
        return "00"

    def action_send_to_mh(self):
        """Envía la anulación al MH"""
        self.ensure_one()
        
        if not self.json_content:
            raise exceptions.UserError(_('Debe generar el JSON antes de enviar'))
        
        # Implementar envío usando l10n_sv_api_client
        try:
            # Aquí se implementaría la llamada al API del MH
            # usando el módulo l10n_sv_api_client
            
            self.state = 'sent'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Anulación Enviada'),
                    'message': _('La anulación ha sido enviada al MH'),
                    'type': 'success'
                }
            }
            
        except Exception as e:
            self.state = 'error'
            raise exceptions.UserError(_('Error al enviar: %s') % str(e))

    def action_view_json(self):
        """Acción para visualizar el JSON generado"""
        self.ensure_one()
        
        if not self.json_content:
            raise exceptions.UserError(_('No hay JSON generado'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('JSON Anulación'),
            'res_model': 'l10n_sv.json.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_json_content': self.json_content,
                'default_document_type': 'Anulación DTE',
                'default_numero_control': self.name
            }
        }

    def action_apply_cancellation(self):
        """Aplica la anulación al documento contable"""
        self.ensure_one()
        
        if self.state != 'accepted':
            raise exceptions.UserError(_('Solo se pueden aplicar anulaciones aceptadas por el MH'))
        
        if self.move_id:
            # Marcar el documento como anulado
            self.move_id.message_post(
                body=_('Documento anulado mediante anulación DTE: %s<br/>Motivo: %s') % (self.name, self.motivo_anulacion)
            )
            
            # Agregar campos de anulación si existen
            if hasattr(self.move_id, 'l10n_sv_edi_anulado'):
                self.move_id.l10n_sv_edi_anulado = True
                self.move_id.l10n_sv_edi_fecha_anulacion = self.fecha_anulacion
                self.move_id.l10n_sv_edi_motivo_anulacion = self.motivo_anulacion
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Anulación Aplicada'),
                'message': _('La anulación ha sido aplicada al documento contable'),
                'type': 'success'
            }
        }