import json
import logging
import requests
import ssl
import base64
from datetime import datetime, timedelta
from odoo import models, fields, api, exceptions, _
from odoo.tools import config

_logger = logging.getLogger(__name__)

try:
    import OpenSSL
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
except ImportError:
    _logger.warning("Librerías de criptografía no disponibles. Instale: pip install pyOpenSSL cryptography")


class L10nSvApiClient(models.Model):
    """Cliente API para comunicación con Ministerio de Hacienda"""
    _name = 'l10n_sv.api.client'
    _description = 'Cliente API MH El Salvador'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre descriptivo del cliente API'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía asociada a este cliente API'
    )
    
    environment = fields.Selection([
        ('test', 'Certificación'),
        ('production', 'Producción')
    ], string='Ambiente', required=True, default='test',
       help='Ambiente del MH (certificación o producción)')
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    # Configuración de certificados
    certificate_id = fields.Many2one(
        'l10n_sv.edi.certificate',
        string='Certificado Digital',
        required=True,
        help='Certificado .cert para autenticación con el MH'
    )
    
    # Credenciales MH API
    mh_api_user = fields.Char(
        string='Usuario MH API',
        help='Usuario proporcionado por el MH para acceso a la API'
    )
    
    mh_api_password = fields.Char(
        string='Contraseña MH API',
        help='Contraseña proporcionada por el MH para acceso a la API'
    )
    
    # URLs de API
    api_base_url = fields.Char(
        string='URL Base API',
        help='URL base de la API del MH para este ambiente'
    )
    
    api_token_url = fields.Char(
        string='URL Token',
        help='URL para obtener token de autenticación'
    )
    
    api_send_url = fields.Char(
        string='URL Envío DTE',
        help='URL para enviar documentos DTE'
    )
    
    api_query_url = fields.Char(
        string='URL Consulta',
        help='URL para consultar estado de DTE'
    )
    
    api_send_lote_url = fields.Char(
        string='URL Envío Lote',
        help='URL para enviar documentos DTE en lote'
    )
    
    api_query_lote_url = fields.Char(
        string='URL Consulta Lote',
        help='URL para consultar estado de lote DTE'
    )
    
    api_contingencia_url = fields.Char(
        string='URL Contingencia',
        help='URL para envío de eventos de contingencia'
    )
    
    api_anular_url = fields.Char(
        string='URL Anular',
        help='URL para envío de eventos de invalidación'
    )
    
    # Configuración de conexión
    timeout = fields.Integer(
        string='Timeout (segundos)',
        default=30,
        help='Tiempo límite para conexiones HTTP'
    )
    
    max_retries = fields.Integer(
        string='Máximo Reintentos',
        default=3,
        help='Número máximo de reintentos en caso de error'
    )
    
    retry_delay = fields.Integer(
        string='Retraso Reintento (segundos)',
        default=5,
        help='Tiempo de espera entre reintentos'
    )
    
    use_ssl_verification = fields.Boolean(
        string='Verificar SSL',
        default=True,
        help='Activar/desactivar verificación SSL (solo para pruebas)'
    )
    
    # Estado de autenticación
    auth_token = fields.Text(
        string='Token de Autenticación',
        readonly=True,
        help='Token JWT para autenticación con el MH'
    )
    
    token_expires_at = fields.Datetime(
        string='Token Expira',
        readonly=True,
        help='Fecha y hora de expiración del token'
    )
    
    last_auth_error = fields.Text(
        string='Último Error de Autenticación',
        readonly=True
    )
    
    # Estadísticas
    total_requests = fields.Integer(
        string='Total Peticiones',
        readonly=True,
        default=0
    )
    
    successful_requests = fields.Integer(
        string='Peticiones Exitosas',
        readonly=True,
        default=0
    )
    
    failed_requests = fields.Integer(
        string='Peticiones Fallidas',
        readonly=True,
        default=0
    )
    
    last_request_date = fields.Datetime(
        string='Última Petición',
        readonly=True
    )

    @api.model
    def _get_default_urls(self, environment):
        """Obtiene URLs oficiales según ambiente
        
        URLs oficiales del Ministerio de Hacienda de El Salvador
        según documentación técnica oficial.
        """
        if environment == 'production':
            return {
                'base': 'https://api.dtes.mh.gob.sv/fesv',
                'token': 'https://api.dtes.mh.gob.sv/seguridad/auth',
                'send': 'https://api.dtes.mh.gob.sv/fesv/recepciondte',
                'send_lote': 'https://api.dtes.mh.gob.sv/fesv/recepcionlote',
                'query': 'https://api.dtes.mh.gob.sv/fesv/recepcion/consultadte',
                'query_lote': 'https://api.dtes.mh.gob.sv/fesv/recepcion/consultadtelote',
                'contingencia': 'https://api.dtes.mh.gob.sv/fesv/contingencia',
                'anular': 'https://api.dtes.mh.gob.sv/fesv/anulardte'
            }
        else:  # test
            return {
                'base': 'https://apitest.dtes.mh.gob.sv/fesv',
                'token': 'https://apitest.dtes.mh.gob.sv/seguridad/auth',
                'send': 'https://apitest.dtes.mh.gob.sv/fesv/recepciondte',
                'send_lote': 'https://apitest.dtes.mh.gob.sv/fesv/recepcionlote',
                'query': 'https://apitest.dtes.mh.gob.sv/fesv/recepcion/consultadte',
                'query_lote': 'https://apitest.dtes.mh.gob.sv/fesv/recepcion/consultadtelote',
                'contingencia': 'https://apitest.dtes.mh.gob.sv/fesv/contingencia',
                'anular': 'https://apitest.dtes.mh.gob.sv/fesv/anulardte'
            }

    @api.onchange('environment')
    def _onchange_environment(self):
        """Actualiza URLs cuando cambia el ambiente"""
        if self.environment:
            urls = self._get_default_urls(self.environment)
            self.api_base_url = urls['base']
            self.api_token_url = urls['token']
            self.api_send_url = urls['send']
            self.api_query_url = urls['query']
            self.api_send_lote_url = urls['send_lote']
            self.api_query_lote_url = urls['query_lote']
            self.api_contingencia_url = urls['contingencia']
            self.api_anular_url = urls['anular']

    def _prepare_ssl_context(self):
        """Prepara configuración SSL con certificado .cert y clave .key"""
        self.ensure_one()
        
        # Si SSL está deshabilitado, no usar certificados
        if not self.use_ssl_verification:
            _logger.info('Verificación SSL deshabilitada para pruebas')
            return {
                'verify': False,
                'cert': None
            }
        
        # Si SSL habilitado pero no hay certificado
        if not self.certificate_id:
            _logger.warning('SSL habilitado pero no hay certificado configurado')
            return {
                'verify': True,  # Verificar SSL pero sin certificado cliente
                'cert': None
            }
        
        # Si no están ambos archivos del certificado
        if not self.certificate_id.certificate_file or not self.certificate_id.private_key_file:
            _logger.warning('Certificado incompleto (falta .cert o .key)')
            return {
                'verify': self.use_ssl_verification,
                'cert': None
            }
        
        try:
            # Decodificar certificado y clave privada desde base64
            cert_data = base64.b64decode(self.certificate_id.certificate_file)
            key_data = base64.b64decode(self.certificate_id.private_key_file)
            
            # Crear archivos temporales para requests
            import tempfile
            
            # Escribir certificado temporal
            cert_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.cert', delete=False)
            cert_file.write(cert_data)
            cert_file.close()
            
            # Escribir clave privada temporal
            key_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.key', delete=False)
            key_file.write(key_data)
            key_file.close()
            
            _logger.info(f'Certificados SSL configurados: {cert_file.name}, {key_file.name}')
            
            return {
                'verify': self.use_ssl_verification,
                'cert': (cert_file.name, key_file.name)
            }
                    
        except Exception as e:
            _logger.error(f'Error preparando SSL para cliente {self.name}: {str(e)}')
            return {
                'verify': self.use_ssl_verification,
                'cert': None
            }

    def _make_authenticated_request(self, method, url, data=None, headers=None):
        """Realiza petición HTTP autenticada con certificado"""
        self.ensure_one()
        
        # Verificar token válido
        if not self._is_token_valid():
            _logger.info('Token no válido o expirado, intentando autenticar...')
            self._authenticate()
        
        # Preparar headers
        request_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Odoo-EDI-SV/18.0'
        }
        
        # Solo agregar Authorization si tenemos token
        if self.auth_token:
            request_headers['Authorization'] = f'Bearer {self.auth_token}'
            _logger.info(f'Usando token de autenticación: {self.auth_token[:20]}...')
        else:
            _logger.warning('No hay token de autenticación disponible')
            # Intentar autenticar nuevamente
            self._authenticate()
            if self.auth_token:
                request_headers['Authorization'] = f'Bearer {self.auth_token}'
            else:
                raise exceptions.UserError(_('No se pudo obtener token de autenticación'))
        
        if headers:
            request_headers.update(headers)
        
        # Preparar SSL
        ssl_config = self._prepare_ssl_context()
        
        attempt = 0
        while attempt < self.max_retries:
            try:
                # Actualizar estadísticas
                self.total_requests += 1
                self.last_request_date = fields.Datetime.now()
                
                # Log de petición para debug
                _logger.info(f'Enviando {method} a {url}')
                _logger.info(f'Headers: {request_headers}')
                _logger.info(f'Data: {json.dumps(data, ensure_ascii=False) if data else "No data"}')
                
                # Realizar petición
                # Si data es string, enviarlo como data raw
                if isinstance(data, str):
                    response = requests.request(
                        method=method,
                        url=url,
                        data=data,
                        headers=request_headers,
                        timeout=self.timeout,
                        verify=ssl_config['verify'],
                        cert=ssl_config['cert']
                    )
                else:
                    response = requests.request(
                        method=method,
                        url=url,
                        json=data if data else None,
                        headers=request_headers,
                        timeout=self.timeout,
                        verify=ssl_config['verify'],
                        cert=ssl_config['cert']
                    )
                
                _logger.info(f'Respuesta recibida: {response.status_code}')
                
                # Verificar respuesta
                if response.status_code in [200, 201, 202]:
                    self.successful_requests += 1
                    try:
                        return response.json() if response.content else {}
                    except ValueError:
                        _logger.warning(f'Respuesta no es JSON válido: {response.text[:200]}')
                        return {'raw_response': response.text, 'status_code': response.status_code}
                elif response.status_code == 401:
                    # No autorizado - intentar re-autenticar
                    self.failed_requests += 1
                    _logger.warning('Error 401: Token inválido o expirado, re-autenticando...')
                    
                    # Limpiar token actual
                    self.auth_token = False
                    self.token_expires_at = False
                    
                    # Re-autenticar
                    try:
                        self._authenticate()
                        # Actualizar headers con nuevo token
                        if self.auth_token:
                            request_headers['Authorization'] = f'Bearer {self.auth_token}'
                        # Continuar con el siguiente intento
                        attempt += 1
                        continue
                    except Exception as e:
                        raise exceptions.UserError(_(
                            'Error re-autenticando después de 401: %s'
                        ) % str(e))
                else:
                    self.failed_requests += 1
                    error_msg = f'HTTP {response.status_code}: {response.text}'
                    _logger.warning(f'Error en petición MH: {error_msg}')
                    
                    if attempt < self.max_retries - 1:
                        attempt += 1
                        self.env.cr.commit()  # Guardar estadísticas
                        import time
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise exceptions.UserError(_(
                            'Error en comunicación con MH: %s'
                        ) % error_msg)
                        
            except requests.exceptions.RequestException as e:
                self.failed_requests += 1
                error_msg = str(e)
                _logger.error(f'Error de conexión MH para cliente {self.name}: {error_msg}')
                
                if attempt < self.max_retries - 1:
                    attempt += 1
                    self.env.cr.commit()  # Guardar estadísticas
                    import time
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise exceptions.UserError(_(
                        'Error de conexión con MH: %s'
                    ) % error_msg)
        
        # Si llegamos aquí sin devolver nada, es un error
        _logger.error('No se devolvió respuesta después de todos los intentos')
        return None

    def _is_token_valid(self):
        """Verifica si el token actual es válido"""
        if not self.auth_token or not self.token_expires_at:
            return False
        
        # Verificar expiración con margen de 5 minutos
        expiry_with_margin = self.token_expires_at - timedelta(minutes=5)
        return fields.Datetime.now() < expiry_with_margin

    def _authenticate(self):
        """Autentica con el MH usando certificado .cert"""
        self.ensure_one()
        
        if not self.api_token_url:
            raise exceptions.UserError(_('URL de autenticación no configurada'))
        
        try:
            # Preparar datos de autenticación
            ssl_config = self._prepare_ssl_context()
            
            # Primero intentar con GET para verificar disponibilidad del endpoint
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Odoo-EDI-SV/18.0',
                'Accept': 'application/json'
            }
            
            # Verificar que la empresa tenga establecimiento y punto de venta configurados
            if not self.company_id.l10n_sv_establishment_ids:
                # Crear establecimiento por defecto automáticamente
                _logger.info(f'Creando establecimiento por defecto para empresa {self.company_id.name}')
                establishment = self._create_default_establishment()
            else:
                # Obtener primer establecimiento activo
                establishment = self.company_id.l10n_sv_establishment_ids.filtered(lambda e: e.active)
                if not establishment:
                    raise exceptions.UserError(_(
                        'La empresa %s no tiene establecimientos activos. '
                        'Por favor active al menos un establecimiento.'
                    ) % self.company_id.name)
                establishment = establishment[0]
            
            # Verificar punto de venta
            if not establishment.point_of_sale_ids:
                raise exceptions.UserError(_(
                    'El establecimiento %s no tiene puntos de venta configurados. '
                    'Por favor configure al menos un punto de venta.'
                ) % establishment.name)
            
            point_of_sale = establishment.point_of_sale_ids.filtered(lambda p: p.active)
            if not point_of_sale:
                raise exceptions.UserError(_(
                    'El establecimiento %s no tiene puntos de venta activos. '
                    'Por favor active al menos un punto de venta.'
                ) % establishment.name)
            
            point_of_sale = point_of_sale[0]
            
            # Datos para solicitar token según especificación MH
            # Usar credenciales MH API si están configuradas, sino usar NIT y contraseña del certificado
            api_user = self.mh_api_user or (self.company_id.l10n_sv_nit or self.company_id.vat)
            api_password = self.mh_api_password or (self.certificate_id.password if self.certificate_id else '')
            
            auth_data = {
                'user': api_user,
                'pwd': api_password,
                'nit': self.company_id.l10n_sv_nit or self.company_id.vat,
                'codEstab': establishment.code,
                'codPtVenta': point_of_sale.code
            }
            
            # Log de datos que se van a enviar para debug
            _logger.info(f'Datos de autenticación: {auth_data}')
            _logger.info(f'Headers: {headers}')
            
            # Intentar diferentes formatos de datos
            formats_to_try = [
                ('json', auth_data),
                ('form', auth_data),
                ('params', auth_data)
            ]
            
            response = None
            last_error = None
            
            for format_type, data in formats_to_try:
                try:
                    _logger.info(f'Intentando autenticación con formato {format_type}')
                    
                    if format_type == 'json':
                        # Enviar como JSON en el body
                        response = requests.post(
                            url=self.api_token_url,
                            json=data,
                            headers=headers,
                            timeout=self.timeout,
                            verify=ssl_config['verify'],
                            cert=ssl_config['cert']
                        )
                    elif format_type == 'form':
                        # Enviar como form-data (FORMATO REQUERIDO POR MH)
                        form_headers = {k: v for k, v in headers.items() if k != 'Content-Type'}
                        form_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                        response = requests.post(
                            url=self.api_token_url,
                            data=data,
                            headers=form_headers,
                            timeout=self.timeout,
                            verify=ssl_config['verify'],
                            cert=ssl_config['cert']
                        )
                    else:  # params
                        # Enviar como query parameters en GET
                        response = requests.get(
                            url=self.api_token_url,
                            params=data,
                            headers=headers,
                            timeout=self.timeout,
                            verify=ssl_config['verify'],
                            cert=ssl_config['cert']
                        )
                    
                    _logger.info(f'Respuesta con formato {format_type}: {response.status_code} - {response.text[:200]}')
                    
                    # Si no es 400 con el mismo error, salir del loop
                    if response.status_code != 400:
                        break
                    
                    # Si es 400, verificar si es el mismo error de parámetro
                    try:
                        error_json = response.json()
                        if 'Parametro user no se encuentra' not in error_json.get('body', {}).get('descripcionMsg', ''):
                            # Es un error diferente, usar esta respuesta
                            break
                    except:
                        # No es JSON, usar esta respuesta
                        break
                        
                except requests.exceptions.RequestException as e:
                    last_error = e
                    continue
            
            # Verificar si obtuvimos una respuesta válida
            if not response:
                raise exceptions.UserError(_(
                    'No se pudo obtener respuesta del endpoint de autenticación. '
                    'Último error: %s'
                ) % (str(last_error) if last_error else 'Desconocido'))
            
            if response.status_code == 405:
                raise exceptions.UserError(_(
                    'El endpoint de autenticación no acepta ningún método HTTP válido. '
                    'Verifique la URL de autenticación: %s'
                ) % self.api_token_url)
            
            # Procesar respuesta
            if response.status_code == 200:
                try:
                    auth_response = response.json()
                    _logger.info(f'Respuesta de autenticación: {auth_response}')
                    
                    # Verificar si la autenticación fue exitosa
                    if auth_response.get('status') == 'OK':
                        # Buscar token en diferentes lugares posibles
                        token = None
                        body = auth_response.get('body', {})
                        
                        if isinstance(body, dict):
                            token = body.get('token') or body.get('access_token') or body.get('authToken')
                        
                        if token:
                            # Remover "Bearer " del token si está presente
                            if token.startswith('Bearer '):
                                token = token[7:]
                            
                            expires_in = body.get('expires_in', 3600)  # 1 hora por defecto
                            self.auth_token = token
                            self.token_expires_at = fields.Datetime.now() + timedelta(seconds=expires_in)
                            self.last_auth_error = False
                            _logger.info(f'Autenticación exitosa para cliente {self.name}')
                            return  # Salir del método después de autenticación exitosa
                        else:
                            _logger.warning(f'Token no encontrado en respuesta: {auth_response}')
                            # Si no hay token pero el status es OK, podría ser que no necesite token
                            # o que use otro método de autenticación
                            self.last_auth_error = False
                            # Guardar la respuesta completa por si acaso
                            self.auth_token = 'NO_TOKEN_REQUIRED'
                            self.token_expires_at = fields.Datetime.now() + timedelta(hours=1)
                            return  # Salir del método
                    else:
                        # Error específico del MH
                        error_details = auth_response.get('body', {})
                        error_msg = error_details.get('descripcionMsg', 'Error desconocido')
                        codigo_msg = error_details.get('codigoMsg', 'N/A')
                        
                        full_error = f'Código {codigo_msg}: {error_msg}'
                        self.last_auth_error = full_error
                        raise exceptions.UserError(_('Error de autenticación con MH: %s') % full_error)
                        
                except ValueError as e:
                    # No es JSON válido
                    error_msg = f'Respuesta no es JSON válido: {response.text[:200]}'
                    self.last_auth_error = error_msg
                    raise exceptions.UserError(_('Error de autenticación con MH: %s') % error_msg)
            else:
                # Error HTTP
                try:
                    error_response = response.json()
                    if 'body' in error_response and 'descripcionMsg' in error_response['body']:
                        error_msg = error_response['body']['descripcionMsg']
                    else:
                        error_msg = f'HTTP {response.status_code}: {response.text}'
                except:
                    error_msg = f'HTTP {response.status_code}: {response.text}'
                
                self.last_auth_error = error_msg
                raise exceptions.UserError(_('Error de autenticación con MH: %s') % error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            self.last_auth_error = error_msg
            _logger.error(f'Error de conexión durante autenticación: {error_msg}')
            raise exceptions.UserError(_(
                'Error de conexión durante autenticación: %s'
            ) % error_msg)

    def _sign_dte_with_mh_service(self, json_data):
        """Firma el DTE usando el servicio oficial del MH (SVFE-API-Firmador)"""
        try:
            # TRAZABILIDAD - Log al inicio del firmado
            _logger.info(f"===== INICIANDO FIRMA DE DTE =====")
            _logger.info(f"JSON pre-firma - version: {json_data.get('identificacion', {}).get('version') if isinstance(json_data, dict) else 'N/A'}")
            _logger.info(f"JSON pre-firma - tipoDte: {json_data.get('identificacion', {}).get('tipoDte') if isinstance(json_data, dict) else 'N/A'}")
            _logger.info(f"JSON pre-firma - numeroControl: {json_data.get('identificacion', {}).get('numeroControl') if isinstance(json_data, dict) else 'N/A'}")
            _logger.info(f"JSON pre-firma - ambiente: {json_data.get('identificacion', {}).get('ambiente') if isinstance(json_data, dict) else 'N/A'}")
            # URL oficial del firmador según documentación del MH
            # El firmador oficial del MH usando IP del gateway Docker
            sign_url = "http://172.17.0.1:8113/firmardocumento/"
            
            # Preparar datos para firmar
            if isinstance(json_data, str):
                json_str = json_data
            else:
                json_str = json.dumps(json_data, ensure_ascii=False)
            
            # Verificar que el certificado esté configurado
            if not self.certificate_id:
                raise exceptions.UserError(_('No hay certificado configurado'))
            
            # Preparar datos según la especificación oficial del firmador MH
            # El firmador del MH espera: nit (14 dígitos), dteJson (objeto), passwordPri
            nit_formatted = (self.company_id.l10n_sv_nit or self.company_id.vat or "").replace("-", "")
            
            # Asegurar que el NIT tenga 14 dígitos
            if len(nit_formatted) != 14:
                raise exceptions.UserError(_(
                    'El NIT debe tener exactamente 14 dígitos. NIT actual: %s (%d dígitos)'
                ) % (nit_formatted, len(nit_formatted)))
            
            # Convertir JSON string a objeto para enviar al firmador
            if isinstance(json_data, str):
                dte_object = json.loads(json_data)
            else:
                dte_object = json_data
            
            # Log detallado del JSON antes de enviarlo
            _logger.info(f"JSON DTE antes de firmar: {json.dumps(dte_object, ensure_ascii=False, indent=2)}")
            _logger.info(f"Tipo de dte_object: {type(dte_object)}")
            
            payload = {
                'nit': nit_formatted,
                'dteJson': dte_object,
                'passwordPri': self.certificate_id.password or '',
                'activo': True
            }
            
            # Log del payload completo
            _logger.info(f"Payload completo a enviar: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Enviar a firmar
            response = requests.post(
                sign_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # TRAZABILIDAD - Log de respuesta del firmador
                _logger.info(f"===== RESPUESTA DEL FIRMADOR =====")
                _logger.info(f"Status code: {response.status_code}")
                _logger.info(f"Response status: {response_data.get('status')}")
                
                # Verificar si el firmador devolvió error
                if response_data.get('status') == 'ERROR':
                    error_body = response_data.get('body', {})
                    error_code = error_body.get('codigo', 'N/A')
                    error_msg = error_body.get('mensaje', 'Error desconocido')
                    
                    # Proporcionar mensajes de error específicos según el código
                    if error_code == '803':
                        user_msg = _('No existe certificado válido para el NIT %s. Verifique que el certificado esté correctamente configurado en el sistema.') % (self.company_id.l10n_sv_nit or self.company_id.vat or 'N/A')
                    elif error_code == '801':
                        user_msg = _('No existe certificado activo. Verifique la configuración del certificado.')
                    elif error_code == '809':
                        user_msg = _('Faltan datos requeridos para firmar el documento. Error: %s') % error_msg
                    elif error_code == '811':
                        user_msg = _('Error en el formato de los datos del DTE. Verifique que el documento esté correctamente estructurado.')
                    elif error_code in ['812', '807']:
                        user_msg = _('Error en el servicio de firma: el certificado no está en el formato correcto. Contacte al administrador del sistema para verificar el formato del certificado PKCS#8.')
                    else:
                        user_msg = _('Error del servicio de firma (Código %s): %s') % (error_code, error_msg)
                    
                    _logger.error(f"Error del firmador - Código: {error_code}, Mensaje: {error_msg}")
                    raise exceptions.UserError(user_msg)
                
                # Si el estado es OK, devolver los datos firmados
                elif response_data.get('status') == 'OK':
                    body = response_data.get('body', response_data)
                    _logger.info(f"Documento firmado correctamente. Tipo de body: {type(body)}")
                    _logger.info(f"Contenido de body: {str(body)[:200]}...")
                    return body
                else:
                    # Respuesta exitosa del firmador con documento firmado
                    _logger.info(f"Respuesta del firmador sin status OK: {response_data}")
                    return response_data
                    
            else:
                _logger.error(f"Error HTTP firmando DTE: {response.status_code} - {response.text}")
                raise exceptions.UserError(_(
                    'Error de comunicación con servicio de firma (HTTP %s): %s'
                ) % (response.status_code, response.text))
                
        except Exception as e:
            _logger.error(f"Error en servicio de firma: {str(e)}")
            raise exceptions.UserError(_(
                'Error conectando con servicio de firma: %s'
            ) % str(e))

    def send_dte_to_mh(self, signed_dte, tipo_dte='01', ambiente='00'):
        """Envía DTE firmado al Ministerio de Hacienda"""
        self.ensure_one()
        
        if not self.api_send_url:
            raise exceptions.UserError(_('URL de envío no configurada'))
        
        if not signed_dte:
            raise exceptions.UserError(_('No hay documento firmado para enviar'))
        
        try:
            # Generar ID único para el envío
            import uuid
            envio_id = int(str(uuid.uuid4().int)[:8]) % 999999999
            
            # Preparar estructura de envío según especificación MH
            envio_data = {
                "ambiente": ambiente,  # 00=Certificación, 01=Producción
                "idEnvio": envio_id,
                "version": 1,  # Nota: Este es el version del protocolo MH, no del DTE
                "tipoDte": tipo_dte,  # Tipo de documento para el protocolo MH
                "documento": signed_dte  # JWT firmado que contiene el DTE real
            }
            
            _logger.info(f'Enviando DTE al MH: {self.api_send_url}')
            _logger.info(f'Datos de envío: ambiente={ambiente}, tipoDte={tipo_dte}, idEnvio={envio_id}')
            
            # Realizar petición autenticada
            response = self._make_authenticated_request(
                method='POST',
                url=self.api_send_url,
                data=envio_data
            )
            
            if response and response.status_code == 200:
                try:
                    response_data = response.json()
                    _logger.info(f'Respuesta del MH: {response_data}')
                    
                    # Verificar respuesta exitosa
                    if response_data.get('status') == 'OK':
                        body = response_data.get('body', {})
                        
                        # Extraer información relevante
                        result = {
                            'success': True,
                            'codigo_generacion': body.get('codigoGeneracion', ''),
                            'sello_recepcion': body.get('selloRecepcion', ''),
                            'fecha_procesamiento': body.get('fhProcesamiento', ''),
                            'estado': body.get('estado', ''),
                            'clasificar_msg': body.get('clasificaMsg', ''),
                            'observaciones': body.get('observaciones', []),
                            'raw_response': response_data
                        }
                        
                        _logger.info(f'✅ DTE enviado exitosamente. Sello: {result["sello_recepcion"]}')
                        return result
                        
                    else:
                        # Error del MH
                        error_body = response_data.get('body', {})
                        error_msg = error_body.get('descripcionMsg', 'Error desconocido')
                        codigo_msg = error_body.get('codigoMsg', 'N/A')
                        
                        _logger.error(f'❌ Error del MH - Código: {codigo_msg}, Mensaje: {error_msg}')
                        return {
                            'success': False,
                            'error_code': codigo_msg,
                            'error_message': error_msg,
                            'raw_response': response_data
                        }
                        
                except ValueError as e:
                    _logger.error(f'Respuesta del MH no es JSON válido: {response.text[:200]}')
                    return {
                        'success': False,
                        'error_code': 'JSON_ERROR',
                        'error_message': f'Respuesta no es JSON válido: {str(e)}',
                        'raw_response': response.text
                    }
            else:
                error_msg = f'HTTP {response.status_code if response else "No response"}'
                if response:
                    error_msg += f': {response.text[:200]}'
                
                _logger.error(f'❌ Error HTTP enviando DTE: {error_msg}')
                return {
                    'success': False,
                    'error_code': 'HTTP_ERROR',
                    'error_message': error_msg,
                    'raw_response': response.text if response else None
                }
                
        except Exception as e:
            _logger.error(f'Error inesperado enviando DTE al MH: {str(e)}')
            return {
                'success': False,
                'error_code': 'UNEXPECTED_ERROR',
                'error_message': f'Error inesperado: {str(e)}',
                'raw_response': None
            }
    
    def send_dte(self, json_data, numero_control, codigo_generacion):
        """Envía DTE al MH"""
        self.ensure_one()
        
        # TRAZABILIDAD COMPLETA - Log inicial para debugging
        _logger.info(f"===== EJECUTANDO API_CLIENT.SEND_DTE =====") 
        _logger.info(f"Client ID: {self.id}, Company: {self.company_id.name}")
        _logger.info(f"Environment: {self.environment}")
        _logger.info(f"JSON recibido - version: {json_data.get('identificacion', {}).get('version')} (tipo: {type(json_data.get('identificacion', {}).get('version'))})")
        _logger.info(f"JSON recibido - tipoDte: {json_data.get('identificacion', {}).get('tipoDte')} (tipo: {type(json_data.get('identificacion', {}).get('tipoDte'))})")
        _logger.info(f"JSON recibido - numeroControl: {json_data.get('identificacion', {}).get('numeroControl')}")
        _logger.info(f"JSON recibido - ambiente: {json_data.get('identificacion', {}).get('ambiente')}")
        _logger.info(f"COMPLETE JSON identificacion: {json_data.get('identificacion', {})}")
        
        if not self.api_send_url:
            raise exceptions.UserError(_('URL de envío no configurada'))
        
        if not json_data:
            raise exceptions.UserError(_('No hay datos JSON para enviar'))
        
        try:
            # Primero firmar el documento con el servicio del MH
            _logger.info('Firmando documento DTE...')
            documento_firmado = self._sign_dte_with_mh_service(json_data)
            
            # Según la especificación del MH, el DTE firmado debe enviarse 
            # dentro de un objeto JSON con formato específico
            if isinstance(documento_firmado, dict) and 'body' in documento_firmado:
                # Si el firmador devolvió una respuesta con estructura, extraer el documento firmado
                documento_jwt = documento_firmado.get('body', documento_firmado)
            else:
                # Si es directamente el documento firmado JWT
                documento_jwt = documento_firmado
            
            # El MH espera el DTE en este formato específico según su documentación
            # Extraer valores del JSON original para mantener consistencia
            identificacion = json_data.get('identificacion', {})
            ambiente = identificacion.get('ambiente', '00')
            version = identificacion.get('version', 1)
            tipo_dte = identificacion.get('tipoDte', '01')
            
            send_data = {
                "ambiente": ambiente,  # Usar el ambiente del JSON
                "idEnvio": 1,
                "version": version,  # Usar la versión del JSON (ej: 3 para CCF)
                "tipoDte": tipo_dte,  # Usar el tipo del JSON (ej: "03" para CCF)
                "documento": documento_jwt
            }
            
            # Log detallado para debug
            nit = (self.company_id.l10n_sv_nit or self.company_id.vat or "").replace("-", "")
            _logger.info(f'===== DEBUGGING SEND_DTE METHOD =====')
            _logger.info(f'Documento firmado recibido: {type(documento_firmado)}')
            _logger.info(f'NIT empresa: {nit}')
            _logger.info(f'JSON identificacion recibido: {identificacion}')
            _logger.info(f'Valores extraídos - ambiente: {ambiente}, version: {version} (tipo: {type(version)}), tipoDte: {tipo_dte} (tipo: {type(tipo_dte)})')
            
            # VALIDACIÓN CRÍTICA PARA CCF
            if tipo_dte == '03':
                _logger.info(f'===== PROCESANDO CCF - VALIDACIÓN CRÍTICA =====')
                if version != 3:
                    _logger.error(f'ERROR CCF: version incorrecta {version}, debe ser 3')
                if ambiente not in ['00', '01']:
                    _logger.warning(f'CCF ambiente: {ambiente} - verificar si es correcto')
            
            _logger.info(f'Estructura send_data: {json.dumps(send_data, ensure_ascii=False, indent=2)}')
            
            # Crear log de petición
            api_log = self.env['l10n_sv.api.log'].create({
                'client_id': self.id,
                'request_type': 'send_dte',
                'numero_control': numero_control,
                'codigo_generacion': codigo_generacion,
                'request_data': json.dumps(send_data, ensure_ascii=False),
                'request_date': fields.Datetime.now(),
                'status': 'pending'
            })
            
            # Enviar DTE
            response_data = self._make_authenticated_request(
                'POST', 
                self.api_send_url, 
                send_data
            )
            
            # Validar que tenemos respuesta
            if not response_data:
                raise exceptions.UserError(_('No se recibió respuesta del servidor MH'))
            
            # Procesar respuesta
            success = False
            status_code = None
            
            # Log de respuesta para debug
            _logger.info(f'Respuesta de envío DTE: {response_data}')
            
            if isinstance(response_data, dict):
                if response_data.get('status') == 'OK':
                    success = True
                    status_code = 'RECEIVED'
                elif response_data.get('estado') == 'PROCESADO':
                    success = True
                    status_code = 'PROCESSED'
                elif response_data.get('status') == 'ERROR':
                    # Manejar error específico del MH
                    body = response_data.get('body', {})
                    error_msg = body.get('descripcionMsg', 'Error desconocido')
                    codigo_msg = body.get('codigoMsg', 'N/A')
                    raise exceptions.UserError(_(
                        'Error del MH (Código %s): %s'
                    ) % (codigo_msg, error_msg))
            else:
                _logger.warning(f'Respuesta no es un diccionario: {type(response_data)}')
            
            # Actualizar log
            api_log.write({
                'response_data': json.dumps(response_data, ensure_ascii=False) if response_data else '{}',
                'response_date': fields.Datetime.now(),
                'status': 'success' if success else 'error',
                'status_code': status_code or (response_data.get('estado', 'UNKNOWN') if isinstance(response_data, dict) else 'UNKNOWN'),
                'error_message': (response_data.get('descripcionMsg') if isinstance(response_data, dict) else None) if not success else None
            })
            
            return {
                'success': success,
                'response': response_data,
                'log_id': api_log.id
            }
            
        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error enviando DTE {numero_control}: {error_msg}')
            
            # Actualizar log con error
            if 'api_log' in locals():
                api_log.write({
                    'response_date': fields.Datetime.now(),
                    'status': 'error',
                    'error_message': error_msg
                })
            
            raise exceptions.UserError(_(
                'Error enviando DTE al MH: %s'
            ) % error_msg)

    def _create_default_establishment(self):
        """Crea un establecimiento por defecto para la empresa"""
        self.ensure_one()
        
        # Crear establecimiento por defecto
        establishment_vals = {
            'name': f'Establecimiento Principal - {self.company_id.name}',
            'code': '0001',  # Código por defecto
            'company_id': self.company_id.id,
            'is_main': True,
            'active': True,
            'street': self.company_id.street or '',
            'departamento_code': '06',  # San Salvador por defecto
            'municipio_code': '01',     # San Salvador por defecto
        }
        
        establishment = self.env['l10n_sv.establishment'].create(establishment_vals)
        
        # Crear punto de venta por defecto
        pos_vals = {
            'name': 'Punto de Venta Principal',
            'code': '001',  # Código por defecto
            'establishment_id': establishment.id,
            'active': True,
        }
        
        self.env['l10n_sv.point.of.sale'].create(pos_vals)
        
        _logger.info(f'Establecimiento {establishment.code} y punto de venta creados para empresa {self.company_id.name}')
        return establishment

    def query_dte_status(self, numero_control, codigo_generacion):
        """Consulta estado de DTE en el MH"""
        self.ensure_one()
        
        if not self.api_query_url:
            raise exceptions.UserError(_('URL de consulta no configurada'))
        
        try:
            # Preparar datos de consulta
            query_data = {
                'codigoGeneracion': codigo_generacion,
                'numeroControl': numero_control
            }
            
            # Crear log de consulta
            api_log = self.env['l10n_sv.api.log'].create({
                'client_id': self.id,
                'request_type': 'query_status',
                'numero_control': numero_control,
                'codigo_generacion': codigo_generacion,
                'request_data': json.dumps(query_data, ensure_ascii=False),
                'request_date': fields.Datetime.now(),
                'status': 'pending'
            })
            
            # Consultar estado
            response_data = self._make_authenticated_request(
                'POST',
                self.api_query_url,
                query_data
            )
            
            # Actualizar log
            api_log.write({
                'response_data': json.dumps(response_data, ensure_ascii=False),
                'response_date': fields.Datetime.now(),
                'status': 'success',
                'status_code': response_data.get('estado', 'UNKNOWN')
            })
            
            return {
                'success': True,
                'response': response_data,
                'log_id': api_log.id
            }
            
        except Exception as e:
            error_msg = str(e)
            _logger.error(f'Error consultando estado DTE {numero_control}: {error_msg}')
            
            if 'api_log' in locals():
                api_log.write({
                    'response_date': fields.Datetime.now(),
                    'status': 'error',
                    'error_message': error_msg
                })
            
            raise exceptions.UserError(_(
                'Error consultando estado DTE: %s'
            ) % error_msg)

    def test_simple_connection(self):
        """Prueba conexión simple sin autenticación"""
        self.ensure_one()
        
        results = []
        ssl_config = self._prepare_ssl_context()
        
        # Lista de URLs a probar
        urls_to_test = [
            ('Base URL', self.api_base_url),
            ('Token URL', self.api_token_url),
            ('Send URL', self.api_send_url),
            ('Query URL', self.api_query_url)
        ]
        
        for name, url in urls_to_test:
            if not url:
                results.append(f"✗ {name}: No configurada")
                continue
                
            try:
                # Prueba simple con HEAD o GET
                response = requests.head(
                    url,
                    timeout=5,
                    verify=ssl_config['verify'],
                    cert=ssl_config['cert'],
                    allow_redirects=True
                )
                results.append(f"✓ {name}: {response.status_code} ({url})")
            except requests.exceptions.ConnectionError:
                results.append(f"✗ {name}: No se puede conectar ({url})")
            except requests.exceptions.Timeout:
                results.append(f"✗ {name}: Timeout ({url})")
            except Exception as e:
                results.append(f"✗ {name}: {str(e)} ({url})")
        
        return "\n".join(results)
    
    def action_test_connection(self):
        """Acción para probar conexión con el MH"""
        self.ensure_one()
        
        try:
            # Primer paso: verificar conectividad básica
            test_results = []
            
            # Probar conectividad simple primero
            simple_test = self.test_simple_connection()
            test_results.append("=== Prueba de Conectividad ===")
            test_results.append(simple_test)
            test_results.append("")
            
            # Preparar configuración SSL
            ssl_config = self._prepare_ssl_context()
            
            # Probar conectividad a la URL base
            if self.api_base_url:
                try:
                    response = requests.get(
                        self.api_base_url,
                        timeout=10,
                        verify=ssl_config['verify'],
                        cert=ssl_config['cert']
                    )
                    test_results.append(f"✓ URL Base accesible ({response.status_code})")
                except Exception as e:
                    test_results.append(f"✗ URL Base falló: {str(e)}")
            
            # Probar URL de autenticación
            if self.api_token_url:
                try:
                    response = requests.get(
                        self.api_token_url,
                        timeout=10,
                        verify=ssl_config['verify'],
                        cert=ssl_config['cert']
                    )
                    test_results.append(f"✓ URL Token accesible ({response.status_code})")
                except Exception as e:
                    test_results.append(f"✗ URL Token falló: {str(e)}")
            
            # Intentar autenticación real solo si las URLs básicas funcionan
            auth_success = False
            try:
                self._authenticate()
                test_results.append("✓ Autenticación exitosa")
                auth_success = True
            except Exception as e:
                test_results.append(f"✗ Autenticación falló: {str(e)}")
            
            message = "\\n".join(test_results)
            
            if auth_success:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Conexión Exitosa'),
                        'message': message,
                        'type': 'success'
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Prueba de Conexión'),
                        'message': message + "\\n\\n" + _(
                            "NOTA: Las URLs actuales son ejemplos. "
                            "Necesita obtener los endpoints reales del MH de El Salvador "
                            "a través de su proceso de certificación oficial."
                        ),
                        'type': 'warning'
                    }
                }
                
        except Exception as e:
            raise exceptions.UserError(_('Error probando conexión: %s') % str(e))

    @api.model
    def get_default_client(self, company_id=None):
        """Obtiene cliente por defecto para la compañía"""
        if not company_id:
            company_id = self.env.company.id
        
        client = self.search([
            ('company_id', '=', company_id),
            ('active', '=', True)
        ], limit=1)
        
        if not client:
            raise exceptions.UserError(_(
                'No hay cliente API configurado para esta compañía'
            ))
        
        return client

    def action_view_logs(self):
        """Acción para ver logs de API"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Logs API MH',
            'res_model': 'l10n_sv.api.log',
            'view_mode': 'list,form',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id}
        }

    def action_authenticate(self):
        """Acción para autenticar manualmente"""
        self.ensure_one()
        try:
            self._authenticate()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Autenticación Exitosa'),
                    'message': _('Se ha autenticado correctamente con el MH'),
                    'type': 'success'
                }
            }
        except Exception as e:
            raise exceptions.UserError(_('Error en autenticación: %s') % str(e))

    # Campos calculados para estadísticas
    @api.depends('l10n_sv_api_log_ids')
    def _compute_request_stats(self):
        """Calcular estadísticas de peticiones"""
        for client in self:
            logs = client.l10n_sv_api_log_ids
            client.total_requests = len(logs)
            client.successful_requests = len(logs.filtered(lambda l: l.status == 'success'))
            client.failed_requests = len(logs.filtered(lambda l: l.status == 'error'))
            client.last_request_date = max(logs.mapped('request_date')) if logs else False

    # Campos de estadísticas
    l10n_sv_api_log_ids = fields.One2many(
        'l10n_sv.api.log',
        'client_id',
        string='Logs API'
    )
    
    total_requests = fields.Integer(
        string='Total Peticiones',
        compute='_compute_request_stats',
        store=True,
        help='Número total de peticiones realizadas'
    )
    
    successful_requests = fields.Integer(
        string='Peticiones Exitosas',
        compute='_compute_request_stats',
        store=True,
        help='Número de peticiones exitosas'
    )
    
    failed_requests = fields.Integer(
        string='Peticiones Fallidas',
        compute='_compute_request_stats',
        store=True,
        help='Número de peticiones que fallaron'
    )
    
    last_request_date = fields.Datetime(
        string='Última Petición',
        compute='_compute_request_stats',
        store=True,
        help='Fecha y hora de la última petición'
    )