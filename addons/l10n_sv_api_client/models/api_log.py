import json
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class L10nSvApiLog(models.Model):
    """Log de comunicación con API del MH"""
    _name = 'l10n_sv.api.log'
    _description = 'Log API MH El Salvador'
    _order = 'request_date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )
    
    client_id = fields.Many2one(
        'l10n_sv.api.client',
        string='Cliente API',
        required=True,
        ondelete='cascade',
        help='Cliente API utilizado para la petición'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='client_id.company_id',
        store=True,
        readonly=True
    )
    
    request_type = fields.Selection([
        ('auth', 'Autenticación'),
        ('send_dte', 'Envío DTE'),
        ('query_status', 'Consulta Estado'),
        ('contingency', 'Contingencia'),
        ('other', 'Otro')
    ], string='Tipo de Petición', required=True)
    
    # Datos del documento
    move_id = fields.Many2one(
        'account.move',
        string='Factura',
        ondelete='set null',
        help='Factura asociada a esta petición'
    )
    
    numero_control = fields.Char(
        string='Número de Control',
        help='Número de control del DTE'
    )
    
    codigo_generacion = fields.Char(
        string='Código de Generación',
        help='Código de generación único del DTE'
    )
    
    # Datos de petición
    request_date = fields.Datetime(
        string='Fecha Petición',
        required=True,
        default=fields.Datetime.now
    )
    
    request_url = fields.Char(
        string='URL Petición',
        help='URL utilizada para la petición'
    )
    
    request_method = fields.Char(
        string='Método HTTP',
        default='POST',
        help='Método HTTP utilizado (GET, POST, etc.)'
    )
    
    request_headers = fields.Text(
        string='Headers Petición',
        help='Headers HTTP enviados (sin información sensible)'
    )
    
    request_data = fields.Text(
        string='Datos Petición',
        help='Datos JSON enviados al MH'
    )
    
    # Datos de respuesta
    response_date = fields.Datetime(
        string='Fecha Respuesta',
        help='Fecha y hora de la respuesta del MH'
    )
    
    response_code = fields.Integer(
        string='Código HTTP',
        help='Código de respuesta HTTP'
    )
    
    response_headers = fields.Text(
        string='Headers Respuesta',
        help='Headers HTTP recibidos del MH'
    )
    
    response_data = fields.Text(
        string='Datos Respuesta',
        help='Datos JSON recibidos del MH'
    )
    
    # Estado y resultado
    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('success', 'Exitoso'),
        ('error', 'Error'),
        ('timeout', 'Timeout')
    ], string='Estado', required=True, default='pending')
    
    status_code = fields.Char(
        string='Código Estado MH',
        help='Código de estado devuelto por el MH'
    )
    
    error_message = fields.Text(
        string='Mensaje de Error',
        help='Descripción del error si la petición falló'
    )
    
    # Tiempos de procesamiento
    duration_ms = fields.Integer(
        string='Duración (ms)',
        compute='_compute_duration',
        store=True,
        help='Duración de la petición en milisegundos'
    )
    
    # Datos procesados
    response_parsed = fields.Text(
        string='Respuesta Procesada',
        compute='_compute_response_parsed',
        help='Respuesta del MH en formato legible'
    )

    @api.depends('request_type', 'numero_control', 'request_date')
    def _compute_display_name(self):
        """Computa nombre de visualización"""
        for log in self:
            request_types = dict(self._fields['request_type'].selection)
            type_name = request_types.get(log.request_type, log.request_type)
            
            if log.numero_control:
                log.display_name = f"{type_name} - {log.numero_control}"
            else:
                log.display_name = f"{type_name} - {log.request_date.strftime('%Y-%m-%d %H:%M')}"

    @api.depends('request_date', 'response_date')
    def _compute_duration(self):
        """Computa duración de la petición"""
        for log in self:
            if log.request_date and log.response_date:
                duration = log.response_date - log.request_date
                log.duration_ms = int(duration.total_seconds() * 1000)
            else:
                log.duration_ms = 0

    @api.depends('response_data')
    def _compute_response_parsed(self):
        """Parsea respuesta JSON para visualización"""
        for log in self:
            if log.response_data:
                try:
                    data = json.loads(log.response_data)
                    
                    # Extraer información relevante según tipo
                    if log.request_type == 'send_dte':
                        parsed = log._parse_send_response(data)
                    elif log.request_type == 'query_status':
                        parsed = log._parse_query_response(data)
                    elif log.request_type == 'auth':
                        parsed = log._parse_auth_response(data)
                    else:
                        parsed = json.dumps(data, ensure_ascii=False, indent=2)
                    
                    log.response_parsed = parsed
                    
                except (json.JSONDecodeError, Exception):
                    log.response_parsed = log.response_data
            else:
                log.response_parsed = ''

    def _parse_send_response(self, data):
        """Parsea respuesta de envío DTE"""
        if isinstance(data, dict):
            estado = data.get('estado', 'DESCONOCIDO')
            descripcion = data.get('descripcionMsg', 'Sin descripción')
            codigo_msg = data.get('codigoMsg', 'Sin código')
            
            parsed = f"""Estado: {estado}
Código: {codigo_msg}
Descripción: {descripcion}"""
            
            # Agregar información adicional si existe
            if 'observaciones' in data:
                parsed += f"\nObservaciones: {data['observaciones']}"
            
            if 'fechaHora' in data:
                parsed += f"\nFecha/Hora MH: {data['fechaHora']}"
            
            if 'selloRecibido' in data:
                parsed += f"\nSello: {data['selloRecibido'][:50]}..."
            
            return parsed
        else:
            return str(data)

    def _parse_query_response(self, data):
        """Parsea respuesta de consulta de estado"""
        if isinstance(data, dict):
            estado = data.get('estado', 'DESCONOCIDO')
            
            parsed = f"Estado DTE: {estado}"
            
            if 'fechaHora' in data:
                parsed += f"\nFecha Procesamiento: {data['fechaHora']}"
            
            if 'observaciones' in data:
                parsed += f"\nObservaciones: {data['observaciones']}"
            
            return parsed
        else:
            return str(data)

    def _parse_auth_response(self, data):
        """Parsea respuesta de autenticación"""
        if isinstance(data, dict):
            body = data.get('body', {})
            status = data.get('status', 'DESCONOCIDO')
            
            parsed = f"Estado Autenticación: {status}"
            
            if 'token' in body:
                token_preview = body['token'][:20] + '...' if len(body['token']) > 20 else body['token']
                parsed += f"\nToken: {token_preview}"
            
            if 'expires_in' in body:
                parsed += f"\nExpira en: {body['expires_in']} segundos"
            
            return parsed
        else:
            return str(data)

    def action_view_request_data(self):
        """Acción para ver datos de petición en ventana separada"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Datos de Petición'),
            'res_model': 'l10n_sv.api.log.viewer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_title': f'Petición - {self.display_name}',
                'default_content': self.request_data,
                'default_content_type': 'json'
            }
        }

    def action_view_response_data(self):
        """Acción para ver datos de respuesta en ventana separada"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Datos de Respuesta'),
            'res_model': 'l10n_sv.api.log.viewer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_title': f'Respuesta - {self.display_name}',
                'default_content': self.response_data,
                'default_content_type': 'json'
            }
        }

    def action_retry_request(self):
        """Acción para reintentar petición fallida"""
        self.ensure_one()
        
        if self.status == 'success':
            raise exceptions.UserError(_('Esta petición ya fue exitosa'))
        
        if not self.move_id and self.request_type == 'send_dte':
            raise exceptions.UserError(_('No hay factura asociada para reintentar'))
        
        try:
            if self.request_type == 'send_dte':
                result = self.move_id.action_send_to_mh()
            elif self.request_type == 'query_status':
                result = self.move_id.action_query_mh_status()
            else:
                raise exceptions.UserError(_('Tipo de petición no soportada para reintento'))
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Reintento Exitoso'),
                    'message': _('La petición se ha reintentado correctamente'),
                    'type': 'success'
                }
            }
            
        except Exception as e:
            raise exceptions.UserError(_(
                'Error al reintentar petición: %s'
            ) % str(e))

    @api.model
    def cleanup_old_logs(self, days=90):
        """Limpia logs antiguos (llamado por cron)"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([('request_date', '<', cutoff_date)])
        
        count = len(old_logs)
        old_logs.unlink()
        
        _logger.info(f'Limpieza de logs API MH completada: {count} registros eliminados')
        return count


class L10nSvApiLogViewer(models.TransientModel):
    """Viewer para datos JSON de logs API"""
    _name = 'l10n_sv.api.log.viewer'
    _description = 'Visor de Datos Log API'

    title = fields.Char(
        string='Título',
        required=True
    )
    
    content = fields.Text(
        string='Contenido',
        required=True
    )
    
    content_type = fields.Selection([
        ('json', 'JSON'),
        ('text', 'Texto'),
        ('xml', 'XML')
    ], string='Tipo de Contenido', default='json')
    
    content_formatted = fields.Html(
        string='Contenido Formateado',
        compute='_compute_content_formatted'
    )

    @api.depends('content', 'content_type')
    def _compute_content_formatted(self):
        """Formatea contenido para visualización"""
        for viewer in self:
            if viewer.content_type == 'json' and viewer.content:
                try:
                    data = json.loads(viewer.content)
                    formatted = json.dumps(data, ensure_ascii=False, indent=2)
                    viewer.content_formatted = f'<pre style="background-color: #f8f9fa; padding: 15px; font-family: monospace; font-size: 12px; overflow: auto;">{formatted}</pre>'
                except json.JSONDecodeError:
                    viewer.content_formatted = f'<pre style="background-color: #f8f9fa; padding: 15px; font-family: monospace; font-size: 12px; overflow: auto;">{viewer.content}</pre>'
            else:
                viewer.content_formatted = f'<pre style="background-color: #f8f9fa; padding: 15px; font-family: monospace; font-size: 12px; overflow: auto;">{viewer.content}</pre>'