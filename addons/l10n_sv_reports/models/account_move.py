import base64
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Extensión de facturas para reportes DTE"""
    _inherit = 'account.move'

    # Datos de reportes DTE
    l10n_sv_qr_code = fields.Text(
        string='Código QR',
        readonly=True,
        help='Código QR generado para el DTE'
    )
    
    l10n_sv_qr_generated = fields.Boolean(
        string='QR Generado',
        readonly=True,
        default=False,
        help='Indica si el código QR ha sido generado'
    )
    
    l10n_sv_qr_generation_date = fields.Datetime(
        string='Fecha Generación QR',
        readonly=True,
        help='Fecha y hora de generación del QR'
    )
    
    l10n_sv_barcode = fields.Text(
        string='Código de Barras',
        readonly=True,
        help='Código de barras adicional para el DTE'
    )
    
    l10n_sv_report_template_id = fields.Many2one(
        'l10n_sv.report.template',
        string='Plantilla de Reporte',
        help='Plantilla personalizada para este documento'
    )
    
    # Estado de impresión
    l10n_sv_printed = fields.Boolean(
        string='Impreso',
        default=False,
        help='Indica si el documento ha sido impreso'
    )
    
    l10n_sv_print_date = fields.Datetime(
        string='Fecha de Impresión',
        readonly=True,
        help='Fecha y hora de primera impresión'
    )
    
    l10n_sv_print_count = fields.Integer(
        string='Contador de Impresiones',
        readonly=True,
        default=0,
        help='Número de veces que se ha impreso'
    )

    def action_generate_qr_code(self):
        """Acción para generar código QR del DTE"""
        self.ensure_one()
        
        if not self.l10n_sv_document_type_id:
            raise exceptions.UserError(_('Debe asignar un tipo de documento DTE'))
        
        try:
            # Obtener generador QR
            qr_generator = self.env['l10n_sv.qr.code.generator'].get_default_qr_generator(
                self.company_id.id
            )
            
            # Generar QR con logo si está disponible
            if self.company_id.logo:
                result = qr_generator.generate_qr_with_logo(self.id, self.company_id.logo)
            else:
                result = qr_generator.generate_qr_code(self.id)
            
            if result['success']:
                self.write({
                    'l10n_sv_qr_code': result['qr_code'],
                    'l10n_sv_qr_generated': True,
                    'l10n_sv_qr_generation_date': fields.Datetime.now()
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('QR Generado'),
                        'message': _('El código QR se ha generado correctamente'),
                        'type': 'success'
                    }
                }
            else:
                raise exceptions.UserError(_('Error generando código QR'))
                
        except Exception as e:
            raise exceptions.UserError(_(
                'Error generando código QR: %s'
            ) % str(e))

    def action_generate_barcode(self):
        """Acción para generar código de barras"""
        self.ensure_one()
        
        try:
            # Obtener generador QR (que también maneja códigos de barras)
            qr_generator = self.env['l10n_sv.qr.code.generator'].get_default_qr_generator(
                self.company_id.id
            )
            
            result = qr_generator.generate_barcode(self.id, 'code128')
            
            if result['success']:
                self.l10n_sv_barcode = result['barcode']
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Código de Barras Generado'),
                        'message': _('El código de barras se ha generado correctamente'),
                        'type': 'success'
                    }
                }
            else:
                raise exceptions.UserError(_('Error generando código de barras'))
                
        except Exception as e:
            raise exceptions.UserError(_(
                'Error generando código de barras: %s'
            ) % str(e))

    def action_print_dte_report(self):
        """Acción para imprimir reporte DTE personalizado"""
        self.ensure_one()
        
        # Generar QR si no existe
        if not self.l10n_sv_qr_generated:
            self.action_generate_qr_code()
        
        # Obtener plantilla
        if not self.l10n_sv_report_template_id:
            template = self.env['l10n_sv.report.template'].get_template_for_document(
                self.l10n_sv_document_type_id.id if self.l10n_sv_document_type_id else False,
                self.company_id.id
            )
            self.l10n_sv_report_template_id = template.id
        
        # Actualizar contador de impresiones
        if not self.l10n_sv_printed:
            self.l10n_sv_printed = True
            self.l10n_sv_print_date = fields.Datetime.now()
        
        self.l10n_sv_print_count += 1
        
        return {
            'type': 'ir.actions.report',
            'report_name': 'l10n_sv_reports.invoice_dte_report',
            'report_type': 'qweb-pdf',
            'data': {
                'template_id': self.l10n_sv_report_template_id.id,
                'include_qr': True,
                'include_signature_info': True,
                'include_mh_info': True
            },
            'context': {'active_id': self.id}
        }

    def action_preview_dte_report(self):
        """Acción para previsualizar reporte DTE"""
        self.ensure_one()
        
        # Generar QR si no existe
        if not self.l10n_sv_qr_generated:
            self.action_generate_qr_code()
        
        return {
            'type': 'ir.actions.report',
            'report_name': 'l10n_sv_reports.invoice_dte_report',
            'report_type': 'qweb-html',
            'data': {
                'template_id': self.l10n_sv_report_template_id.id if self.l10n_sv_report_template_id else False,
                'preview_mode': True
            },
            'context': {'active_id': self.id}
        }

    def action_download_qr_image(self):
        """Acción para descargar imagen QR"""
        self.ensure_one()
        
        if not self.l10n_sv_qr_code:
            raise exceptions.UserError(_('No hay código QR generado'))
        
        # Preparar archivo para descarga
        filename = f"QR_{self.l10n_sv_document_type_id.code}_{self.l10n_sv_edi_numero_control or self.name}.png"
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=l10n_sv_qr_code&filename={filename}&download=true',
            'target': 'self'
        }

    def action_email_dte_report(self):
        """Acción para enviar reporte DTE por correo"""
        self.ensure_one()
        
        # Verificar que hay correo electrónico
        if not self.partner_id.email:
            raise exceptions.UserError(_(
                'El cliente no tiene correo electrónico configurado'
            ))
        
        # Generar QR si no existe
        if not self.l10n_sv_qr_generated:
            self.action_generate_qr_code()
        
        # Generar PDF
        report = self.env.ref('l10n_sv_reports.invoice_dte_report')
        pdf_content, _ = report._render_qweb_pdf(self.ids, data={
            'template_id': self.l10n_sv_report_template_id.id if self.l10n_sv_report_template_id else False
        })
        
        # Crear adjunto
        filename = f"DTE_{self.l10n_sv_document_type_id.code}_{self.l10n_sv_edi_numero_control or self.name}.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        
        # Preparar template de correo
        mail_template = self.env.ref('l10n_sv_reports.email_template_dte_invoice', raise_if_not_found=False)
        
        if mail_template:
            # Usar template personalizado
            mail_template.attachment_ids = [(6, 0, [attachment.id])]
            mail_template.send_mail(self.id, force_send=True)
            mail_template.attachment_ids = [(5, 0, 0)]  # Limpiar adjuntos
        else:
            # Crear correo básico
            mail_values = {
                'subject': f'Documento Electrónico - {self.name}',
                'body_html': f'''
                    <p>Estimado/a {self.partner_id.name},</p>
                    <p>Adjunto encontrará su documento tributario electrónico.</p>
                    <p><strong>Documento:</strong> {self.l10n_sv_document_type_id.name if self.l10n_sv_document_type_id else 'Factura'}</p>
                    <p><strong>Número:</strong> {self.name}</p>
                    <p><strong>Fecha:</strong> {self.invoice_date}</p>
                    <p><strong>Total:</strong> {self.currency_id.symbol} {self.amount_total:,.2f}</p>
                    <br>
                    <p>Saludos cordiales,<br>{self.company_id.name}</p>
                ''',
                'email_to': self.partner_id.email,
                'email_from': self.company_id.email or self.env.user.email,
                'attachment_ids': [(6, 0, [attachment.id])]
            }
            
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Correo Enviado'),
                'message': _('El documento DTE se ha enviado por correo a %s') % self.partner_id.email,
                'type': 'success'
            }
        }

    def get_dte_status_badge(self):
        """Obtiene badge de estado DTE para reportes"""
        self.ensure_one()
        
        if self.l10n_sv_mh_status == 'approved':
            return {
                'text': 'APROBADO MH',
                'color': '#10b981',  # green
                'background': '#d1fae5'
            }
        elif self.l10n_sv_mh_status == 'processed':
            return {
                'text': 'PROCESADO MH',
                'color': '#3b82f6',  # blue
                'background': '#dbeafe'
            }
        elif self.l10n_sv_mh_status == 'rejected':
            return {
                'text': 'RECHAZADO MH',
                'color': '#ef4444',  # red
                'background': '#fee2e2'
            }
        elif self.l10n_sv_signature_status == 'verified':
            return {
                'text': 'FIRMADO DIGITALMENTE',
                'color': '#8b5cf6',  # purple
                'background': '#ede9fe'
            }
        elif self.l10n_sv_json_validated:
            return {
                'text': 'JSON VALIDADO',
                'color': '#f59e0b',  # amber
                'background': '#fef3c7'
            }
        else:
            return {
                'text': 'BORRADOR',
                'color': '#6b7280',  # gray
                'background': '#f3f4f6'
            }

    def get_dte_summary_data(self):
        """Obtiene datos resumidos para reporte"""
        self.ensure_one()
        
        return {
            'numero_control': self.l10n_sv_edi_numero_control or 'Pendiente',
            'codigo_generacion': self.l10n_sv_edi_codigo_generacion or 'Pendiente',
            'tipo_documento': self.l10n_sv_document_type_id.name if self.l10n_sv_document_type_id else 'No asignado',
            'fecha_emision': self.invoice_date.strftime('%d/%m/%Y') if self.invoice_date else '',
            'hora_emision': self.create_date.strftime('%H:%M:%S'),
            'estado_edi': dict(self._fields['l10n_sv_edi_status'].selection).get(self.l10n_sv_edi_status, self.l10n_sv_edi_status),
            'estado_firma': dict(self._fields['l10n_sv_signature_status'].selection).get(self.l10n_sv_signature_status, self.l10n_sv_signature_status),
            'estado_mh': dict(self._fields['l10n_sv_mh_status'].selection).get(self.l10n_sv_mh_status, self.l10n_sv_mh_status),
            'fecha_firma': self.l10n_sv_signature_date.strftime('%d/%m/%Y %H:%M:%S') if self.l10n_sv_signature_date else '',
            'fecha_envio_mh': self.l10n_sv_mh_send_date.strftime('%d/%m/%Y %H:%M:%S') if self.l10n_sv_mh_send_date else '',
            'sello_mh': self.l10n_sv_mh_sello[:100] + '...' if self.l10n_sv_mh_sello and len(self.l10n_sv_mh_sello) > 100 else self.l10n_sv_mh_sello or ''
        }

    @api.model
    def cron_generate_missing_qr_codes(self):
        """Tarea programada para generar QR faltantes"""
        moves_without_qr = self.search([
            ('state', '=', 'posted'),
            ('l10n_sv_document_type_id', '!=', False),
            ('l10n_sv_qr_generated', '=', False)
        ])
        
        success_count = 0
        error_count = 0
        
        for move in moves_without_qr:
            try:
                move.action_generate_qr_code()
                success_count += 1
            except Exception as e:
                error_count += 1
                _logger.error(f'Error generando QR automático para {move.name}: {str(e)}')
        
        _logger.info(f'Generación automática QR completada: {success_count} exitosos, {error_count} errores')

    def write(self, vals):
        """Override para regenerar QR si cambian datos críticos"""
        result = super().write(vals)
        
        # Campos que requieren regeneración de QR
        qr_sensitive_fields = [
            'l10n_sv_edi_numero_control',
            'l10n_sv_edi_codigo_generacion',
            'l10n_sv_signature_status',
            'l10n_sv_mh_status',
            'amount_total'
        ]
        
        if any(field in vals for field in qr_sensitive_fields):
            qr_moves = self.filtered(lambda m: m.l10n_sv_qr_generated)
            if qr_moves:
                # Marcar QR como desactualizado sin regenerar automáticamente
                qr_moves.write({'l10n_sv_qr_generated': False})
        
        return result