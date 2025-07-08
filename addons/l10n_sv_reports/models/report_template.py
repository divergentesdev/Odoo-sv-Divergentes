import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class L10nSvReportTemplate(models.Model):
    """Plantillas de reportes DTE personalizables"""
    _name = 'l10n_sv.report.template'
    _description = 'Plantillas de Reportes DTE'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre de la plantilla de reporte'
    )
    
    code = fields.Char(
        string='Código',
        required=True,
        help='Código único de la plantilla'
    )
    
    document_type_id = fields.Many2one(
        'l10n_sv.document.type',
        string='Tipo de Documento',
        required=True,
        help='Tipo de documento DTE para esta plantilla'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía que usa esta plantilla'
    )
    
    active = fields.Boolean(
        string='Activa',
        default=True
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción de la plantilla'
    )
    
    # Configuración de diseño
    paper_format = fields.Selection([
        ('A4', 'A4 (210 x 297 mm)'),
        ('Letter', 'Carta (216 x 279 mm)'),
        ('Legal', 'Legal (216 x 356 mm)'),
        ('A5', 'A5 (148 x 210 mm)')
    ], string='Formato de Papel', default='A4',
       help='Formato de papel para el reporte')
    
    orientation = fields.Selection([
        ('portrait', 'Vertical'),
        ('landscape', 'Horizontal')
    ], string='Orientación', default='portrait',
       help='Orientación del papel')
    
    margin_top = fields.Float(
        string='Margen Superior (mm)',
        default=20.0,
        help='Margen superior en milímetros'
    )
    
    margin_bottom = fields.Float(
        string='Margen Inferior (mm)',
        default=20.0,
        help='Margen inferior en milímetros'
    )
    
    margin_left = fields.Float(
        string='Margen Izquierdo (mm)',
        default=15.0,
        help='Margen izquierdo en milímetros'
    )
    
    margin_right = fields.Float(
        string='Margen Derecho (mm)',
        default=15.0,
        help='Margen derecho en milímetros'
    )
    
    # Configuración de header
    show_header = fields.Boolean(
        string='Mostrar Encabezado',
        default=True,
        help='Mostrar encabezado en el reporte'
    )
    
    header_height = fields.Float(
        string='Altura Encabezado (mm)',
        default=60.0,
        help='Altura del encabezado en milímetros'
    )
    
    show_company_logo = fields.Boolean(
        string='Mostrar Logo Empresa',
        default=True,
        help='Mostrar logo de la empresa'
    )
    
    logo_position = fields.Selection([
        ('left', 'Izquierda'),
        ('center', 'Centro'),
        ('right', 'Derecha')
    ], string='Posición Logo', default='left',
       help='Posición del logo en el encabezado')
    
    logo_width = fields.Float(
        string='Ancho Logo (mm)',
        default=40.0,
        help='Ancho del logo en milímetros'
    )
    
    logo_height = fields.Float(
        string='Alto Logo (mm)',
        default=30.0,
        help='Alto del logo en milímetros'
    )
    
    # Configuración de footer
    show_footer = fields.Boolean(
        string='Mostrar Pie de Página',
        default=True,
        help='Mostrar pie de página en el reporte'
    )
    
    footer_height = fields.Float(
        string='Altura Pie (mm)',
        default=40.0,
        help='Altura del pie de página en milímetros'
    )
    
    footer_text = fields.Text(
        string='Texto Pie de Página',
        help='Texto personalizado para pie de página'
    )
    
    # Configuración de QR
    show_qr_code = fields.Boolean(
        string='Mostrar Código QR',
        default=True,
        help='Mostrar código QR en el reporte'
    )
    
    qr_position = fields.Selection([
        ('header_right', 'Encabezado Derecha'),
        ('footer_left', 'Pie Izquierda'),
        ('footer_right', 'Pie Derecha'),
        ('body_right', 'Cuerpo Derecha')
    ], string='Posición QR', default='footer_right',
       help='Posición del código QR')
    
    qr_size = fields.Float(
        string='Tamaño QR (mm)',
        default=25.0,
        help='Tamaño del código QR en milímetros'
    )
    
    qr_generator_id = fields.Many2one(
        'l10n_sv.qr.code.generator',
        string='Generador QR',
        help='Generador QR a utilizar'
    )
    
    # Configuración de barcode
    show_barcode = fields.Boolean(
        string='Mostrar Código de Barras',
        default=False,
        help='Mostrar código de barras adicional'
    )
    
    barcode_type = fields.Selection([
        ('code128', 'Code 128'),
        ('ean13', 'EAN-13'),
        ('code39', 'Code 39')
    ], string='Tipo de Código de Barras', default='code128',
       help='Tipo de código de barras')
    
    barcode_position = fields.Selection([
        ('header', 'Encabezado'),
        ('footer', 'Pie de Página')
    ], string='Posición Código de Barras', default='footer',
       help='Posición del código de barras')
    
    # Información DTE
    show_dte_info = fields.Boolean(
        string='Mostrar Info DTE',
        default=True,
        help='Mostrar información específica de DTE'
    )
    
    show_signature_info = fields.Boolean(
        string='Mostrar Info Firma',
        default=True,
        help='Mostrar información de firma digital'
    )
    
    show_mh_info = fields.Boolean(
        string='Mostrar Info MH',
        default=True,
        help='Mostrar información del Ministerio de Hacienda'
    )
    
    # Marcas de agua
    show_watermark = fields.Boolean(
        string='Mostrar Marca de Agua',
        default=True,
        help='Mostrar marca de agua según estado'
    )
    
    watermark_draft = fields.Char(
        string='Marca Borrador',
        default='BORRADOR',
        help='Texto para documentos en borrador'
    )
    
    watermark_cancelled = fields.Char(
        string='Marca Cancelado',
        default='CANCELADO',
        help='Texto para documentos cancelados'
    )
    
    watermark_opacity = fields.Float(
        string='Opacidad Marca (%)',
        default=15.0,
        help='Opacidad de la marca de agua (0-100)'
    )
    
    # Colores y estilos
    primary_color = fields.Char(
        string='Color Primario',
        default='#1f2937',
        help='Color primario del reporte (hexadecimal)'
    )
    
    secondary_color = fields.Char(
        string='Color Secundario',
        default='#6b7280',
        help='Color secundario del reporte (hexadecimal)'
    )
    
    accent_color = fields.Char(
        string='Color de Acento',
        default='#3b82f6',
        help='Color de acento del reporte (hexadecimal)'
    )
    
    font_size_normal = fields.Float(
        string='Tamaño Fuente Normal',
        default=10.0,
        help='Tamaño de fuente normal en puntos'
    )
    
    font_size_small = fields.Float(
        string='Tamaño Fuente Pequeña',
        default=8.0,
        help='Tamaño de fuente pequeña en puntos'
    )
    
    font_size_large = fields.Float(
        string='Tamaño Fuente Grande',
        default=12.0,
        help='Tamaño de fuente grande en puntos'
    )
    
    # Configuración de tabla
    table_border_color = fields.Char(
        string='Color Borde Tabla',
        default='#e5e7eb',
        help='Color de bordes de tabla (hexadecimal)'
    )
    
    table_header_color = fields.Char(
        string='Color Encabezado Tabla',
        default='#f9fafb',
        help='Color de fondo de encabezados de tabla'
    )
    
    table_row_alternate = fields.Boolean(
        string='Filas Alternadas',
        default=True,
        help='Alternar colores de filas en tablas'
    )
    
    table_row_color = fields.Char(
        string='Color Fila Alternada',
        default='#f8fafc',
        help='Color de filas alternadas'
    )
    
    # CSS personalizado y texto de marca de agua
    custom_css = fields.Text(
        string='CSS Personalizado',
        help='CSS adicional para personalizar el reporte'
    )
    
    watermark_text = fields.Char(
        string='Texto de Marca de Agua',
        help='Texto personalizado para marca de agua'
    )
    
    # Campo de fuente unificado (por compatibilidad con vista)
    font_family = fields.Selection([
        ('helvetica', 'Helvetica'),
        ('arial', 'Arial'),
        ('times', 'Times New Roman'),
        ('courier', 'Courier New')
    ], string='Familia de Fuente', default='helvetica',
       help='Familia de fuente para el reporte')
    
    font_size = fields.Float(
        string='Tamaño de Fuente',
        default=10.0,
        help='Tamaño de fuente principal en puntos'
    )

    @api.constrains('code')
    def _check_unique_code(self):
        """Asegura que el código sea único por compañía"""
        for template in self:
            if self.search_count([
                ('code', '=', template.code),
                ('company_id', '=', template.company_id.id),
                ('id', '!=', template.id)
            ]) > 0:
                raise exceptions.ValidationError(_(
                    'Ya existe una plantilla con el código %s en esta compañía'
                ) % template.code)

    @api.constrains('margin_top', 'margin_bottom', 'margin_left', 'margin_right')
    def _check_margins(self):
        """Valida márgenes"""
        for template in self:
            if any(margin < 0 for margin in [template.margin_top, template.margin_bottom, 
                                           template.margin_left, template.margin_right]):
                raise exceptions.ValidationError(_('Los márgenes no pueden ser negativos'))

    @api.constrains('watermark_opacity')
    def _check_watermark_opacity(self):
        """Valida opacidad de marca de agua"""
        for template in self:
            if not 0 <= template.watermark_opacity <= 100:
                raise exceptions.ValidationError(_(
                    'La opacidad debe estar entre 0 y 100'
                ))

    def get_template_css(self):
        """Genera CSS personalizado para la plantilla"""
        self.ensure_one()
        
        css = f"""
        <style>
            .report-template {{
                font-family: {self.font_family}, sans-serif;
                font-size: {self.font_size_normal}pt;
                color: {self.primary_color};
            }}
            
            .report-header {{
                height: {self.header_height}mm;
                margin-bottom: 10mm;
            }}
            
            .report-footer {{
                height: {self.footer_height}mm;
                margin-top: 10mm;
            }}
            
            .report-logo {{
                width: {self.logo_width}mm;
                height: {self.logo_height}mm;
                float: {self.logo_position};
            }}
            
            .report-qr {{
                width: {self.qr_size}mm;
                height: {self.qr_size}mm;
            }}
            
            .font-small {{ font-size: {self.font_size_small}pt; }}
            .font-normal {{ font-size: {self.font_size_normal}pt; }}
            .font-large {{ font-size: {self.font_size_large}pt; }}
            
            .color-primary {{ color: {self.primary_color}; }}
            .color-secondary {{ color: {self.secondary_color}; }}
            .color-accent {{ color: {self.accent_color}; }}
            
            .table-dte {{
                width: 100%;
                border-collapse: collapse;
                border: 1px solid {self.table_border_color};
            }}
            
            .table-dte th {{
                background-color: {self.table_header_color};
                border: 1px solid {self.table_border_color};
                padding: 5px;
                text-align: left;
            }}
            
            .table-dte td {{
                border: 1px solid {self.table_border_color};
                padding: 5px;
            }}
        """
        
        if self.table_row_alternate:
            css += f"""
            .table-dte tr:nth-child(even) {{
                background-color: {self.table_row_color};
            }}
            """
        
        if self.show_watermark:
            css += f"""
            .watermark {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 72pt;
                font-weight: bold;
                opacity: {self.watermark_opacity / 100};
                z-index: -1;
                color: {self.secondary_color};
            }}
            """
        
        css += "</style>"
        return css

    def get_watermark_text(self, move):
        """Obtiene texto de marca de agua según estado del documento"""
        self.ensure_one()
        
        if not self.show_watermark:
            return ''
        
        if move.state == 'draft':
            return self.watermark_draft
        elif move.state == 'cancel':
            return self.watermark_cancelled
        elif move.l10n_sv_mh_status == 'rejected':
            return 'RECHAZADO'
        elif move.l10n_sv_mh_status == 'error':
            return 'ERROR'
        
        return ''

    @api.model
    def get_template_for_document(self, document_type_id, company_id=None):
        """Obtiene plantilla para tipo de documento"""
        if not company_id:
            company_id = self.env.company.id
        
        template = self.search([
            ('document_type_id', '=', document_type_id),
            ('company_id', '=', company_id),
            ('active', '=', True)
        ], limit=1)
        
        if not template:
            # Buscar plantilla genérica
            template = self.search([
                ('code', '=', 'default'),
                ('company_id', '=', company_id),
                ('active', '=', True)
            ], limit=1)
        
        if not template:
            # Crear plantilla por defecto
            document_type = self.env['l10n_sv.document.type'].browse(document_type_id)
            template = self.create({
                'name': f'Plantilla {document_type.name}',
                'code': f'template_{document_type.code}',
                'document_type_id': document_type_id,
                'company_id': company_id
            })
        
        return template

    def action_preview_template(self):
        """Acción para previsualizar plantilla"""
        self.ensure_one()
        
        # Buscar factura de ejemplo
        sample_move = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('l10n_sv_document_type_id', '=', self.document_type_id.id),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not sample_move:
            sample_move = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
        
        if not sample_move:
            raise exceptions.UserError(_(
                'No se encontró factura de ejemplo para previsualizar'
            ))
        
        return {
            'type': 'ir.actions.report',
            'report_name': 'l10n_sv_reports.invoice_dte_report',
            'report_type': 'qweb-pdf',
            'data': {'template_id': self.id},
            'context': {'active_id': sample_move.id}
        }

    def action_duplicate_template(self):
        """Acción para duplicar plantilla"""
        self.ensure_one()
        
        # Crear copia de la plantilla
        new_template = self.copy({
            'name': f'{self.name} (Copia)',
            'code': f'{self.code}_copy_{fields.Datetime.now().strftime("%Y%m%d_%H%M%S")}'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Plantilla Duplicada'),
            'res_model': 'l10n_sv.report.template',
            'res_id': new_template.id,
            'view_mode': 'form',
            'target': 'current'
        }