import json
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)
_logger.info("=== MÓDULO L10N_SV_API_CLIENT ACCOUNT_MOVE CARGADO ===")


class AccountMove(models.Model):
    """Extensión de facturas para comunicación con API del MH"""
    _inherit = 'account.move'

    # Estados de comunicación con MH
    l10n_sv_mh_status = fields.Selection([
        ('draft', 'Borrador'),
        ('ready', 'Listo para Envío'),
        ('sent', 'Enviado al MH'),
        ('received', 'Recibido por MH'),
        ('processed', 'Procesado por MH'),
        ('approved', 'Aprobado por MH'),
        ('rejected', 'Rechazado por MH'),
        ('error', 'Error de Comunicación')
    ], string='Estado MH', readonly=True, default='draft',
       help='Estado de la comunicación con el Ministerio de Hacienda')
    
    l10n_sv_mh_response = fields.Text(
        string='Respuesta MH',
        readonly=True,
        help='Última respuesta recibida del Ministerio de Hacienda'
    )
    
    l10n_sv_mh_send_date = fields.Datetime(
        string='Fecha Envío MH',
        readonly=True,
        help='Fecha y hora de envío al MH'
    )
    
    l10n_sv_mh_received_date = fields.Datetime(
        string='Fecha Recibido MH',
        readonly=True,
        help='Fecha y hora de recepción confirmada por el MH'
    )
    
    l10n_sv_mh_processed_date = fields.Datetime(
        string='Fecha Procesado MH',
        readonly=True,
        help='Fecha y hora de procesamiento por el MH'
    )
    
    l10n_sv_mh_error_message = fields.Text(
        string='Error MH',
        readonly=True,
        help='Último mensaje de error del MH'
    )
    
    l10n_sv_mh_observations = fields.Text(
        string='Observaciones MH',
        readonly=True,
        help='Observaciones del MH sobre el documento'
    )
    
    # Información de sello recibido del MH
    l10n_sv_mh_sello = fields.Text(
        string='Sello MH',
        readonly=True,
        help='Sello digital recibido del MH tras aprobación'
    )
    
    l10n_sv_mh_uuid = fields.Char(
        string='UUID MH',
        readonly=True,
        help='UUID asignado por el MH al documento'
    )
    
    # Log de comunicaciones
    l10n_sv_api_log_ids = fields.One2many(
        'l10n_sv.api.log',
        'move_id',
        string='Logs API MH',
        readonly=True,
        help='Historial de comunicaciones con el MH'
    )
    
    # Contadores de intentos
    l10n_sv_send_attempts = fields.Integer(
        string='Intentos de Envío',
        readonly=True,
        default=0,
        help='Número de intentos de envío al MH'
    )
    
    l10n_sv_query_attempts = fields.Integer(
        string='Intentos de Consulta',
        readonly=True,
        default=0,
        help='Número de intentos de consulta de estado'
    )

    def action_send_to_mh(self):
        """Acción para enviar DTE al MH"""
        self.ensure_one()
        
        # TRAZABILIDAD COMPLETA - Log al inicio
        _logger.info(f"===== INICIANDO ACTION_SEND_TO_MH =====")
        _logger.info(f"Usuario que ejecuta: {self.env.user.name}")
        _logger.info(f"Factura: {self.name}")
        _logger.info(f"Tipo documento: {self.l10n_sv_document_type_id.code if self.l10n_sv_document_type_id else 'N/A'}")
        _logger.info(f"Estado actual: {self.state}")
        
        # Validaciones previas
        if self.state != 'posted':
            raise exceptions.UserError(_('Solo se pueden enviar facturas validadas'))
        
        if not self.l10n_sv_document_type_id:
            raise exceptions.UserError(_('Debe asignar un tipo de documento DTE'))
        
        if not self.l10n_sv_edi_numero_control:
            raise exceptions.UserError(_('Debe generar el número de control DTE'))
        
        if not self.l10n_sv_json_generated:
            raise exceptions.UserError(_(
                'Debe generar el JSON DTE antes de enviar al MH'
            ))
        
        if not self.l10n_sv_json_validated:
            raise exceptions.UserError(_(
                'El JSON DTE debe estar validado antes del envío'
            ))
        
        try:
            # DEBUG: Log inicial del proceso de envío
            _logger.info(f"=== INICIANDO ENVÍO CCF AL MH ===")
            _logger.info(f"Factura: {self.name}, Tipo doc: {self.l10n_sv_document_type_id.code}")
            
            # Obtener cliente API
            api_client = self.env['l10n_sv.api.client'].get_default_client(self.company_id.id)
            
            # Incrementar contador de intentos
            self.l10n_sv_send_attempts += 1
            
            # Actualizar estado
            self.l10n_sv_mh_status = 'ready'
            
            # Obtener JSON DTE
            json_data = self.get_json_dte_dict()
            if not json_data:
                raise exceptions.UserError(_('No se pudo obtener el JSON DTE'))
            
            # DEBUG: Log del JSON para verificar estructura
            _logger.info(f"JSON DTE a enviar (tipoDte: {json_data.get('identificacion', {}).get('tipoDte')}, version: {json_data.get('identificacion', {}).get('version')})")
            _logger.info(f"NumeroControl: {json_data.get('identificacion', {}).get('numeroControl')}")
            _logger.info(f"JSON completo identificacion: {json_data.get('identificacion', {})}")
            _logger.info(f"Receptor: {json_data.get('receptor', {})}")
            
            # DEBUG: Log antes de envío
            _logger.info(f"=== LLAMANDO A api_client.send_dte ===")
            
            # Enviar al MH
            result = api_client.send_dte(
                json_data=json_data,
                numero_control=self.l10n_sv_edi_numero_control,
                codigo_generacion=self.l10n_sv_edi_codigo_generacion
            )
            
            # Procesar resultado
            if result['success']:
                response = result['response']
                
                # Actualizar estado y datos
                self.write({
                    'l10n_sv_mh_status': 'sent',
                    'l10n_sv_mh_send_date': fields.Datetime.now(),
                    'l10n_sv_mh_response': json.dumps(response, ensure_ascii=False),
                    'l10n_sv_mh_error_message': False
                })
                
                # Extraer información específica de la respuesta
                self._process_mh_response(response)
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Envío Exitoso'),
                        'message': _('El DTE se ha enviado correctamente al MH'),
                        'type': 'success'
                    }
                }
            else:
                # Error en el envío
                error_msg = result.get('error', 'Error desconocido')
                self.write({
                    'l10n_sv_mh_status': 'error',
                    'l10n_sv_mh_error_message': error_msg
                })
                
                raise exceptions.UserError(_(
                    'Error enviando DTE al MH: %s'
                ) % error_msg)
                
        except Exception as e:
            # Error general
            error_msg = str(e)
            self.write({
                'l10n_sv_mh_status': 'error',
                'l10n_sv_mh_error_message': error_msg
            })
            
            _logger.error(f'Error enviando DTE {self.name} al MH: {error_msg}')
            raise exceptions.UserError(_(
                'Error enviando DTE al MH: %s'
            ) % error_msg)

    def action_send_dte(self):
        """Override del método action_send_dte para usar action_send_to_mh"""
        _logger.info(f"===== ACTION_SEND_DTE LLAMADO EN L10N_SV_API_CLIENT =====")
        _logger.info(f"Usuario: {self.env.user.name}, Factura: {self.name}")
        _logger.info(f"=== Redirigiendo a action_send_to_mh ===")
        return self.action_send_to_mh()

    def action_query_mh_status(self):
        """Acción para consultar estado en el MH"""
        self.ensure_one()
        
        if not self.l10n_sv_edi_numero_control:
            raise exceptions.UserError(_('No hay número de control para consultar'))
        
        if not self.l10n_sv_edi_codigo_generacion:
            raise exceptions.UserError(_('No hay código de generación para consultar'))
        
        try:
            # Obtener cliente API
            api_client = self.env['l10n_sv.api.client'].get_default_client(self.company_id.id)
            
            # Incrementar contador de consultas
            self.l10n_sv_query_attempts += 1
            
            # Consultar estado
            result = api_client.query_dte_status(
                numero_control=self.l10n_sv_edi_numero_control,
                codigo_generacion=self.l10n_sv_edi_codigo_generacion
            )
            
            if result['success']:
                response = result['response']
                
                # Procesar respuesta de consulta
                self._process_mh_query_response(response)
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Consulta Exitosa'),
                        'message': _('Estado actualizado desde el MH'),
                        'type': 'success'
                    }
                }
            else:
                error_msg = result.get('error', 'Error en consulta')
                raise exceptions.UserError(_(
                    'Error consultando estado en MH: %s'
                ) % error_msg)
                
        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error consultando estado DTE {self.name}: {error_msg}')
            raise exceptions.UserError(_(
                'Error consultando estado: %s'
            ) % error_msg)

    def _process_mh_response(self, response):
        """Procesa respuesta del MH después del envío - LÓGICA VALIDADA 29/06/2025"""
        self.ensure_one()
        
        if isinstance(response, dict):
            # El MH responde directamente con los datos, no con wrapper "status"/"body"
            estado = response.get('estado', '')
            codigo_msg = response.get('codigoMsg', '')
            descripcion_msg = response.get('descripcionMsg', '')
            sello_recepcion = response.get('selloRecibido', '')
            fecha_procesamiento = response.get('fhProcesamiento', '')
            
            # Mapear estados según respuesta validada del MH
            if estado == 'PROCESADO' and codigo_msg == '001':
                self.l10n_sv_mh_status = 'processed'
                self.l10n_sv_mh_processed_date = fields.Datetime.now()
                
                # Extraer sello de recepción (formato validado)
                if sello_recepcion:
                    self.l10n_sv_mh_sello = sello_recepcion
                
                # Log de éxito
                _logger.info(f'DTE {self.name} procesado exitosamente por MH. Sello: {sello_recepcion}')
                
            elif estado == 'RECIBIDO':
                self.l10n_sv_mh_status = 'received'
                self.l10n_sv_mh_received_date = fields.Datetime.now()
                
            elif estado == 'RECHAZADO':
                self.l10n_sv_mh_status = 'rejected'
                
            elif estado == 'ERROR' or codigo_msg != '001':
                self.l10n_sv_mh_status = 'error'
                # Log de error específico
                _logger.error(f'DTE {self.name} con error en MH. Código: {codigo_msg}, Mensaje: {descripcion_msg}')
            
            # Extraer observaciones (puede ser lista o string)
            observaciones = response.get('observaciones', [])
            if observaciones:
                if isinstance(observaciones, list):
                    self.l10n_sv_mh_observations = '\n'.join(str(obs) for obs in observaciones)
                else:
                    self.l10n_sv_mh_observations = str(observaciones)
            
            # Agregar descripción del mensaje si está disponible
            if descripcion_msg:
                if self.l10n_sv_mh_observations:
                    self.l10n_sv_mh_observations += f'\n{descripcion_msg}'
                else:
                    self.l10n_sv_mh_observations = descripcion_msg
            
            # Extraer UUID del MH si existe (algunos esquemas lo incluyen)
            uuid_mh = response.get('uuid') or response.get('codigoGeneracion')
            if uuid_mh:
                self.l10n_sv_mh_uuid = uuid_mh

    def _process_mh_query_response(self, response):
        """Procesa respuesta de consulta de estado"""
        self.ensure_one()
        
        if isinstance(response, dict):
            estado = response.get('estado', '').upper()
            
            # Actualizar estado basado en consulta
            if estado in ['PROCESADO', 'APPROVED']:
                self.l10n_sv_mh_status = 'approved'
                if not self.l10n_sv_mh_processed_date:
                    self.l10n_sv_mh_processed_date = fields.Datetime.now()
                    
            elif estado in ['RECHAZADO', 'REJECTED']:
                self.l10n_sv_mh_status = 'rejected'
                
            elif estado in ['RECIBIDO', 'RECEIVED']:
                if self.l10n_sv_mh_status == 'sent':
                    self.l10n_sv_mh_status = 'received'
                    if not self.l10n_sv_mh_received_date:
                        self.l10n_sv_mh_received_date = fields.Datetime.now()
            
            # Actualizar observaciones si hay nuevas
            if 'observaciones' in response and response['observaciones']:
                existing_obs = self.l10n_sv_mh_observations or ''
                new_obs = response['observaciones']
                if new_obs not in existing_obs:
                    if existing_obs:
                        self.l10n_sv_mh_observations = existing_obs + '\n---\n' + new_obs
                    else:
                        self.l10n_sv_mh_observations = new_obs

    def action_view_mh_logs(self):
        """Acción para ver logs de comunicación con MH"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Logs Comunicación MH'),
            'res_model': 'l10n_sv.api.log',
            'view_mode': 'tree,form',
            'domain': [('move_id', '=', self.id)],
            'context': {'default_move_id': self.id}
        }

    def action_reset_mh_status(self):
        """Acción para resetear estado de comunicación con MH"""
        self.ensure_one()
        
        self.write({
            'l10n_sv_mh_status': 'draft',
            'l10n_sv_mh_response': False,
            'l10n_sv_mh_send_date': False,
            'l10n_sv_mh_received_date': False,
            'l10n_sv_mh_processed_date': False,
            'l10n_sv_mh_error_message': False,
            'l10n_sv_mh_observations': False,
            'l10n_sv_mh_sello': False,
            'l10n_sv_mh_uuid': False,
            'l10n_sv_send_attempts': 0,
            'l10n_sv_query_attempts': 0
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Estado Reseteado'),
                'message': _('El estado de comunicación con MH ha sido reseteado'),
                'type': 'info'
            }
        }

    @api.model
    def cron_send_pending_dte(self):
        """Tarea programada para enviar DTE pendientes al MH"""
        pending_moves = self.search([
            ('state', '=', 'posted'),
            ('l10n_sv_document_type_id', '!=', False),
            ('l10n_sv_json_generated', '=', True),
            ('l10n_sv_json_validated', '=', True),
            ('l10n_sv_mh_status', 'in', ['draft', 'ready']),
            ('l10n_sv_send_attempts', '<', 3)  # Máximo 3 intentos automáticos
        ])
        
        success_count = 0
        error_count = 0
        
        for move in pending_moves:
            try:
                move.action_send_to_mh()
                success_count += 1
            except Exception as e:
                error_count += 1
                _logger.error(f'Error enviando DTE automático {move.name}: {str(e)}')
        
        _logger.info(f'Envío automático DTE completado: {success_count} exitosos, {error_count} errores')

    @api.model
    def cron_query_sent_dte_status(self):
        """Tarea programada para consultar estado de DTE enviados"""
        sent_moves = self.search([
            ('l10n_sv_mh_status', 'in', ['sent', 'received']),
            ('l10n_sv_query_attempts', '<', 10),  # Máximo 10 consultas
            ('l10n_sv_mh_send_date', '>', fields.Datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=7))  # Solo últimos 7 días
        ])
        
        for move in sent_moves:
            try:
                move.action_query_mh_status()
            except Exception as e:
                _logger.error(f'Error consultando estado automático DTE {move.name}: {str(e)}')
        
        _logger.info(f'Consulta automática de estado completada para {len(sent_moves)} documentos')

    @api.depends('l10n_sv_json_validated', 'l10n_sv_mh_status')
    def _compute_edi_status(self):
        """Computa estado EDI incluyendo comunicación MH"""
        super()._compute_edi_status()
        
        for move in self:
            if move.l10n_sv_mh_status in ['approved', 'processed']:
                move.l10n_sv_edi_status = 'approved'
            elif move.l10n_sv_mh_status == 'rejected':
                move.l10n_sv_edi_status = 'rejected'
            elif move.l10n_sv_mh_status in ['sent', 'received']:
                move.l10n_sv_edi_status = 'sent'
            elif move.l10n_sv_mh_status == 'error':
                move.l10n_sv_edi_status = 'error'