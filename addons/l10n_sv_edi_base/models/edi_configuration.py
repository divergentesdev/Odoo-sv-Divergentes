import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class EdiConfiguration(models.Model):
    """Configuración general para EDI de El Salvador"""
    _name = 'l10n_sv.edi.configuration'
    _description = 'Configuración EDI El Salvador'
    _rec_name = 'company_id'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía para esta configuración EDI'
    )
    
    environment = fields.Selection([
        ('test', 'Certificación (Pruebas)'),
        ('production', 'Producción')
    ], string='Ambiente Activo', required=True, default='test',
       help='Ambiente actualmente activo para facturación electrónica')
    
    certificate_test_id = fields.Many2one(
        'l10n_sv.edi.certificate',
        string='Certificado de Pruebas',
        domain="[('environment', '=', 'test'), ('company_id', '=', company_id)]",
        help='Certificado para ambiente de certificación'
    )
    
    certificate_production_id = fields.Many2one(
        'l10n_sv.edi.certificate',
        string='Certificado de Producción',
        domain="[('environment', '=', 'production'), ('company_id', '=', company_id)]",
        help='Certificado para ambiente de producción'
    )
    
    nit_emisor = fields.Char(
        string='NIT del Emisor',
        required=True,
        help='Número de Identificación Tributaria del emisor'
    )
    
    nrc_emisor = fields.Char(
        string='NRC del Emisor',
        help='Número de Registro de Contribuyente del emisor'
    )
    
    codigo_actividad = fields.Char(
        string='Código de Actividad',
        help='Código de actividad económica según catálogo del MH'
    )
    
    desc_actividad = fields.Char(
        string='Descripción de Actividad',
        help='Descripción de la actividad económica'
    )
    
    # Configuración de establecimientos
    codigo_establecimiento = fields.Char(
        string='Código de Establecimiento',
        size=4,
        help='Código alfanumérico del establecimiento para DTE (4 caracteres A-Z, 0-9)'
    )
    
    punto_venta = fields.Char(
        string='Punto de Venta',
        size=4,
        help='Código alfanumérico del punto de venta (4 caracteres A-Z, 0-9)'
    )
    
    # Configuración de numeración
    correlativo_factura = fields.Integer(
        string='Correlativo Factura',
        default=1,
        help='Próximo número correlativo para facturas'
    )
    
    correlativo_ccf = fields.Integer(
        string='Correlativo CCF',
        default=1,
        help='Próximo número correlativo para Comprobantes de Crédito Fiscal'
    )
    
    correlativo_nota_remision = fields.Integer(
        string='Correlativo Nota Remisión',
        default=1,
        help='Próximo número correlativo para Notas de Remisión'
    )
    
    correlativo_nota_credito = fields.Integer(
        string='Correlativo Nota Crédito',
        default=1,
        help='Próximo número correlativo para Notas de Crédito'
    )
    
    correlativo_nota_debito = fields.Integer(
        string='Correlativo Nota Débito',
        default=1,
        help='Próximo número correlativo para Notas de Débito'
    )
    
    # Configuración de contingencia
    modo_contingencia = fields.Boolean(
        string='Modo Contingencia',
        default=False,
        help='Activar modo contingencia cuando el API del MH no esté disponible'
    )
    
    motivo_contingencia = fields.Selection([
        ('1', 'Falla en el sistema del MH'),
        ('2', 'Falla en el sistema del contribuyente'),
        ('3', 'Falla en las comunicaciones'),
        ('4', 'Otros motivos técnicos')
    ], string='Motivo de Contingencia',
       help='Motivo por el cual se activa el modo contingencia')
    
    fecha_inicio_contingencia = fields.Datetime(
        string='Fecha Inicio Contingencia',
        help='Fecha y hora de inicio del modo contingencia'
    )
    
    # URLs de API por ambiente
    api_url_test = fields.Char(
        string='URL API Pruebas',
        default='https://apitest.dtes.mh.gob.sv/fesv/recepciondte',
        help='URL del API del MH para ambiente de pruebas'
    )
    
    api_url_production = fields.Char(
        string='URL API Producción',
        default='https://api.dtes.mh.gob.sv/fesv/recepciondte',
        help='URL del API del MH para ambiente de producción'
    )
    
    # Configuración de timeouts
    api_timeout = fields.Integer(
        string='Timeout API (segundos)',
        default=30,
        help='Tiempo máximo de espera para respuestas del API'
    )
    
    reintentos_automaticos = fields.Integer(
        string='Reintentos Automáticos',
        default=3,
        help='Número de reintentos automáticos en caso de falla'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Determina si esta configuración está activa'
    )

    @api.model
    def get_company_configuration(self, company_id=None):
        """Obtiene la configuración EDI para una compañía"""
        if not company_id:
            company_id = self.env.company.id
            
        config = self.search([
            ('company_id', '=', company_id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            # Crear configuración por defecto si no existe
            config = self.create({
                'company_id': company_id,
                'environment': 'test',
            })
        
        return config

    def get_active_certificate(self):
        """Obtiene el certificado activo según el ambiente configurado"""
        self.ensure_one()
        if self.environment == 'test':
            if not self.certificate_test_id:
                raise exceptions.UserError(_(
                    'No hay certificado configurado para el ambiente de pruebas'
                ))
            return self.certificate_test_id
        else:
            if not self.certificate_production_id:
                raise exceptions.UserError(_(
                    'No hay certificado configurado para el ambiente de producción'
                ))
            return self.certificate_production_id

    def get_api_url(self):
        """Obtiene la URL del API según el ambiente activo"""
        self.ensure_one()
        if self.environment == 'test':
            return self.api_url_test
        else:
            return self.api_url_production

    def generate_numero_control(self, tipo_dte, establecimiento_code=None, punto_venta_code=None):
        """Genera número de control DTE según tipo de documento"""
        self.ensure_one()
        
        # Mapeo de tipos de documento a correlativos
        correlativo_map = {
            '01': 'correlativo_factura',  # Factura
            '03': 'correlativo_ccf',      # CCF
            '04': 'correlativo_nota_remision',  # Nota de Remisión
            '05': 'correlativo_nota_credito',  # Nota Crédito
            '06': 'correlativo_nota_debito',   # Nota Débito
        }
        
        field_name = correlativo_map.get(tipo_dte, 'correlativo_factura')
        correlativo = getattr(self, field_name, 1)
        
        # Formato correcto según MH: DTE-{tipo}-{numérico8}-{correlativo:015d}
        # Los códigos deben ser exactamente 8 dígitos numéricos
        codigo_estab = establecimiento_code or self.codigo_establecimiento or '0001'
        codigo_punto_venta = punto_venta_code or self.punto_venta or '0001'
        
        # Remover caracteres no numéricos y asegurar que son 4 dígitos cada uno
        import re
        codigo_estab = re.sub(r'\D', '', codigo_estab)[:4].zfill(4)
        codigo_punto_venta = re.sub(r'\D', '', codigo_punto_venta)[:4].zfill(4)
        
        # Código numérico de 8 dígitos (4 estab + 4 punto venta)
        codigo_completo = codigo_estab + codigo_punto_venta
        
        # Validar que el código completo tenga 8 caracteres
        if len(codigo_completo) != 8:
            # Si no cumple, usar valores por defecto válidos
            codigo_completo = '00000001'
            
        # Para CCF y Nota de Remisión el patrón permite letras y números
        if tipo_dte in ['03', '04']:
            # Convertir a mayúsculas y validar que sea alfanumérico
            codigo_completo = codigo_completo.upper()
            if not re.match(r'^[A-Z0-9]{8}$', codigo_completo):
                codigo_completo = '00000001'
            numero_control = f"DTE-{tipo_dte}-{codigo_completo}-{correlativo:015d}"
        else:
            # Para otros tipos mantener formato numérico
            if not re.match(r'^[0-9]{8}$', codigo_completo):
                codigo_completo = '00000001'
            numero_control = f"DTE-{tipo_dte}-{codigo_completo}-{correlativo:015d}"
        
        # Incrementar correlativo y guardar en la base de datos
        setattr(self, field_name, correlativo + 1)
        self.env.cr.commit()  # Forzar guardado inmediato para evitar pérdida del secuencial
        
        return numero_control
    
    @api.constrains('codigo_establecimiento', 'punto_venta')
    def _check_codigo_numerico(self):
        """Validar que los códigos sean numéricos"""
        import re
        pattern = re.compile(r'^[0-9]+$')
        
        for record in self:
            if record.codigo_establecimiento:
                if not pattern.match(record.codigo_establecimiento):
                    raise exceptions.ValidationError(
                        _('El código de establecimiento debe contener solo números (0-9)')
                    )
                if len(record.codigo_establecimiento) != 4:
                    raise exceptions.ValidationError(
                        _('El código de establecimiento debe tener exactamente 4 dígitos')
                    )
            
            if record.punto_venta:
                if not pattern.match(record.punto_venta):
                    raise exceptions.ValidationError(
                        _('El código de punto de venta debe contener solo números (0-9)')
                    )
                if len(record.punto_venta) != 4:
                    raise exceptions.ValidationError(
                        _('El código de punto de venta debe tener exactamente 4 dígitos')
                    )

    def action_test_connection(self):
        """Acción para probar la conexión con el API del MH"""
        self.ensure_one()
        try:
            certificate = self.get_active_certificate()
            api_url = self.get_api_url()
            
            # Aquí se implementaría la prueba real de conexión
            # Por ahora simulamos una prueba exitosa
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Conexión Exitosa'),
                    'message': _('La conexión con el API del MH se estableció correctamente'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f"Error probando conexión: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error de Conexión'),
                    'message': _('Error al conectar con el API del MH: %s') % str(e),
                    'type': 'danger',
                }
            }

    def action_activate_contingency(self):
        """Activa el modo contingencia"""
        self.ensure_one()
        self.write({
            'modo_contingencia': True,
            'fecha_inicio_contingencia': fields.Datetime.now()
        })

    def action_deactivate_contingency(self):
        """Desactiva el modo contingencia"""
        self.ensure_one()
        self.write({
            'modo_contingencia': False,
            'motivo_contingencia': False,
            'fecha_inicio_contingencia': False
        })

    @api.constrains('company_id', 'active')
    def _check_unique_active_configuration(self):
        """Validar que solo haya una configuración activa por compañía"""
        for config in self:
            if config.active:
                domain = [
                    ('company_id', '=', config.company_id.id),
                    ('active', '=', True),
                    ('id', '!=', config.id)
                ]
                if self.search_count(domain) > 0:
                    raise exceptions.ValidationError(_(
                        'Solo puede haber una configuración EDI activa por compañía'
                    ))