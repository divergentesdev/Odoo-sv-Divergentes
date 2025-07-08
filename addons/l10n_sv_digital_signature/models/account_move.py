import json
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Extensión de facturas para firma digital"""
    _inherit = 'account.move'

    # Estado de firma digital
    l10n_sv_signature_status = fields.Selection([
        ('draft', 'Sin Firmar'),
        ('signed', 'Firmado'),
        ('verified', 'Verificado'),
        ('invalid', 'Firma Inválida'),
        ('error', 'Error de Firma')
    ], string='Estado Firma', readonly=True, default='draft',
       help='Estado de la firma digital del documento')
    
    # Datos de firma
    l10n_sv_signature_data = fields.Text(
        string='Datos de Firma',
        readonly=True,
        help='Datos de la firma digital generada'
    )
    
    l10n_sv_signature_algorithm = fields.Char(
        string='Algoritmo de Firma',
        readonly=True,
        help='Algoritmo utilizado para la firma'
    )
    
    l10n_sv_signature_format = fields.Char(
        string='Formato de Firma',
        readonly=True,
        help='Formato de la firma digital'
    )
    
    l10n_sv_signature_date = fields.Datetime(
        string='Fecha de Firma',
        readonly=True,
        help='Fecha y hora de la firma digital'
    )
    
    l10n_sv_signature_certificate = fields.Char(
        string='Certificado de Firma',
        readonly=True,
        help='Información del certificado utilizado'
    )
    
    l10n_sv_signature_error = fields.Text(
        string='Error de Firma',
        readonly=True,
        help='Último error de firma digital'
    )
    
    # Verificación de firma
    l10n_sv_signature_verified = fields.Boolean(
        string='Firma Verificada',
        readonly=True,
        default=False,
        help='Indica si la firma ha sido verificada'
    )
    
    l10n_sv_signature_verification_date = fields.Datetime(
        string='Fecha Verificación',
        readonly=True,
        help='Fecha de última verificación de firma'
    )
    
    l10n_sv_signature_verification_result = fields.Text(
        string='Resultado Verificación',
        readonly=True,
        help='Resultado de la verificación de firma'
    )
    
    # Logs de firma
    l10n_sv_signature_log_ids = fields.One2many(
        'l10n_sv.signature.log',
        'move_id',
        string='Logs de Firma',
        readonly=True,
        help='Historial de operaciones de firma'
    )
    
    # JSON firmado
    l10n_sv_signed_json = fields.Text(
        string='JSON Firmado',
        readonly=True,
        help='JSON DTE con firma digital integrada'
    )

    def action_sign_dte(self):
        """Acción para firmar DTE digitalmente"""
        self.ensure_one()
        
        # Validaciones previas
        if self.state != 'posted':
            raise exceptions.UserError(_('Solo se pueden firmar facturas validadas'))
        
        # Safe boolean checks with getattr to handle missing fields
        json_generated = bool(getattr(self, 'l10n_sv_json_generated', False))
        json_validated = bool(getattr(self, 'l10n_sv_json_validated', False))
        
        if not json_generated:
            raise exceptions.UserError(_(
                'Debe generar el JSON DTE antes de firmar'
            ))
        
        if not json_validated:
            raise exceptions.UserError(_(
                'El JSON DTE debe estar validado antes de firmar'
            ))
        
        try:
            # Obtener servicio de firma
            signature_service = self.env['l10n_sv.digital.signature'].get_default_signature_service(
                self.company_id.id
            )
            
            # Obtener JSON DTE
            json_data = self.l10n_sv_json_dte
            if not json_data:
                raise exceptions.UserError(_('No hay JSON DTE para firmar'))
            
            # Preparar datos para firma
            document_data = {
                'json_dte': json_data,
                'numero_control': self.l10n_sv_edi_numero_control,
                'codigo_generacion': self.l10n_sv_edi_codigo_generacion,
                'tipo_documento': self.l10n_sv_document_type_id.code,
                'fecha_emision': self.invoice_date.isoformat() if self.invoice_date else None,
                'emisor_nit': self.company_id.l10n_sv_nit or self.company_id.vat,
                'receptor_documento': self.partner_id.vat,
                'monto_total': float(self.amount_total)
            }
            
            # Firmar documento
            result = signature_service.sign_document(
                data=document_data,
                document_type='json'
            )
            
            if result['success']:
                # Actualizar datos de firma
                self.write({
                    'l10n_sv_signature_status': 'signed',
                    'l10n_sv_signature_data': result['signature'],
                    'l10n_sv_signature_algorithm': signature_service.algorithm_id.name,
                    'l10n_sv_signature_format': signature_service.signature_format,
                    'l10n_sv_signature_date': fields.Datetime.now(),
                    'l10n_sv_signature_certificate': result['certificate_info']['subject'],
                    'l10n_sv_signature_error': False
                })
                
                # Crear JSON firmado integrado
                self._create_signed_json(result)
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Firma Digital Exitosa'),
                        'message': _('El DTE se ha firmado digitalmente'),
                        'type': 'success'
                    }
                }
            else:
                error_msg = result.get('error', 'Error desconocido en firma')
                self.write({
                    'l10n_sv_signature_status': 'error',
                    'l10n_sv_signature_error': error_msg
                })
                
                raise exceptions.UserError(_(
                    'Error firmando DTE: %s'
                ) % error_msg)
                
        except Exception as e:
            error_msg = str(e)
            self.write({
                'l10n_sv_signature_status': 'error',
                'l10n_sv_signature_error': error_msg
            })
            
            _logger.error(f'Error firmando DTE {self.name}: {error_msg}')
            raise exceptions.UserError(_(
                'Error firmando DTE: %s'
            ) % error_msg)

    def _create_signed_json(self, signature_result):
        """Crea JSON DTE con firma integrada"""
        self.ensure_one()
        
        try:
            # Parsear JSON original
            json_data = json.loads(self.l10n_sv_json_dte)
            
            # Agregar información de firma
            json_data['firmaElectronica'] = {
                'fechaFirma': self.l10n_sv_signature_date.isoformat(),
                'algoritmo': self.l10n_sv_signature_algorithm,
                'formato': self.l10n_sv_signature_format,
                'certificado': {
                    'sujeto': signature_result['certificate_info']['subject'],
                    'emisor': signature_result['certificate_info']['issuer'],
                    'numeroSerie': signature_result['certificate_info']['serial_number'],
                    'validoDesde': signature_result['certificate_info']['not_valid_before'],
                    'validoHasta': signature_result['certificate_info']['not_valid_after']
                },
                'firma': signature_result['signature'][:500] if len(signature_result['signature']) > 500 else signature_result['signature']
            }
            
            # Guardar JSON firmado
            self.l10n_sv_signed_json = json.dumps(json_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            _logger.warning(f'Error creando JSON firmado para {self.name}: {str(e)}')

    def action_verify_signature(self):
        """Acción para verificar firma digital"""
        self.ensure_one()
        
        if not self.l10n_sv_signature_data:
            raise exceptions.UserError(_('No hay firma digital para verificar'))
        
        try:
            # Obtener servicio de firma
            signature_service = self.env['l10n_sv.digital.signature'].get_default_signature_service(
                self.company_id.id
            )
            
            # Verificar firma
            original_data = self.l10n_sv_json_dte
            result = signature_service.verify_signature(
                self.l10n_sv_signature_data,
                original_data
            )
            
            # Actualizar estado
            if result['valid']:
                self.write({
                    'l10n_sv_signature_status': 'verified',
                    'l10n_sv_signature_verified': True,
                    'l10n_sv_signature_verification_date': fields.Datetime.now(),
                    'l10n_sv_signature_verification_result': result.get('message', 'Firma válida')
                })
                
                message = _('Firma digital válida')
                notification_type = 'success'
            else:
                self.write({
                    'l10n_sv_signature_status': 'invalid',
                    'l10n_sv_signature_verified': False,
                    'l10n_sv_signature_verification_date': fields.Datetime.now(),
                    'l10n_sv_signature_verification_result': result.get('error', 'Firma inválida')
                })
                
                message = _('Firma digital inválida: %s') % result.get('error', '')
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
            error_msg = str(e)
            self.write({
                'l10n_sv_signature_status': 'error',
                'l10n_sv_signature_verification_result': error_msg
            })
            
            raise exceptions.UserError(_(
                'Error verificando firma: %s'
            ) % error_msg)

    def action_view_signature_details(self):
        """Acción para ver detalles de firma"""
        self.ensure_one()
        
        if not self.l10n_sv_signature_data:
            raise exceptions.UserError(_('No hay firma digital para mostrar'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Detalles de Firma Digital'),
            'res_model': 'l10n_sv.signature.data.viewer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_title': f'Firma DTE - {self.name}',
                'default_signature_data': self.l10n_sv_signature_data,
                'default_algorithm': self.l10n_sv_signature_algorithm,
                'default_format': self.l10n_sv_signature_format,
                'default_certificate_info': self.l10n_sv_signature_certificate
            }
        }

    def action_view_signature_logs(self):
        """Acción para ver logs de firma"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Logs de Firma Digital'),
            'res_model': 'l10n_sv.signature.log',
            'view_mode': 'tree,form',
            'domain': [('move_id', '=', self.id)],
            'context': {'default_move_id': self.id}
        }

    def action_download_signed_json(self):
        """Acción para descargar JSON firmado"""
        self.ensure_one()
        
        if not self.l10n_sv_signed_json:
            raise exceptions.UserError(_('No hay JSON firmado para descargar'))
        
        # Generar nombre de archivo
        filename = f"DTE_FIRMADO_{self.l10n_sv_document_type_id.code}_{self.l10n_sv_edi_numero_control or 'DRAFT'}.json"
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=l10n_sv_signed_json&filename_field=filename&download=true',
            'target': 'self'
        }

    def action_reset_signature(self):
        """Acción para resetear firma digital"""
        self.ensure_one()
        
        self.write({
            'l10n_sv_signature_status': 'draft',
            'l10n_sv_signature_data': False,
            'l10n_sv_signature_algorithm': False,
            'l10n_sv_signature_format': False,
            'l10n_sv_signature_date': False,
            'l10n_sv_signature_certificate': False,
            'l10n_sv_signature_error': False,
            'l10n_sv_signature_verified': False,
            'l10n_sv_signature_verification_date': False,
            'l10n_sv_signature_verification_result': False,
            'l10n_sv_signed_json': False
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Firma Reseteada'),
                'message': _('La firma digital ha sido eliminada'),
                'type': 'info'
            }
        }

    @api.model
    def cron_sign_pending_dte(self):
        """Tarea programada para firmar DTE pendientes"""
        # Safe search with boolean validation
        try:
            pending_moves = self.search([
                ('state', '=', 'posted'),
                ('l10n_sv_signature_status', '=', 'draft'),
                ('l10n_sv_document_type_id', '!=', False)
            ])
            # Filter with safe boolean checks
            pending_moves = pending_moves.filtered(
                lambda m: bool(getattr(m, 'l10n_sv_json_validated', False))
            )
        except Exception:
            pending_moves = self.env['account.move']
        
        success_count = 0
        error_count = 0
        
        for move in pending_moves:
            try:
                move.action_sign_dte()
                success_count += 1
            except Exception as e:
                error_count += 1
                _logger.error(f'Error firmando DTE automático {move.name}: {str(e)}')
        
        _logger.info(f'Firma automática DTE completada: {success_count} exitosos, {error_count} errores')

    @api.model
    def cron_verify_signatures(self):
        """Tarea programada para verificar firmas existentes"""
        signed_moves = self.search([
            ('l10n_sv_signature_status', '=', 'signed'),
            ('l10n_sv_signature_verified', '=', False)
        ])
        
        for move in signed_moves:
            try:
                move.action_verify_signature()
            except Exception as e:
                _logger.error(f'Error verificando firma automática {move.name}: {str(e)}')
        
        _logger.info(f'Verificación automática de firmas completada para {len(signed_moves)} documentos')

    @api.depends('l10n_sv_signature_status')
    def _compute_edi_status(self):
        """Computa estado EDI incluyendo firma digital"""
        super()._compute_edi_status()
        
        for move in self:
            if move.l10n_sv_signature_status == 'verified':
                move.l10n_sv_edi_status = 'signed'
            elif move.l10n_sv_signature_status == 'invalid':
                move.l10n_sv_edi_status = 'signature_error'

    def write(self, vals):
        """Override para invalidar firma si cambian datos críticos"""
        result = super().write(vals)
        
        # Campos que invalidan la firma
        critical_fields = [
            'invoice_line_ids',
            'partner_id',
            'amount_total',
            'l10n_sv_json_dte'
        ]
        
        if any(field in vals for field in critical_fields):
            signed_moves = self.filtered(lambda m: m.l10n_sv_signature_status in ['signed', 'verified'])
            if signed_moves:
                signed_moves.write({
                    'l10n_sv_signature_status': 'invalid',
                    'l10n_sv_signature_verified': False,
                    'l10n_sv_signature_verification_result': _('Firma invalidada por cambios en documento')
                })
        
        return result