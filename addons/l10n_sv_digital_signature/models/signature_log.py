import json
import logging
from datetime import timedelta
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class L10nSvSignatureLog(models.Model):
    """Log de operaciones de firma digital"""
    _name = 'l10n_sv.signature.log'
    _description = 'Log de Firmas Digitales'
    _order = 'signature_date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )
    
    signature_service_id = fields.Many2one(
        'l10n_sv.digital.signature',
        string='Servicio de Firma',
        required=True,
        ondelete='cascade',
        help='Servicio de firma utilizado'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='signature_service_id.company_id',
        store=True,
        readonly=True
    )
    
    # Información del documento
    move_id = fields.Many2one(
        'account.move',
        string='Factura',
        ondelete='set null',
        help='Factura asociada si aplica'
    )
    
    document_type = fields.Selection([
        ('json', 'JSON DTE'),
        ('xml', 'XML'),
        ('pdf', 'PDF'),
        ('text', 'Texto'),
        ('test', 'Prueba'),
        ('other', 'Otro')
    ], string='Tipo de Documento', required=True,
       help='Tipo de documento firmado')
    
    document_reference = fields.Char(
        string='Referencia Documento',
        help='Referencia o identificador del documento'
    )
    
    # Información de la firma
    signature_date = fields.Datetime(
        string='Fecha de Firma',
        required=True,
        default=fields.Datetime.now
    )
    
    completion_date = fields.Datetime(
        string='Fecha de Finalización',
        help='Fecha y hora de finalización de la operación'
    )
    
    duration_ms = fields.Integer(
        string='Duración (ms)',
        compute='_compute_duration',
        store=True,
        help='Duración de la operación en milisegundos'
    )
    
    # Estado y resultado
    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('success', 'Exitoso'),
        ('error', 'Error'),
        ('timeout', 'Timeout')
    ], string='Estado', required=True, default='pending')
    
    error_message = fields.Text(
        string='Mensaje de Error',
        help='Descripción del error si la operación falló'
    )
    
    # Información técnica
    algorithm_used = fields.Char(
        string='Algoritmo Utilizado',
        help='Algoritmo de firma utilizado'
    )
    
    signature_format = fields.Char(
        string='Formato de Firma',
        help='Formato de la firma generada'
    )
    
    certificate_subject = fields.Char(
        string='Sujeto Certificado',
        help='Sujeto del certificado utilizado'
    )
    
    certificate_issuer = fields.Char(
        string='Emisor Certificado',
        help='Emisor del certificado utilizado'
    )
    
    certificate_serial = fields.Char(
        string='Serie Certificado',
        help='Número de serie del certificado'
    )
    
    # Datos de la operación
    input_hash = fields.Char(
        string='Hash Entrada',
        help='Hash de los datos de entrada'
    )
    
    signature_data = fields.Text(
        string='Datos de Firma',
        help='Datos de la firma generada (truncados para almacenamiento)'
    )
    
    signature_size = fields.Integer(
        string='Tamaño Firma (bytes)',
        help='Tamaño total de la firma en bytes'
    )
    
    # Metadatos adicionales
    client_info = fields.Char(
        string='Información Cliente',
        help='Información del cliente que solicitó la firma'
    )
    
    additional_data = fields.Text(
        string='Datos Adicionales',
        help='Datos adicionales en formato JSON'
    )

    @api.depends('document_type', 'document_reference', 'signature_date')
    def _compute_display_name(self):
        """Computa nombre de visualización"""
        for log in self:
            doc_types = dict(self._fields['document_type'].selection)
            type_name = doc_types.get(log.document_type, log.document_type)
            
            if log.document_reference:
                log.display_name = f"{type_name} - {log.document_reference}"
            else:
                log.display_name = f"{type_name} - {log.signature_date.strftime('%Y-%m-%d %H:%M')}"

    @api.depends('signature_date', 'completion_date')
    def _compute_duration(self):
        """Computa duración de la operación"""
        for log in self:
            if log.signature_date and log.completion_date:
                duration = log.completion_date - log.signature_date
                log.duration_ms = int(duration.total_seconds() * 1000)
            else:
                log.duration_ms = 0

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para generar hash de entrada"""
        for vals in vals_list:
            # Generar hash de entrada si no se proporciona
            if not vals.get('input_hash') and vals.get('additional_data'):
                try:
                    import hashlib
                    data = vals['additional_data'].encode('utf-8')
                    vals['input_hash'] = hashlib.sha256(data).hexdigest()[:16]
                except Exception:
                    pass
        
        return super().create(vals_list)

    def action_view_signature_data(self):
        """Acción para ver datos de firma en ventana separada"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Datos de Firma'),
            'res_model': 'l10n_sv.signature.data.viewer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_title': f'Firma - {self.display_name}',
                'default_signature_data': self.signature_data,
                'default_algorithm': self.algorithm_used,
                'default_format': self.signature_format,
                'default_certificate_info': f"""
Sujeto: {self.certificate_subject or 'N/A'}
Emisor: {self.certificate_issuer or 'N/A'}
Serie: {self.certificate_serial or 'N/A'}
                """.strip()
            }
        }

    def action_retry_signature(self):
        """Acción para reintentar operación de firma"""
        self.ensure_one()
        
        if self.status == 'success':
            raise exceptions.UserError(_('Esta firma ya fue exitosa'))
        
        if not self.move_id:
            raise exceptions.UserError(_('No hay factura asociada para reintentar'))
        
        try:
            # Reintentar firma en la factura
            result = self.move_id.action_sign_dte()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Reintento Exitoso'),
                    'message': _('La firma se ha reintentado correctamente'),
                    'type': 'success'
                }
            }
            
        except Exception as e:
            raise exceptions.UserError(_(
                'Error al reintentar firma: %s'
            ) % str(e))

    def action_verify_signature(self):
        """Acción para verificar firma"""
        self.ensure_one()
        
        if not self.signature_data:
            raise exceptions.UserError(_('No hay datos de firma para verificar'))
        
        try:
            # Verificar con el servicio de firma
            result = self.signature_service_id.verify_signature(self.signature_data)
            
            if result.get('valid'):
                message = _('Firma válida: %s') % result.get('message', '')
                notification_type = 'success'
            else:
                message = _('Firma inválida: %s') % result.get('error', '')
                notification_type = 'danger'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Verificación de Firma'),
                    'message': message,
                    'type': notification_type
                }
            }
            
        except Exception as e:
            raise exceptions.UserError(_(
                'Error verificando firma: %s'
            ) % str(e))

    @api.model
    def cleanup_old_logs(self, days=180):
        """Limpia logs antiguos (llamado por cron)"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([
            ('signature_date', '<', cutoff_date),
            ('status', 'in', ['success', 'error'])  # Mantener pendientes
        ])
        
        count = len(old_logs)
        old_logs.unlink()
        
        _logger.info(f'Limpieza de logs de firma completada: {count} registros eliminados')
        return count

    @api.model
    def get_signature_statistics(self, days=30):
        """Obtiene estadísticas de firma de los últimos días"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        
        logs = self.search([('signature_date', '>=', cutoff_date)])
        
        total = len(logs)
        successful = len(logs.filtered(lambda l: l.status == 'success'))
        failed = len(logs.filtered(lambda l: l.status == 'error'))
        pending = len(logs.filtered(lambda l: l.status == 'pending'))
        
        avg_duration = 0
        if successful > 0:
            successful_logs = logs.filtered(lambda l: l.status == 'success' and l.duration_ms > 0)
            if successful_logs:
                avg_duration = sum(successful_logs.mapped('duration_ms')) / len(successful_logs)
        
        # Estadísticas por tipo de documento
        doc_types = {}
        for log in logs:
            doc_type = log.document_type
            if doc_type not in doc_types:
                doc_types[doc_type] = {'total': 0, 'success': 0}
            doc_types[doc_type]['total'] += 1
            if log.status == 'success':
                doc_types[doc_type]['success'] += 1
        
        # Estadísticas por algoritmo
        algorithms = {}
        for log in logs.filtered(lambda l: l.algorithm_used):
            alg = log.algorithm_used
            if alg not in algorithms:
                algorithms[alg] = {'total': 0, 'success': 0}
            algorithms[alg]['total'] += 1
            if log.status == 'success':
                algorithms[alg]['success'] += 1
        
        return {
            'period_days': days,
            'total_signatures': total,
            'successful_signatures': successful,
            'failed_signatures': failed,
            'pending_signatures': pending,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'average_duration_ms': avg_duration,
            'by_document_type': doc_types,
            'by_algorithm': algorithms
        }

    def action_view_related_move(self):
        """Acción para ver factura relacionada"""
        self.ensure_one()
        
        if not self.move_id:
            raise exceptions.UserError(_('No hay factura asociada'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Factura'),
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'target': 'current'
        }


class L10nSvSignatureDataViewer(models.TransientModel):
    """Visor para datos de firma"""
    _name = 'l10n_sv.signature.data.viewer'
    _description = 'Visor de Datos de Firma'

    title = fields.Char(
        string='Título',
        required=True
    )
    
    signature_data = fields.Text(
        string='Datos de Firma',
        required=True
    )
    
    algorithm = fields.Char(
        string='Algoritmo',
        readonly=True
    )
    
    format = fields.Char(
        string='Formato',
        readonly=True
    )
    
    certificate_info = fields.Text(
        string='Información Certificado',
        readonly=True
    )
    
    signature_formatted = fields.Html(
        string='Firma Formateada',
        compute='_compute_signature_formatted'
    )
    
    signature_length = fields.Integer(
        string='Longitud',
        compute='_compute_signature_stats'
    )
    
    signature_type = fields.Char(
        string='Tipo Detectado',
        compute='_compute_signature_stats'
    )

    @api.depends('signature_data')
    def _compute_signature_formatted(self):
        """Formatea datos de firma para visualización"""
        for viewer in self:
            if viewer.signature_data:
                data = viewer.signature_data
                
                # Detectar formato y formatear apropiadamente
                if data.startswith('<?xml'):
                    # XML - formatear con indentación
                    try:
                        from lxml import etree
                        parsed = etree.fromstring(data.encode('utf-8'))
                        formatted = etree.tostring(parsed, pretty_print=True, encoding='unicode')
                        viewer.signature_formatted = f'<pre style="background-color: #f8f9fa; padding: 15px; font-family: monospace; font-size: 12px; overflow: auto;">{formatted}</pre>'
                    except Exception:
                        viewer.signature_formatted = f'<pre style="background-color: #f8f9fa; padding: 15px; font-family: monospace; font-size: 12px; overflow: auto;">{data}</pre>'
                        
                elif '.' in data and len(data.split('.')) == 3:
                    # Posible JWT/JWS
                    parts = data.split('.')
                    formatted = f"""
<div style="background-color: #f8f9fa; padding: 15px; font-family: monospace; font-size: 12px;">
<strong>Header:</strong><br>
{parts[0]}<br><br>
<strong>Payload:</strong><br>
{parts[1]}<br><br>
<strong>Signature:</strong><br>
{parts[2]}
</div>
                    """
                    viewer.signature_formatted = formatted
                    
                else:
                    # Firma base64 u otro formato
                    # Dividir en líneas de 64 caracteres
                    lines = [data[i:i+64] for i in range(0, len(data), 64)]
                    formatted = '<br>'.join(lines)
                    viewer.signature_formatted = f'<pre style="background-color: #f8f9fa; padding: 15px; font-family: monospace; font-size: 12px; overflow: auto;">{formatted}</pre>'
            else:
                viewer.signature_formatted = '<p>No hay datos de firma para mostrar</p>'

    @api.depends('signature_data')
    def _compute_signature_stats(self):
        """Computa estadísticas de la firma"""
        for viewer in self:
            if viewer.signature_data:
                viewer.signature_length = len(viewer.signature_data)
                
                # Detectar tipo
                data = viewer.signature_data
                if data.startswith('<?xml'):
                    viewer.signature_type = 'XML Digital Signature'
                elif '.' in data and len(data.split('.')) == 3:
                    viewer.signature_type = 'JSON Web Signature (JWS)'
                elif data.startswith('-----BEGIN'):
                    viewer.signature_type = 'PEM Format'
                elif all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in data):
                    viewer.signature_type = 'Base64 Encoded'
                else:
                    viewer.signature_type = 'Unknown Format'
            else:
                viewer.signature_length = 0
                viewer.signature_type = 'No Data'