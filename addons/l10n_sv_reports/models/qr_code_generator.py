import json
import logging
import base64
from io import BytesIO
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)

try:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    import barcode
    from barcode.writer import ImageWriter
except ImportError:
    _logger.warning("Librerías de códigos QR no disponibles. Instale: pip install qrcode Pillow python-barcode")


class L10nSvQrCodeGenerator(models.Model):
    """Generador de códigos QR para DTE El Salvador"""
    _name = 'l10n_sv.qr.code.generator'
    _description = 'Generador QR DTE El Salvador'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre descriptivo del generador QR'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía asociada a este generador'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    # Configuración QR
    qr_version = fields.Integer(
        string='Versión QR',
        default=1,
        help='Versión del código QR (1-40), determina el tamaño'
    )
    
    error_correction = fields.Selection([
        ('L', 'Bajo (7%)'),
        ('M', 'Medio (15%)'),
        ('Q', 'Cuartil (25%)'),
        ('H', 'Alto (30%)')
    ], string='Corrección de Error', default='M',
       help='Nivel de corrección de errores del QR')
    
    box_size = fields.Integer(
        string='Tamaño de Caja',
        default=10,
        help='Píxeles por cada caja del QR'
    )
    
    border = fields.Integer(
        string='Borde',
        default=4,
        help='Tamaño del borde en cajas'
    )
    
    # Colores
    fill_color = fields.Char(
        string='Color de Relleno',
        default='black',
        help='Color de los módulos del QR'
    )
    
    back_color = fields.Char(
        string='Color de Fondo',
        default='white',
        help='Color de fondo del QR'
    )
    
    # Configuración de datos
    include_url = fields.Boolean(
        string='Incluir URL de Consulta',
        default=True,
        help='Incluir URL para consulta en línea'
    )
    
    include_signature_info = fields.Boolean(
        string='Incluir Info de Firma',
        default=True,
        help='Incluir información de firma digital'
    )
    
    include_mh_response = fields.Boolean(
        string='Incluir Respuesta MH',
        default=True,
        help='Incluir información de respuesta del MH'
    )
    
    base_url = fields.Char(
        string='URL Base',
        default='https://dte.gob.sv/verify',
        help='URL base para consultas DTE'
    )
    
    verification_url = fields.Char(
        string='URL de Verificación',
        default='https://dte.gob.sv/api/verify',
        help='URL de la API de verificación'
    )
    
    url_template = fields.Char(
        string='Plantilla de URL',
        default='https://consultas.mh.gob.sv/dte/{numero_control}',
        help='Plantilla para URL de consulta'
    )
    
    # Configuración de logo
    logo_size_ratio = fields.Float(
        string='Proporción del Logo',
        default=0.2,
        help='Proporción del logo respecto al QR (0.1 = 10%)'
    )
    
    logo_border_size = fields.Integer(
        string='Borde del Logo',
        default=10,
        help='Tamaño del borde alrededor del logo en píxeles'
    )
    
    # Plantilla personalizada de datos
    custom_data_template = fields.Text(
        string='Plantilla de Datos Personalizada',
        help='Plantilla Python para generar datos personalizados del QR'
    )
    
    # Formato de datos
    data_format = fields.Selection([
        ('json', 'JSON Compacto'),
        ('url', 'Solo URL'),
        ('mixed', 'Mixto (URL + Datos)')
    ], string='Formato de Datos', default='mixed',
       help='Formato de datos incluidos en el QR')
    
    max_data_length = fields.Integer(
        string='Longitud Máxima de Datos',
        default=2000,
        help='Longitud máxima de datos en el QR'
    )
    
    # Estadísticas
    total_generated = fields.Integer(
        string='Total Generados',
        readonly=True,
        default=0,
        help='Número total de QR generados'
    )
    
    last_generation_date = fields.Datetime(
        string='Última Generación',
        readonly=True,
        help='Fecha de última generación de QR'
    )

    @api.constrains('qr_version')
    def _check_qr_version(self):
        """Valida versión de QR"""
        for generator in self:
            if not 1 <= generator.qr_version <= 40:
                raise exceptions.ValidationError(_(
                    'La versión QR debe estar entre 1 y 40'
                ))

    @api.constrains('box_size', 'border')
    def _check_sizes(self):
        """Valida tamaños"""
        for generator in self:
            if generator.box_size < 1:
                raise exceptions.ValidationError(_('Tamaño de caja debe ser al menos 1'))
            if generator.border < 0:
                raise exceptions.ValidationError(_('Borde no puede ser negativo'))

    def generate_qr_code(self, move_id):
        """Genera código QR para una factura DTE"""
        self.ensure_one()
        
        try:
            move = self.env['account.move'].browse(move_id)
            if not move.exists():
                raise exceptions.UserError(_('Factura no encontrada'))
            
            # Preparar datos para QR
            qr_data = self._prepare_qr_data(move)
            
            # Crear QR code
            qr = qrcode.QRCode(
                version=self.qr_version,
                error_correction=getattr(qrcode.constants, f'ERROR_CORRECT_{self.error_correction}'),
                box_size=self.box_size,
                border=self.border,
            )
            
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Crear imagen
            img = qr.make_image(
                fill_color=self.fill_color,
                back_color=self.back_color
            )
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Actualizar estadísticas
            self.total_generated += 1
            self.last_generation_date = fields.Datetime.now()
            
            return {
                'success': True,
                'qr_code': qr_base64,
                'qr_data': qr_data,
                'format': 'PNG',
                'size': len(buffer.getvalue())
            }
            
        except Exception as e:
            _logger.error(f'Error generando QR para factura {move_id}: {str(e)}')
            raise exceptions.UserError(_(
                'Error generando código QR: %s'
            ) % str(e))

    def _prepare_qr_data(self, move):
        """Prepara datos para incluir en el QR"""
        self.ensure_one()
        
        if self.data_format == 'url':
            return self._get_consultation_url(move)
        elif self.data_format == 'json':
            return self._get_json_data(move)
        else:  # mixed
            return self._get_mixed_data(move)

    def _get_consultation_url(self, move):
        """Obtiene URL de consulta del DTE"""
        if not self.url_template:
            return f"https://consultas.mh.gob.sv/dte/{move.l10n_sv_edi_numero_control or 'DRAFT'}"
        
        return self.url_template.format(
            numero_control=move.l10n_sv_edi_numero_control or 'DRAFT',
            codigo_generacion=move.l10n_sv_edi_codigo_generacion or '',
            nit_emisor=move.company_id.l10n_sv_nit or move.company_id.vat or '',
            total=move.amount_total
        )

    def _get_json_data(self, move):
        """Obtiene datos en formato JSON compacto"""
        data = {
            'nc': move.l10n_sv_edi_numero_control,  # Número Control
            'cg': move.l10n_sv_edi_codigo_generacion,  # Código Generación
            'td': move.l10n_sv_document_type_id.code if move.l10n_sv_document_type_id else '',  # Tipo Documento
            'fe': move.invoice_date.strftime('%Y-%m-%d') if move.invoice_date else '',  # Fecha Emisión
            'ne': move.company_id.l10n_sv_nit or move.company_id.vat or '',  # NIT Emisor
            'nr': move.partner_id.vat or '',  # NIT Receptor
            'mt': float(move.amount_total),  # Monto Total
        }
        
        # Agregar información de firma si está disponible y configurado
        if self.include_signature_info and move.l10n_sv_signature_status == 'signed':
            data['fs'] = move.l10n_sv_signature_status  # Firma Status
            data['fa'] = move.l10n_sv_signature_algorithm  # Firma Algoritmo
            data['ff'] = move.l10n_sv_signature_date.strftime('%Y-%m-%d %H:%M:%S') if move.l10n_sv_signature_date else ''  # Firma Fecha
        
        # Agregar información del MH si está disponible y configurado
        if self.include_mh_response and move.l10n_sv_mh_status not in ['draft', 'ready']:
            data['ms'] = move.l10n_sv_mh_status  # MH Status
            data['mf'] = move.l10n_sv_mh_send_date.strftime('%Y-%m-%d %H:%M:%S') if move.l10n_sv_mh_send_date else ''  # MH Fecha
            if move.l10n_sv_mh_sello:
                data['se'] = move.l10n_sv_mh_sello[:50]  # Sello (truncado)
        
        json_str = json.dumps(data, separators=(',', ':'))
        
        # Verificar longitud máxima
        if len(json_str) > self.max_data_length:
            # Crear versión reducida
            reduced_data = {
                'nc': data['nc'],
                'td': data['td'],
                'mt': data['mt'],
                'url': self._get_consultation_url(move)
            }
            json_str = json.dumps(reduced_data, separators=(',', ':'))
        
        return json_str

    def _get_mixed_data(self, move):
        """Obtiene datos mixtos (URL + información básica)"""
        url = self._get_consultation_url(move)
        
        basic_info = []
        basic_info.append(f"NC:{move.l10n_sv_edi_numero_control or 'DRAFT'}")
        basic_info.append(f"TOTAL:{move.amount_total}")
        
        if move.l10n_sv_signature_status == 'signed':
            basic_info.append("FIRMADO:SI")
        
        if move.l10n_sv_mh_status == 'approved':
            basic_info.append("APROBADO:SI")
        
        data = url + "|" + "|".join(basic_info)
        
        # Verificar longitud máxima
        if len(data) > self.max_data_length:
            return url  # Solo URL si es muy largo
        
        return data

    def generate_barcode(self, move_id, barcode_type='code128'):
        """Genera código de barras adicional"""
        self.ensure_one()
        
        try:
            move = self.env['account.move'].browse(move_id)
            if not move.exists():
                raise exceptions.UserError(_('Factura no encontrada'))
            
            # Datos para código de barras
            if barcode_type == 'code128':
                barcode_data = move.l10n_sv_edi_numero_control or move.name
            elif barcode_type == 'ean13':
                # Generar EAN13 a partir del número de control
                control_num = move.l10n_sv_edi_numero_control or '000000000000'
                # Extraer solo números y ajustar a 12 dígitos
                numbers = ''.join(filter(str.isdigit, control_num))
                if len(numbers) >= 12:
                    barcode_data = numbers[:12]
                else:
                    barcode_data = numbers.ljust(12, '0')
            else:
                raise exceptions.UserError(_('Tipo de código de barras no soportado'))
            
            # Generar código de barras
            code_class = barcode.get_barcode_class(barcode_type)
            code_instance = code_class(barcode_data, writer=ImageWriter())
            
            # Renderizar a imagen
            buffer = BytesIO()
            code_instance.write(buffer)
            barcode_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'success': True,
                'barcode': barcode_base64,
                'data': barcode_data,
                'type': barcode_type,
                'format': 'PNG'
            }
            
        except Exception as e:
            _logger.error(f'Error generando código de barras para factura {move_id}: {str(e)}')
            raise exceptions.UserError(_(
                'Error generando código de barras: %s'
            ) % str(e))

    def action_generate_test_qr(self):
        """Acción para generar QR de prueba"""
        return self.action_test_qr_generation()

    def action_test_qr_generation(self):
        """Acción para probar generación de QR"""
        self.ensure_one()
        
        # Buscar una factura de prueba
        test_move = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not test_move:
            raise exceptions.UserError(_(
                'No se encontró factura de prueba. Cree una factura validada primero.'
            ))
        
        try:
            result = self.generate_qr_code(test_move.id)
            
            if result['success']:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('QR Generado Exitosamente'),
                        'message': _('El código QR se generó correctamente para la factura %s') % test_move.name,
                        'type': 'success'
                    }
                }
            else:
                raise exceptions.UserError(_('Fallo en generación de QR'))
                
        except Exception as e:
            raise exceptions.UserError(_(
                'Error en prueba de QR: %s'
            ) % str(e))

    @api.model
    def get_default_qr_generator(self, company_id=None):
        """Obtiene generador QR por defecto para la compañía"""
        if not company_id:
            company_id = self.env.company.id
        
        generator = self.search([
            ('company_id', '=', company_id),
            ('active', '=', True)
        ], limit=1)
        
        if not generator:
            # Crear generador por defecto
            generator = self.create({
                'name': 'Generador QR - Principal',
                'company_id': company_id,
                'qr_version': 1,
                'error_correction': 'M',
                'data_format': 'mixed'
            })
        
        return generator

    def generate_qr_with_logo(self, move_id, logo_data=None):
        """Genera QR con logo de empresa en el centro"""
        self.ensure_one()
        
        try:
            # Generar QR básico
            result = self.generate_qr_code(move_id)
            
            if not result['success']:
                return result
            
            # Si no hay logo, retornar QR normal
            if not logo_data:
                move = self.env['account.move'].browse(move_id)
                if move.company_id.logo:
                    logo_data = move.company_id.logo
                else:
                    return result
            
            # Cargar imagen QR
            qr_image_data = base64.b64decode(result['qr_code'])
            qr_img = Image.open(BytesIO(qr_image_data))
            
            # Cargar logo
            logo_image_data = base64.b64decode(logo_data)
            logo_img = Image.open(BytesIO(logo_image_data))
            
            # Redimensionar logo (máximo 20% del QR)
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 5
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Crear máscara circular para el logo
            mask = Image.new('L', (logo_size, logo_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo_size, logo_size), fill=255)
            
            # Aplicar máscara al logo
            logo_img.putalpha(mask)
            
            # Crear fondo blanco para el logo
            background = Image.new('RGBA', (logo_size + 20, logo_size + 20), (255, 255, 255, 255))
            bg_pos = ((background.size[0] - logo_size) // 2, (background.size[1] - logo_size) // 2)
            background.paste(logo_img, bg_pos, logo_img)
            
            # Pegar logo en el centro del QR
            qr_img = qr_img.convert('RGBA')
            logo_pos = ((qr_width - background.size[0]) // 2, (qr_height - background.size[1]) // 2)
            qr_img.paste(background, logo_pos, background)
            
            # Convertir de vuelta a base64
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_with_logo = base64.b64encode(buffer.getvalue()).decode()
            
            result['qr_code'] = qr_with_logo
            result['has_logo'] = True
            
            return result
            
        except Exception as e:
            _logger.error(f'Error generando QR con logo: {str(e)}')
            # Retornar QR sin logo en caso de error
            return self.generate_qr_code(move_id)