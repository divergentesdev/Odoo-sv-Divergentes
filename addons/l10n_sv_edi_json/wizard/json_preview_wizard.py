import json
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class JsonPreviewWizard(models.TransientModel):
    """Wizard para previsualizar y validar JSON DTE"""
    _name = 'l10n_sv.json.preview.wizard'
    _description = 'Wizard Vista Previa JSON DTE'

    move_id = fields.Many2one(
        'account.move',
        string='Factura',
        readonly=True,
        required=False,
        help='Factura relacionada (solo para DTEs)'
    )
    
    contingency_id = fields.Many2one(
        'l10n_sv.contingency',
        string='Contingencia',
        readonly=True,
        help='Contingencia relacionada (solo para reportes de contingencia)'
    )
    
    document_type_id = fields.Many2one(
        'l10n_sv.document.type',  # Usar el tipo de documento correcto
        string='Tipo de Documento',
        related='move_id.l10n_sv_document_type_id',
        readonly=True,
        required=False
    )
    
    numero_control = fields.Char(
        string='Número de Control',
        related='move_id.l10n_sv_edi_numero_control',
        readonly=True,
        required=False
    )
    
    json_content = fields.Text(
        string='JSON DTE',
        required=True,
        help='Contenido del JSON DTE para previsualización'
    )
    
    json_formatted = fields.Html(
        string='JSON Formateado',
        compute='_compute_json_formatted',
        help='JSON formateado con sintaxis highlighting para mejor lectura'
    )
    
    is_valid = fields.Boolean(
        string='JSON Válido',
        compute='_compute_validation_status',
        help='Indica si el JSON es válido según las especificaciones MH'
    )
    
    validation_errors = fields.Text(
        string='Errores de Validación',
        compute='_compute_validation_status',
        help='Lista de errores encontrados durante la validación'
    )
    
    json_size = fields.Integer(
        string='Tamaño JSON (bytes)',
        compute='_compute_json_stats',
        help='Tamaño del JSON en bytes'
    )
    
    json_lines = fields.Integer(
        string='Líneas JSON',
        compute='_compute_json_stats',
        help='Número de líneas del JSON'
    )

    @api.depends('json_content')
    def _compute_json_formatted(self):
        """Computa JSON formateado para visualización"""
        for wizard in self:
            if wizard.json_content:
                try:
                    # Parsear y reformatear JSON
                    json_data = json.loads(wizard.json_content)
                    formatted = json.dumps(json_data, ensure_ascii=False, indent=2, separators=(',', ': '))
                    
                    # Convertir a HTML con colores básicos
                    html_content = f"""
                    <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.4; overflow: auto; max-height: 600px;">
{self._format_json_html(formatted)}
                    </pre>
                    """
                    wizard.json_formatted = html_content
                except json.JSONDecodeError:
                    wizard.json_formatted = f"""
                    <div style="color: red; padding: 10px; border: 1px solid red; border-radius: 5px;">
                        <strong>Error:</strong> JSON inválido - No se puede parsear el contenido
                    </div>
                    """
            else:
                wizard.json_formatted = '<p>No hay contenido JSON para mostrar</p>'

    @api.depends('json_content', 'move_id')
    def _compute_validation_status(self):
        """Computa estado de validación del JSON"""
        for wizard in self:
            wizard.is_valid = False
            wizard.validation_errors = ''
            
            if not wizard.json_content:
                wizard.validation_errors = 'No hay contenido JSON para validar'
                continue
            
            try:
                # Parsear JSON
                json_data = json.loads(wizard.json_content)
                
                # Lógica específica para contingencias
                if wizard.contingency_id:
                    # Validación básica de contingencia
                    required_fields = ['identificacion', 'emisor', 'detalleDTE', 'motivo']
                    missing_fields = [field for field in required_fields if field not in json_data]
                    
                    if missing_fields:
                        wizard.validation_errors = f'Campos requeridos faltantes: {", ".join(missing_fields)}'
                        wizard.is_valid = False
                    else:
                        wizard.is_valid = True
                        wizard.validation_errors = 'JSON de contingencia válido'
                
                # Lógica original para DTEs (facturas)
                elif wizard.move_id and wizard.document_type_id:
                    # Usar el tipo de documento para encontrar el generador
                    document_type = wizard.document_type_id
                    
                    if document_type:
                        # Buscar generador asociado al tipo de documento
                        generator = wizard.env['l10n_sv.json.generator'].search([
                            ('document_type_id', '=', document_type.id),
                            ('active', '=', True)
                        ], limit=1)
                        
                        if generator:
                            # Validar con el generador
                            try:
                                generator.validate_json(json_data, wizard.move_id)
                                wizard.is_valid = True
                                wizard.validation_errors = 'JSON DTE válido'
                            except Exception as e:
                                wizard.validation_errors = str(e)
                                wizard.is_valid = False
                        else:
                            wizard.validation_errors = f'No se encontró generador para el tipo de documento {document_type.name}'
                    else:
                        wizard.validation_errors = 'No se encontró tipo de documento para validación'
                
                else:
                    wizard.validation_errors = 'No se pudo determinar el tipo de documento para validación'
                    wizard.is_valid = False
                    
            except json.JSONDecodeError as e:
                wizard.validation_errors = f'JSON inválido: {str(e)}'
            except Exception as e:
                wizard.validation_errors = f'Error durante validación: {str(e)}'

    @api.depends('json_content')
    def _compute_json_stats(self):
        """Computa estadísticas del JSON"""
        for wizard in self:
            if wizard.json_content:
                wizard.json_size = len(wizard.json_content.encode('utf-8'))
                wizard.json_lines = len(wizard.json_content.splitlines())
            else:
                wizard.json_size = 0
                wizard.json_lines = 0

    def _format_json_html(self, json_str):
        """Formatea JSON con colores básicos HTML"""
        import re
        
        # Escapar HTML
        json_str = json_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Colorear strings (texto entre comillas)
        json_str = re.sub(r'"([^"]*)":', r'<span style="color: #0066cc; font-weight: bold;">"&"\1"</span>:', json_str)
        json_str = re.sub(r': "([^"]*)"', r': <span style="color: #cc6600;">"&"\1"</span>', json_str)
        
        # Colorear números
        json_str = re.sub(r': (\d+\.?\d*)', r': <span style="color: #990099;">&"\1"</span>', json_str)
        
        # Colorear null, true, false
        json_str = re.sub(r': (null|true|false)', r': <span style="color: #009900; font-weight: bold;">&"\1"</span>', json_str)
        
        return json_str

    def action_download_json(self):
        """Acción para descargar JSON como archivo"""
        self.ensure_one()
        
        if not self.json_content:
            raise exceptions.UserError(_('No hay contenido JSON para descargar'))
        
        # Generar nombre de archivo
        doc_code = self.document_type_id.code if self.document_type_id else 'DRAFT'
        filename = f"DTE_{doc_code}_{self.numero_control or 'DRAFT'}.json"
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=json_content&filename_field=filename&download=true',
            'target': 'self'
        }

    def action_validate_json(self):
        """Acción para validar JSON manualmente"""
        self.ensure_one()
        self._compute_validation_status()
        
        if self.is_valid:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Validación Exitosa'),
                    'message': _('El JSON DTE es válido según las especificaciones del MH'),
                    'type': 'success'
                }
            }
        else:
            raise exceptions.UserError(_(
                'JSON DTE inválido:\n%s'
            ) % (self.validation_errors or 'Errores de validación desconocidos'))

    def action_regenerate_json(self):
        """Acción para regenerar JSON desde la factura"""
        self.ensure_one()
        
        if not self.move_id:
            raise exceptions.UserError(_('No hay factura asociada para regenerar JSON'))
        
        try:
            # Regenerar JSON en la factura
            self.move_id.action_regenerate_json_dte()
            
            # Actualizar contenido del wizard
            self.json_content = self.move_id.l10n_sv_json_dte
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('JSON Regenerado'),
                    'message': _('El JSON DTE se ha regenerado correctamente'),
                    'type': 'success'
                }
            }
            
        except Exception as e:
            raise exceptions.UserError(_(
                'Error al regenerar JSON DTE:\n%s'
            ) % str(e))

    def action_copy_to_clipboard(self):
        """Acción para copiar JSON al portapapeles (JavaScript)"""
        self.ensure_one()
        
        if not self.json_content:
            raise exceptions.UserError(_('No hay contenido JSON para copiar'))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'copy_to_clipboard',
            'params': {
                'content': self.json_content,
                'message': _('JSON DTE copiado al portapapeles')
            }
        }

    def action_compare_with_template(self):
        """Acción para comparar JSON con plantilla base"""
        self.ensure_one()
        
        # Esta funcionalidad podría implementarse en una versión futura
        # para comparar el JSON generado con plantillas de referencia
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Funcionalidad en Desarrollo'),
                'message': _('La comparación con plantillas estará disponible en una versión futura'),
                'type': 'info'
            }
        }