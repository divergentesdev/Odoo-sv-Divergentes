import uuid
import json
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class L10nSvContingency(models.Model):
    """Modelo para manejar reportes de contingencia DTE"""
    _name = 'l10n_sv.contingency'
    _description = 'Reporte de Contingencia DTE'
    _order = 'create_date desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Campos básicos
    name = fields.Char(
        string='Número de Reporte',
        readonly=True,
        copy=False,
        help='Número consecutivo del reporte de contingencia'
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
    
    # Identificación del reporte
    codigo_generacion = fields.Char(
        string='Código de Generación',
        copy=False,
        help='UUID único para este reporte de contingencia'
    )
    
    fecha_inicio = fields.Datetime(
        string='Fecha/Hora Inicio',
        required=True,
        help='Fecha y hora de inicio de la contingencia'
    )
    
    fecha_fin = fields.Datetime(
        string='Fecha/Hora Fin',
        required=True,
        help='Fecha y hora de fin de la contingencia'
    )
    
    fecha_transmision = fields.Datetime(
        string='Fecha/Hora Transmisión',
        help='Fecha y hora de transmisión del reporte al MH'
    )
    
    # El ambiente se toma de la configuración EDI de la compañía
    
    # Tipo de contingencia
    tipo_contingencia = fields.Selection([
        ('1', 'Falla del sistema del contribuyente'),
        ('2', 'Falla de conectividad'),
        ('3', 'Mantenimiento programado'),
        ('4', 'Falla del sistema del MH'),
        ('5', 'Otra contingencia')
    ], string='Tipo de Contingencia', required=True)
    
    motivo_contingencia = fields.Text(
        string='Motivo de Contingencia',
        required=True,
        help='Descripción detallada del motivo de la contingencia'
    )
    
    # Responsable
    responsable_nombre = fields.Char(
        string='Nombre del Responsable',
        required=True,
        help='Nombre del responsable del establecimiento'
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
    
    # Documentos incluidos en la contingencia
    document_ids = fields.One2many(
        'l10n_sv.contingency.document',
        'contingency_id',
        string='Documentos en Contingencia'
    )
    
    # JSON generado
    json_content = fields.Text(
        string='JSON Contingencia',
        readonly=True,
        help='JSON del reporte de contingencia generado'
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

    @api.depends('name', 'tipo_contingencia', 'fecha_inicio')
    def _compute_display_name(self):
        for record in self:
            if record.name:
                tipo_desc = dict(record._fields['tipo_contingencia'].selection).get(record.tipo_contingencia, '')
                record.display_name = f"{record.name} - {tipo_desc}"
            else:
                record.display_name = 'Nuevo Reporte'

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fecha_consistency(self):
        """Valida que fecha_fin sea posterior a fecha_inicio"""
        for record in self:
            if record.fecha_inicio and record.fecha_fin:
                if record.fecha_fin <= record.fecha_inicio:
                    raise exceptions.ValidationError(_(
                        'La fecha y hora de fin debe ser POSTERIOR a la fecha y hora de inicio.\n'
                        'Inicio: %s\n'
                        'Fin: %s\n\n'
                        'Corrija la hora de fin para que sea al menos 1 minuto después del inicio.'
                    ) % (record.fecha_inicio.strftime('%Y-%m-%d %H:%M:%S'), 
                         record.fecha_fin.strftime('%Y-%m-%d %H:%M:%S')))

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('l10n_sv.contingency') or '/'
        if not vals.get('codigo_generacion'):
            vals['codigo_generacion'] = str(uuid.uuid4()).upper()
        return super().create(vals)

    def action_generate_json(self):
        """Genera el JSON del reporte de contingencia"""
        self.ensure_one()
        
        if not self.document_ids:
            raise exceptions.UserError(_('Debe agregar al menos un documento a la contingencia'))
        
        # Obtener datos del emisor desde la compañía
        emisor_data = self._get_emisor_data()
        
        # Generar JSON según esquema v3
        contingency_json = {
            "identificacion": {
                "version": 3,
                "ambiente": self._get_environment(),
                "codigoGeneracion": self.codigo_generacion,
                "fTransmision": self.fecha_transmision.strftime('%Y-%m-%d') if self.fecha_transmision else datetime.now().strftime('%Y-%m-%d'),
                "hTransmision": self.fecha_transmision.strftime('%H:%M:%S') if self.fecha_transmision else datetime.now().strftime('%H:%M:%S')
            },
            "emisor": emisor_data,
            "detalleDTE": self._get_document_details(),
            "motivo": {
                "fInicio": self.fecha_inicio.strftime('%Y-%m-%d'),
                "fFin": self.fecha_fin.strftime('%Y-%m-%d'),
                "hInicio": self.fecha_inicio.strftime('%H:%M:%S'),
                "hFin": self.fecha_fin.strftime('%H:%M:%S'),
                "tipoContingencia": int(self.tipo_contingencia),
                "motivoContingencia": self.motivo_contingencia
            }
        }
        
        self.json_content = json.dumps(contingency_json, indent=4, ensure_ascii=False)
        self.state = 'pending'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('JSON Generado'),
                'message': _('El JSON del reporte de contingencia ha sido generado exitosamente'),
                'type': 'success'
            }
        }

    def _get_emisor_data(self):
        """Obtiene datos del emisor desde la compañía"""
        company = self.company_id
        
        # Obtener configuración EDI si existe
        edi_config = self.env['l10n_sv.edi.configuration'].search([
            ('company_id', '=', company.id)
        ], limit=1)
        
        return {
            "nit": edi_config.nit_emisor if edi_config else (company.vat or ''),
            "nombre": company.name,
            "nombreResponsable": self.responsable_nombre,
            "tipoDocResponsable": self.responsable_tipo_doc,
            "numeroDocResponsable": self.responsable_numero_doc,
            "tipoEstablecimiento": "01",  # Tipo por defecto: local comercial
            "codEstableMH": edi_config.codigo_establecimiento if edi_config else None,
            "codPuntoVenta": edi_config.punto_venta if edi_config else None,
            "telefono": company.phone or '',
            "correo": company.email or ''
        }

    def _get_document_details(self):
        """Obtiene detalles de documentos en contingencia"""
        details = []
        for i, doc in enumerate(self.document_ids, 1):
            details.append({
                "noItem": i,
                "codigoGeneracion": doc.codigo_generacion,
                "tipoDoc": doc.tipo_documento
            })
        return details

    def _get_environment(self):
        """Determina el ambiente (certificación/producción) desde la configuración EDI"""
        edi_config = self.env['l10n_sv.edi.configuration'].search([
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if edi_config:
            # Mapear de test/production a 00/01
            return "01" if edi_config.environment == 'production' else "00"
        return "00"  # Por defecto certificación

    def action_send_to_mh(self):
        """Envía el reporte de contingencia al MH"""
        self.ensure_one()
        
        if not self.json_content:
            raise exceptions.UserError(_('Debe generar el JSON antes de enviar'))
        
        # Obtener API client
        api_client = self.env['l10n_sv.api.client'].search([
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not api_client:
            raise exceptions.UserError(_(
                'No se encontró configuración de API para la compañía. '
                'Configure el cliente API en Facturación Electrónica > Configuración > API MH'
            ))
        
        try:
            # Preparar datos para envío
            json_data = json.loads(self.json_content)
            
            _logger.info(f"===== INICIANDO ENVÍO DE CONTINGENCIA =====")
            _logger.info(f"Contingencia: {self.name}")
            _logger.info(f"JSON: {json.dumps(json_data, indent=2)}")
            
            # Actualizar fecha/hora de transmisión al momento actual
            json_data['identificacion']['fTransmision'] = datetime.now().strftime('%Y-%m-%d')
            json_data['identificacion']['hTransmision'] = datetime.now().strftime('%H:%M:%S')
            
            # Paso 1: Firmar el documento de contingencia usando el firmador oficial del MH
            _logger.info('Firmando reporte de contingencia...')
            
            try:
                # Usar el método existente que maneja la firma correctamente
                # El firmador detectará que es una contingencia por la estructura del JSON
                documento_firmado = api_client._sign_dte_with_mh_service(json_data)
                
                # El firmador devuelve el JWT firmado para DTEs normales,
                # pero para contingencias necesitamos verificar qué devuelve
                _logger.info(f'Respuesta del firmador - tipo: {type(documento_firmado)}')
                
                if isinstance(documento_firmado, dict):
                    # Si es un diccionario, verificar si tiene 'body'
                    if 'body' in documento_firmado:
                        json_firmado = documento_firmado['body']
                        _logger.info('Firmador devolvió respuesta con body')
                    else:
                        json_firmado = documento_firmado
                        _logger.info('Firmador devolvió diccionario directo')
                elif isinstance(documento_firmado, str):
                    # Si es string, puede ser JWT o JSON string
                    try:
                        # Intentar parsear como JSON
                        json_firmado = json.loads(documento_firmado)
                        _logger.info('Firmador devolvió JSON string')
                    except:
                        # Si no es JSON, es JWT
                        _logger.info('Firmador devolvió JWT')
                        json_firmado = documento_firmado
                else:
                    json_firmado = documento_firmado
                
                _logger.info(f'Documento firmado procesado - tipo final: {type(json_firmado)}')
                
            except Exception as e:
                _logger.error(f"Error al firmar contingencia: {str(e)}")
                raise exceptions.UserError(_(
                    'Error al firmar el reporte de contingencia: %s'
                ) % str(e))
            
            # Paso 2: Enviar al MH usando el endpoint de contingencia
            _logger.info(f"Enviando contingencia firmada a: {api_client.api_contingencia_url}")
            
            # Preparar el formato específico para contingencias según documentación MH
            # Las contingencias necesitan el mismo wrapper que los DTEs normales
            import uuid
            envio_id = int(str(uuid.uuid4().int)[:8]) % 999999999
            
            # Estructura de envío similar a DTEs normales pero para contingencias
            contingency_envelope = {
                "ambiente": self._get_environment(),  # 00=Certificación, 01=Producción
                "idEnvio": envio_id,
                "version": 1,  # Versión del protocolo MH
                "documento": json_firmado  # Documento firmado (JWT o JSON según lo que devuelva el firmador)
            }
            
            # Headers estándar para el MH
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            _logger.info(f"Envelope de contingencia: {json.dumps(contingency_envelope, ensure_ascii=False, indent=2)}")
            _logger.info(f"Tipo de documento firmado: {type(json_firmado)}")
            
            # Enviar la contingencia al MH usando el método autenticado estándar
            _logger.info(f"Enviando envelope de contingencia al MH...")
            
            response = api_client._make_authenticated_request(
                method='POST',
                url=api_client.api_contingencia_url,
                data=contingency_envelope,
                headers=headers
            )
            
            # Procesar respuesta del método _make_authenticated_request
            if response:
                _logger.info(f"Respuesta del MH: {response}")
                
                # El método _make_authenticated_request ya devuelve el JSON parseado
                if isinstance(response, dict):
                    response_data = response
                    
                    self.response_code = response_data.get('codigoMsg', 'OK')
                    self.response_message = json.dumps(response_data, indent=2, ensure_ascii=False)

                    # Verificar estructura de respuesta del MH
                    if response_data.get('status') == 'OK':
                        # Respuesta exitosa con estructura {status: OK, body: {...}}
                        body = response_data.get('body', {})
                        estado = body.get('estado', '').upper()
                        
                        if estado == 'PROCESADO':
                            self.state = 'accepted'
                            message = _('Reporte de contingencia aceptado por el MH')
                            msg_type = 'success'
                        elif estado == 'RECHAZADO':
                            self.state = 'rejected'
                            message = _('Reporte rechazado: %s') % body.get('descripcionMsg', 'Error desconocido')
                            msg_type = 'warning'
                        else:
                            self.state = 'sent'
                            message = _('Reporte enviado al MH. Estado: %s') % body.get('descripcionMsg', 'Procesando')
                            msg_type = 'info'
                    
                    elif 'estado' in response_data:
                        # Respuesta directa sin wrapper status/body
                        estado = response_data.get('estado', '').upper()
                        if estado == 'PROCESADO':
                            self.state = 'accepted'
                            message = _('Reporte de contingencia aceptado por el MH')
                            msg_type = 'success'
                        elif estado == 'RECHAZADO':
                            self.state = 'rejected'
                            message = _('Reporte rechazado: %s') % response_data.get('descripcionMsg', 'Error desconocido')
                            msg_type = 'warning'
                        else:
                            self.state = 'sent'
                            message = _('Reporte enviado al MH')
                            msg_type = 'info'
                    
                    else:
                        # Respuesta de error
                        self.state = 'error'
                        error_msg = response_data.get('mensaje', response_data.get('message', 'Error desconocido'))
                        message = _('Error del MH: %s') % error_msg
                        msg_type = 'danger'
                        
                        _logger.error(f"Error en respuesta del MH: {response_data}")
                
                else:
                    # Respuesta no es diccionario
                    self.state = 'error'
                    self.response_message = str(response)
                    message = _('Respuesta inesperada del MH')
                    msg_type = 'danger'
            else:
                # Sin respuesta del MH
                self.state = 'error'
                self.response_message = 'No se recibió respuesta del servidor'
                message = _('Error de comunicación con MH: Sin respuesta')
                msg_type = 'danger'
            
            self.fecha_transmision = datetime.now()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Envío de Contingencia'),
                    'message': message,
                    'type': msg_type
                }
            }
            
        except Exception as e:
            _logger.error(f"Error enviando contingencia: {str(e)}")
            self.state = 'error'
            self.response_message = str(e)
            raise exceptions.UserError(_('Error al enviar contingencia al MH: %s') % str(e))

    def action_view_json(self):
        """Acción para visualizar el JSON generado"""
        self.ensure_one()
        
        if not self.json_content:
            raise exceptions.UserError(_('No hay JSON generado'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('JSON Reporte Contingencia'),
            'res_model': 'l10n_sv.contingency.json.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_json_content': self.json_content,
                'default_contingency_id': self.id
            }
        }


class L10nSvContingencyDocument(models.Model):
    """Documentos incluidos en un reporte de contingencia"""
    _name = 'l10n_sv.contingency.document'
    _description = 'Documento en Contingencia'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Secuencia', default=10)
    
    contingency_id = fields.Many2one(
        'l10n_sv.contingency',
        string='Reporte Contingencia',
        required=True,
        ondelete='cascade'
    )
    
    move_id = fields.Many2one(
        'account.move',
        string='Documento Contable',
        help='Documento contable relacionado (opcional)'
    )
    
    codigo_generacion = fields.Char(
        string='Código de Generación',
        required=True,
        help='UUID del documento en contingencia'
    )
    
    tipo_documento = fields.Selection([
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
        ('15', 'Comprobante de Donación')
    ], string='Tipo de Documento', required=True)
    
    numero_control = fields.Char(
        string='Número de Control',
        help='Número de control del documento'
    )
    
    fecha_emision = fields.Date(
        string='Fecha Emisión',
        help='Fecha de emisión del documento'
    )
    
    observaciones = fields.Text(
        string='Observaciones',
        help='Observaciones adicionales sobre este documento'
    )

    @api.onchange('move_id')
    def _onchange_move_id(self):
        """Autocompleta campos desde el documento contable"""
        if self.move_id:
            self.codigo_generacion = self.move_id.l10n_sv_edi_codigo_generacion or ''
            self.numero_control = self.move_id.l10n_sv_edi_numero_control or ''
            self.fecha_emision = self.move_id.invoice_date or self.move_id.date
            
            # Determinar tipo de documento
            if hasattr(self.move_id, 'l10n_sv_document_type_id') and self.move_id.l10n_sv_document_type_id:
                self.tipo_documento = self.move_id.l10n_sv_document_type_id.code