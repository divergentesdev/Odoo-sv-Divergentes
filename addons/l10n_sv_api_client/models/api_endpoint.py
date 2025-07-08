import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class L10nSvApiEndpoint(models.Model):
    """Configuración de endpoints de API del MH"""
    _name = 'l10n_sv.api.endpoint'
    _description = 'Endpoints API MH El Salvador'
    _order = 'environment, endpoint_type'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre descriptivo del endpoint'
    )
    
    environment = fields.Selection([
        ('test', 'Certificación'),
        ('production', 'Producción')
    ], string='Ambiente', required=True,
       help='Ambiente del MH')
    
    endpoint_type = fields.Selection([
        ('auth', 'Autenticación'),
        ('send', 'Envío DTE'),
        ('query', 'Consulta Estado'),
        ('contingency', 'Contingencia'),
        ('cancel', 'Anulación'),
        ('other', 'Otro')
    ], string='Tipo de Endpoint', required=True)
    
    url = fields.Char(
        string='URL',
        required=True,
        help='URL completa del endpoint'
    )
    
    method = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE')
    ], string='Método HTTP', required=True, default='POST')
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción del propósito del endpoint'
    )
    
    # Configuración adicional
    timeout = fields.Integer(
        string='Timeout (segundos)',
        default=30,
        help='Tiempo límite para este endpoint específico'
    )
    
    requires_auth = fields.Boolean(
        string='Requiere Autenticación',
        default=True,
        help='Indica si este endpoint requiere token de autenticación'
    )
    
    content_type = fields.Char(
        string='Content-Type',
        default='application/json',
        help='Tipo de contenido para las peticiones'
    )
    
    # Headers adicionales específicos del endpoint
    additional_headers = fields.Text(
        string='Headers Adicionales',
        help='Headers HTTP adicionales en formato JSON'
    )
    
    # Validación de respuesta
    expected_status_codes = fields.Char(
        string='Códigos de Estado Esperados',
        default='200,201,202',
        help='Códigos de estado HTTP considerados exitosos (separados por coma)'
    )
    
    # Información de documentación
    documentation_url = fields.Char(
        string='URL Documentación',
        help='URL a la documentación oficial de este endpoint'
    )
    
    version = fields.Char(
        string='Versión API',
        default='v1',
        help='Versión de la API utilizada'
    )
    
    # Estadísticas de uso
    usage_count = fields.Integer(
        string='Uso Total',
        readonly=True,
        default=0,
        help='Número total de veces que se ha utilizado este endpoint'
    )
    
    last_used = fields.Datetime(
        string='Último Uso',
        readonly=True,
        help='Fecha y hora del último uso'
    )
    
    success_rate = fields.Float(
        string='Tasa de Éxito (%)',
        compute='_compute_success_rate',
        help='Porcentaje de peticiones exitosas'
    )

    @api.depends('usage_count')
    def _compute_success_rate(self):
        """Calcula tasa de éxito basada en logs"""
        for endpoint in self:
            if endpoint.usage_count > 0:
                # Buscar logs relacionados con este endpoint
                logs = self.env['l10n_sv.api.log'].search([
                    ('request_url', 'like', endpoint.url),
                ])
                
                if logs:
                    successful = logs.filtered(lambda l: l.status == 'success')
                    endpoint.success_rate = (len(successful) / len(logs)) * 100
                else:
                    endpoint.success_rate = 0.0
            else:
                endpoint.success_rate = 0.0

    def increment_usage(self):
        """Incrementa contador de uso"""
        self.ensure_one()
        self.usage_count += 1
        self.last_used = fields.Datetime.now()

    def get_headers(self):
        """Obtiene headers para peticiones a este endpoint"""
        self.ensure_one()
        
        headers = {
            'Content-Type': self.content_type,
            'User-Agent': 'Odoo-EDI-SV/18.0'
        }
        
        # Agregar headers adicionales si existen
        if self.additional_headers:
            try:
                import json
                additional = json.loads(self.additional_headers)
                headers.update(additional)
            except (json.JSONDecodeError, TypeError):
                _logger.warning(f'Headers adicionales inválidos para endpoint {self.name}')
        
        return headers

    def is_success_status(self, status_code):
        """Verifica si un código de estado es considerado exitoso"""
        self.ensure_one()
        
        expected_codes = [int(code.strip()) for code in self.expected_status_codes.split(',')]
        return status_code in expected_codes

    @api.model
    def get_endpoint(self, environment, endpoint_type):
        """Obtiene endpoint específico por ambiente y tipo"""
        endpoint = self.search([
            ('environment', '=', environment),
            ('endpoint_type', '=', endpoint_type),
            ('active', '=', True)
        ], limit=1)
        
        if not endpoint:
            raise exceptions.UserError(_(
                'No se encontró endpoint %s para ambiente %s'
            ) % (endpoint_type, environment))
        
        return endpoint

    @api.model
    def setup_default_endpoints(self):
        """Configura endpoints por defecto del MH"""
        
        # Endpoints de certificación
        test_endpoints = [
            {
                'name': 'Autenticación - Certificación',
                'environment': 'test',
                'endpoint_type': 'auth',
                'url': 'https://apitestauth.mh.gob.sv/seguridad/auth',
                'method': 'POST',
                'description': 'Endpoint para obtener token de autenticación en ambiente de certificación',
                'requires_auth': False,
                'documentation_url': 'https://www.mh.gob.sv/descargas/dte/'
            },
            {
                'name': 'Envío DTE - Certificación',
                'environment': 'test',
                'endpoint_type': 'send',
                'url': 'https://apitest.mh.gob.sv/v1/dte',
                'method': 'POST',
                'description': 'Endpoint para enviar documentos DTE en ambiente de certificación'
            },
            {
                'name': 'Consulta Estado - Certificación',
                'environment': 'test',
                'endpoint_type': 'query',
                'url': 'https://apitest.mh.gob.sv/v1/dte/consulta',
                'method': 'POST',
                'description': 'Endpoint para consultar estado de DTE en ambiente de certificación'
            },
            {
                'name': 'Contingencia - Certificación',
                'environment': 'test',
                'endpoint_type': 'contingency',
                'url': 'https://apitest.mh.gob.sv/v1/dte/contingencia',
                'method': 'POST',
                'description': 'Endpoint para reportar eventos de contingencia en certificación'
            }
        ]
        
        # Endpoints de producción
        production_endpoints = [
            {
                'name': 'Autenticación - Producción',
                'environment': 'production',
                'endpoint_type': 'auth',
                'url': 'https://apiauth.mh.gob.sv/seguridad/auth',
                'method': 'POST',
                'description': 'Endpoint para obtener token de autenticación en ambiente de producción',
                'requires_auth': False,
                'documentation_url': 'https://www.mh.gob.sv/descargas/dte/'
            },
            {
                'name': 'Envío DTE - Producción',
                'environment': 'production',
                'endpoint_type': 'send',
                'url': 'https://api.mh.gob.sv/v1/dte',
                'method': 'POST',
                'description': 'Endpoint para enviar documentos DTE en ambiente de producción'
            },
            {
                'name': 'Consulta Estado - Producción',
                'environment': 'production',
                'endpoint_type': 'query',
                'url': 'https://api.mh.gob.sv/v1/dte/consulta',
                'method': 'POST',
                'description': 'Endpoint para consultar estado de DTE en ambiente de producción'
            },
            {
                'name': 'Contingencia - Producción',
                'environment': 'production',
                'endpoint_type': 'contingency',
                'url': 'https://api.mh.gob.sv/v1/dte/contingencia',
                'method': 'POST',
                'description': 'Endpoint para reportar eventos de contingencia en producción'
            }
        ]
        
        all_endpoints = test_endpoints + production_endpoints
        
        for endpoint_data in all_endpoints:
            # Verificar si ya existe
            existing = self.search([
                ('environment', '=', endpoint_data['environment']),
                ('endpoint_type', '=', endpoint_data['endpoint_type'])
            ])
            
            if not existing:
                self.create(endpoint_data)
                _logger.info(f"Endpoint creado: {endpoint_data['name']}")

    def action_test_endpoint(self):
        """Acción para probar conectividad del endpoint"""
        self.ensure_one()
        
        try:
            import requests
            
            # Para endpoints que no requieren autenticación, hacer petición simple
            if not self.requires_auth:
                response = requests.request(
                    method=self.method,
                    url=self.url,
                    headers=self.get_headers(),
                    timeout=self.timeout
                )
                
                if self.is_success_status(response.status_code):
                    message = f'Endpoint responde correctamente (HTTP {response.status_code})'
                    notification_type = 'success'
                else:
                    message = f'Endpoint responde con código inesperado: HTTP {response.status_code}'
                    notification_type = 'warning'
            else:
                # Para endpoints que requieren auth, solo verificar conectividad
                response = requests.head(self.url, timeout=self.timeout)
                message = f'Endpoint es accesible (conectividad OK)'
                notification_type = 'info'
            
            self.increment_usage()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Prueba de Endpoint'),
                    'message': _(message),
                    'type': notification_type
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error de Conectividad'),
                    'message': _('No se puede conectar al endpoint: %s') % str(e),
                    'type': 'danger'
                }
            }

    @api.model
    def get_environment_endpoints(self, environment):
        """Obtiene todos los endpoints para un ambiente específico"""
        return self.search([
            ('environment', '=', environment),
            ('active', '=', True)
        ])

    def action_view_logs(self):
        """Acción para ver logs relacionados con este endpoint"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Logs del Endpoint'),
            'res_model': 'l10n_sv.api.log',
            'view_mode': 'tree,form',
            'domain': [('request_url', 'like', self.url)],
            'context': {'default_request_url': self.url}
        }