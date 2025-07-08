import json
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Extensión de facturas para generación de JSON DTE"""
    _inherit = 'account.move'

    # Campo para el tipo de documento DTE real
    l10n_sv_document_type_id = fields.Many2one(
        'l10n_sv.document.type',
        string='Tipo de Documento DTE',
        help='Tipo de documento tributario electrónico'
    )

    # Campo que faltaba - número de control DTE
    l10n_sv_edi_numero_control = fields.Char(
        string='Número de Control DTE',
        help='Número de control asignado por el Ministerio de Hacienda'
    )

    # Campo para el código de generación
    l10n_sv_edi_codigo_generacion = fields.Char(
        string='Código de Generación DTE',
        help='UUID único del documento tributario electrónico'
    )

    # Campo para el estado del DTE específico de JSON
    l10n_sv_json_dte_status = fields.Selection([
        ('draft', 'Borrador'),
        ('ready', 'Listo para enviar'),
        ('json_ready', 'JSON Generado'),
        ('sent', 'Enviado'),
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado'),
        ('error', 'Error')
    ], string='Estado JSON DTE', default='draft', help='Estado del documento tributario electrónico JSON')

    l10n_sv_json_dte = fields.Text(
        string='JSON DTE',
        readonly=True,
        help='JSON del documento tributario electrónico generado'
    )
    
    l10n_sv_json_emitted_date = fields.Datetime(
        string='Fecha Emisión JSON',
        readonly=True,
        help='Fecha y hora de emisión del JSON DTE'
    )
    
    l10n_sv_json_generator_id = fields.Many2one(
        'l10n_sv.json.generator',
        string='Generador JSON',
        readonly=True,
        help='Generador utilizado para crear el JSON DTE'
    )
    
    l10n_sv_json_generated = fields.Boolean(
        string='JSON Generado',
        readonly=True,
        default=False,
        help='Indica si el JSON DTE ha sido generado'
    )
    
    l10n_sv_json_validated = fields.Boolean(
        string='JSON Validado',
        readonly=True,
        default=False,
        help='Indica si el JSON DTE ha sido validado exitosamente'
    )
    
    l10n_sv_json_errors = fields.Text(
        string='Errores de Validación JSON',
        readonly=True,
        help='Errores encontrados durante la validación del JSON'
    )
    
    l10n_sv_json_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Archivo JSON DTE',
        readonly=True,
        help='Archivo adjunto del JSON DTE generado'
    )
    
    l10n_sv_pdf_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Archivo PDF DTE',
        readonly=True,
        help='Archivo adjunto del PDF DTE generado'
    )
    
    l10n_sv_json_content = fields.Text(
        string='Contenido JSON',
        readonly=True,
        help='Contenido del JSON DTE para previsualización'
    )

    def action_generate_json_dte(self):
        """Acción para generar JSON DTE directamente sin wizard"""
        self.ensure_one()
        
        if not self.l10n_sv_document_type_id:
            raise exceptions.UserError(_('Debe asignar un tipo de documento DTE a la factura'))
        
        if not self.l10n_sv_edi_numero_control:
            raise exceptions.UserError(_('La factura debe tener un número de control DTE'))
        
        # Buscar generador apropiado basado en el tipo de documento
        if self.l10n_sv_json_generator_id:
            generator = self.l10n_sv_json_generator_id
        else:
            # Si no hay generador asignado, buscar uno basado en el tipo de documento
            generator = self.env['l10n_sv.json.generator'].search([
                ('document_type_id', '=', self.l10n_sv_document_type_id.id),
                ('active', '=', True)
            ], limit=1)
        
        if not generator:
            raise exceptions.UserError(_(
                'No se encontró un generador JSON para el tipo de documento %s'
            ) % (self.l10n_sv_document_type_id.name if self.l10n_sv_document_type_id else 'especificado'))
        
        try:
            # Generar JSON
            json_data = generator.generate_json_dte(self.id)
            
            # Log temporal para depuración
            if hasattr(generator, 'document_type_code') and generator.document_type_code == '03':
                _logger.info("JSON generado para CCF antes de formatear:")
                _logger.info(f"Tiene codTributo en items: {'codTributo' in json_data.get('cuerpoDocumento', [{}])[0]}")
                _logger.info(f"Tiene ivaItem en items: {'ivaItem' in json_data.get('cuerpoDocumento', [{}])[0]}")
                
            # Validar JSON
            generator.validate_json(json_data, self)
            
            # Formatear para almacenamiento
            document_type_code = getattr(generator, 'document_type_code', '01')
            formatted_json = generator.format_json_output(json_data, document_type_code)
            
            # Actualizar factura
            self.write({
                'l10n_sv_json_dte': formatted_json,
                'l10n_sv_json_generator_id': generator.id,
                'l10n_sv_json_generated': True,
                'l10n_sv_json_validated': True,
                'l10n_sv_json_errors': False,
                'l10n_sv_json_dte_status': 'json_ready',
                'l10n_sv_json_emitted_date': fields.Datetime.now(),
                'l10n_sv_json_content': formatted_json
            })
            
            # Retornar notificación de éxito en lugar del wizard
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('JSON DTE Generado'),
                    'message': _('El JSON DTE se ha generado exitosamente'),
                    'type': 'success'
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            self.write({
                'l10n_sv_json_errors': error_msg,
                'l10n_sv_json_validated': False,
                'l10n_sv_json_dte_status': 'error'
            })
            raise exceptions.UserError(_(
                'Error al generar JSON DTE: %s'
            ) % error_msg)

    def action_generate_json_from_document_type(self):
        """Genera JSON DTE usando el tipo de documento directamente sin wizard"""
        self.ensure_one()
        
        if not self.l10n_sv_document_type_id:
            raise exceptions.UserError(_('Debe asignar un tipo de documento DTE a la factura'))
        
        # Usar el método del tipo de documento que busca el generador internamente
        try:
            json_data = self.l10n_sv_document_type_id.generate_json_dte(self.id)
            
            # El tipo de documento ya devuelve el JSON formateado
            self.write({
                'l10n_sv_json_dte': json_data,
                'l10n_sv_json_generated': True,
                'l10n_sv_json_validated': True,
                'l10n_sv_json_errors': False,
                'l10n_sv_json_dte_status': 'json_ready',
                'l10n_sv_json_emitted_date': fields.Datetime.now(),
                'l10n_sv_json_content': json_data
            })
            
            # Retornar notificación de éxito en lugar del wizard
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('JSON DTE Generado'),
                    'message': _('El JSON DTE se ha generado exitosamente usando el tipo de documento'),
                    'type': 'success'
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            self.write({
                'l10n_sv_json_errors': error_msg,
                'l10n_sv_json_generated': False,
                'l10n_sv_json_validated': False,
                'l10n_sv_json_dte_status': 'error'
            })
            raise exceptions.UserError(_(
                'Error al generar JSON DTE: %s'
            ) % error_msg)

    def action_view_json_dte(self):
        """Acción para ver el JSON DTE generado"""
        self.ensure_one()
        
        if not self.l10n_sv_json_dte:
            raise exceptions.UserError(_('No hay JSON DTE generado para esta factura'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'JSON DTE Generado',
            'res_model': 'l10n_sv.json.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
                'default_json_content': self.l10n_sv_json_dte
            }
        }

    def action_preview_json_dte(self):
        """Acción para vista previa del JSON DTE (siempre abre wizard)"""
        self.ensure_one()
        
        # Si no existe JSON, generarlo primero
        if not self.l10n_sv_json_dte:
            # Generar JSON sin mostrar notificación
            if not self.l10n_sv_document_type_id:
                raise exceptions.UserError(_('Debe asignar un tipo de documento DTE a la factura'))
            
            generator = self.env['l10n_sv.json.generator'].search([
                ('document_type_id', '=', self.l10n_sv_document_type_id.id),
                ('active', '=', True)
            ], limit=1)
            
            if not generator:
                raise exceptions.UserError(_(
                    'No se encontró un generador JSON para el tipo de documento %s'
                ) % self.l10n_sv_document_type_id.name)
            
            try:
                json_data = generator.generate_json_dte(self.id)
                formatted_json = generator.format_json_output(json_data, self.l10n_sv_document_type_id.code)
                
                self.write({
                    'l10n_sv_json_dte': formatted_json,
                    'l10n_sv_json_generator_id': generator.id,
                    'l10n_sv_json_generated': True,
                    'l10n_sv_json_validated': True,
                    'l10n_sv_json_errors': False,
                    'l10n_sv_json_dte_status': 'json_ready',
                    'l10n_sv_json_emitted_date': fields.Datetime.now(),
                    'l10n_sv_json_content': formatted_json
                })
            except Exception as e:
                error_msg = str(e)
                self.write({
                    'l10n_sv_json_errors': error_msg,
                    'l10n_sv_json_validated': False,
                    'l10n_sv_json_dte_status': 'error'
                })
                raise exceptions.UserError(_(
                    'Error al generar JSON DTE para vista previa: %s'
                ) % error_msg)
        
        # Siempre abrir wizard para vista previa
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vista Previa JSON DTE',
            'res_model': 'l10n_sv.json.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
                'default_json_content': self.l10n_sv_json_dte
            }
        }
    
    def action_validate_json_dte(self):
        """Acción para validar JSON DTE existente"""
        self.ensure_one()
        
        if not self.l10n_sv_json_dte:
            raise exceptions.UserError(_('No hay JSON DTE para validar'))
        
        try:
            json_data = json.loads(self.l10n_sv_json_dte)
            self.l10n_sv_json_generator_id.validate_json(json_data, self)
            
            self.write({
                'l10n_sv_json_validated': True,
                'l10n_sv_json_errors': False
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Validación Exitosa'),
                    'message': _('El JSON DTE es válido según las especificaciones técnicas'),
                    'type': 'success'
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            self.write({
                'l10n_sv_json_errors': error_msg,
                'l10n_sv_json_validated': False
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error de Validación'),
                    'message': error_msg,
                    'type': 'danger'
                }
            }

    def action_regenerate_json_dte(self):
        """Acción para regenerar JSON DTE directamente sin wizard"""
        self.ensure_one()
        
        # Limpiar campos JSON existentes
        self.write({
            'l10n_sv_json_dte': False,
            'l10n_sv_json_generated': False,
            'l10n_sv_json_validated': False,
            'l10n_sv_json_errors': False,
            'l10n_sv_json_dte_status': 'ready'
        })
        
        # Generar nuevamente (ya retorna notificación directa)
        return self.action_generate_json_dte()

    @api.model
    def get_pending_json_generation(self):
        """Obtener facturas pendientes de generación JSON"""
        return self.search([
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('l10n_sv_document_type_id', '!=', False),
            ('l10n_sv_edi_numero_control', '!=', False),
            ('l10n_sv_json_generated', '=', False)
        ])

    def action_bulk_generate_json(self):
        """Generar JSON para múltiples facturas"""
        for move in self:
            if move.state == 'posted' and move.l10n_sv_document_type_id and move.l10n_sv_edi_numero_control:
                try:
                    move.action_generate_json_dte()
                except Exception as e:
                    _logger.error(f"Error generando JSON para factura {move.name}: {e}")
                    continue

    @api.model
    def _compute_json_status_batch(self):
        """Actualizar estado JSON en lote para facturas con cambios"""
        moves_to_update = self.search([
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('l10n_sv_json_generated', '=', True)
        ])
        
        for move in moves_to_update:
            try:
                if move.l10n_sv_json_dte_status == 'ready':
                    move.l10n_sv_json_dte_status = 'json_ready'
            except Exception as e:
                _logger.warning(f"Error actualizando estado para {move.name}: {e}")

    def _has_significant_changes(self):
        """Detectar si la factura tiene cambios significativos que requieren regenerar JSON"""
        self.ensure_one()
        
        sensitive_fields = [
            'invoice_line_ids',
            'partner_id',
            'l10n_sv_document_type_id',
            'currency_id',
            'invoice_payment_term_id',
            'amount_total'
        ]
        
        return any(self._fields[field].compute for field in sensitive_fields if field in self._fields)

    def write(self, vals):
        """Override write para detectar cambios que requieren regenerar JSON"""
        result = super().write(vals)
        
        # Si hay cambios significativos y ya se había generado JSON, marcar para regenerar
        sensitive_fields = ['invoice_line_ids', 'partner_id', 'l10n_sv_document_type_id']
        
        if any(field in vals for field in sensitive_fields):
            for record in self:
                if record.l10n_sv_json_generated:
                    record.write({
                        'l10n_sv_json_validated': False,
                        'l10n_sv_json_errors': _('Factura modificada. JSON necesita regeneración.'),
                        'l10n_sv_json_dte_status': 'ready'
                    })
        
        return result

    def get_json_dte_dict(self):
        """Obtiene el JSON DTE como diccionario para envío al MH"""
        self.ensure_one()
        
        # Si ya existe JSON generado, usarlo
        if self.l10n_sv_json_dte:
            try:
                return json.loads(self.l10n_sv_json_dte)
            except json.JSONDecodeError:
                _logger.error(f"Error parseando JSON DTE existente para factura {self.name}")
        
        # Si no existe JSON, generarlo
        if not self.l10n_sv_document_type_id:
            raise exceptions.UserError(_('Debe asignar un tipo de documento DTE a la factura'))
        
        # Buscar generador apropiado
        generator = self.env['l10n_sv.json.generator'].search([
            ('document_type_id', '=', self.l10n_sv_document_type_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not generator:
            raise exceptions.UserError(_(
                'No se encontró un generador JSON activo para el tipo de documento %s'
            ) % self.l10n_sv_document_type_id.name)
        
        try:
            # Generar JSON usando el generador
            json_data = generator.generate_json_dte(self.id)
            
            # Guardar el JSON generado
            formatted_json = generator.format_json_output(json_data, self.l10n_sv_document_type_id.code)
            self.write({
                'l10n_sv_json_dte': formatted_json,
                'l10n_sv_json_generator_id': generator.id,
                'l10n_sv_json_generated': True,
                'l10n_sv_json_emitted_date': fields.Datetime.now(),
                'l10n_sv_json_content': formatted_json
            })
            
            return json_data
            
        except Exception as e:
            error_msg = str(e)
            self.write({
                'l10n_sv_json_errors': error_msg,
                'l10n_sv_json_generated': False,
                'l10n_sv_json_dte_status': 'error'
            })
            raise exceptions.UserError(_(
                'Error al generar JSON DTE para envío: %s'
            ) % error_msg)