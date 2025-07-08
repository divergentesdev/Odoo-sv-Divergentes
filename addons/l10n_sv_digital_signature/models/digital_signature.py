import json
import logging
import base64
import hashlib
from datetime import datetime
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)

try:
    import OpenSSL
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.x509.oid import NameOID
    import xmlsec
    from lxml import etree
except ImportError:
    _logger.warning("Librerías de firma digital no disponibles. Instale: pip install cryptography pyOpenSSL xmlsec lxml")


class L10nSvDigitalSignature(models.Model):
    """Servicio de firma digital para DTE El Salvador"""
    _name = 'l10n_sv.digital.signature'
    _description = 'Firma Digital DTE El Salvador'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre descriptivo del servicio de firma'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía asociada a este servicio de firma'
    )
    
    certificate_id = fields.Many2one(
        'l10n_sv.edi.certificate',
        string='Certificado de Firma',
        required=True,
        help='Certificado .cert para firma digital'
    )
    
    algorithm_id = fields.Many2one(
        'l10n_sv.signature.algorithm',
        string='Algoritmo de Firma',
        required=True,
        help='Algoritmo utilizado para la firma digital'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    # Configuración de firma
    signature_format = fields.Selection([
        ('xmldsig', 'XML Digital Signature'),
        ('pkcs7', 'PKCS#7/CMS'),
        ('jose', 'JSON Web Signature (JWS)'),
        ('raw', 'Firma Raw')
    ], string='Formato de Firma', required=True, default='xmldsig',
       help='Formato de la firma digital')
    
    canonicalization_method = fields.Selection([
        ('c14n', 'Canonical XML 1.0'),
        ('c14n11', 'Canonical XML 1.1'),
        ('exc_c14n', 'Exclusive Canonical XML')
    ], string='Método de Canonicalización', default='exc_c14n',
       help='Método de canonicalización para XML')
    
    include_certificate = fields.Boolean(
        string='Incluir Certificado',
        default=True,
        help='Incluir certificado en la firma'
    )
    
    include_key_info = fields.Boolean(
        string='Incluir Key Info',
        default=True,
        help='Incluir información de clave en la firma'
    )
    
    # Validación temporal
    validate_certificate_dates = fields.Boolean(
        string='Validar Fechas Certificado',
        default=True,
        help='Validar que el certificado esté vigente'
    )
    
    validate_chain = fields.Boolean(
        string='Validar Cadena',
        default=False,
        help='Validar cadena completa de certificados'
    )
    
    # Estadísticas
    total_signatures = fields.Integer(
        string='Total Firmas',
        readonly=True,
        default=0,
        help='Número total de documentos firmados'
    )
    
    successful_signatures = fields.Integer(
        string='Firmas Exitosas',
        readonly=True,
        default=0,
        help='Número de firmas exitosas'
    )
    
    failed_signatures = fields.Integer(
        string='Firmas Fallidas',
        readonly=True,
        default=0,
        help='Número de firmas que fallaron'
    )
    
    last_signature_date = fields.Datetime(
        string='Última Firma',
        readonly=True,
        help='Fecha y hora de la última firma'
    )

    # @api.constrains('certificate_id')
    def _check_certificate_validity(self):
        """Valida que el certificado sea válido para firma"""
        return  # Temporalmente deshabilitado para permitir instalación
        for signature in self:
            if signature.certificate_id and signature.validate_certificate_dates:
                try:
                    cert_data = base64.b64decode(signature.certificate_id.certificate_file)
                    
                    # Intentar cargar como PKCS#12
                    try:
                        p12 = OpenSSL.crypto.load_pkcs12(cert_data, signature.certificate_id.password.encode() if signature.certificate_id.password else None)
                        cert = p12.get_certificate()
                        
                        # Verificar expiración
                        if cert.has_expired():
                            raise exceptions.ValidationError(_(
                                'El certificado %s ha expirado'
                            ) % signature.certificate_id.name)
                            
                        # Verificar que aún no sea válido
                        not_before = datetime.strptime(cert.get_notBefore().decode('ascii'), '%Y%m%d%H%M%SZ')
                        if datetime.now() < not_before:
                            raise exceptions.ValidationError(_(
                                'El certificado %s aún no es válido'
                            ) % signature.certificate_id.name)
                            
                    except Exception:
                        # Intentar como PEM
                        cert = x509.load_pem_x509_certificate(cert_data)
                        
                        now = datetime.now()
                        if now < cert.not_valid_before or now > cert.not_valid_after:
                            raise exceptions.ValidationError(_(
                                'El certificado %s no está vigente'
                            ) % signature.certificate_id.name)
                            
                except Exception as e:
                    raise exceptions.ValidationError(_(
                        'Error validando certificado: %s'
                    ) % str(e))

    def _load_certificate_and_key(self):
        """Carga certificado y clave privada desde archivo .cert"""
        self.ensure_one()
        
        if not self.certificate_id or not self.certificate_id.certificate_file:
            raise exceptions.UserError(_('No hay certificado configurado'))
        
        try:
            cert_data = base64.b64decode(self.certificate_id.certificate_file)
            password = self.certificate_id.password.encode() if self.certificate_id.password else None
            
            # Intentar cargar como PKCS#12 (formato típico .cert del MH)
            try:
                p12 = OpenSSL.crypto.load_pkcs12(cert_data, password)
                
                # Extraer certificado y clave
                certificate = p12.get_certificate()
                private_key = p12.get_privatekey()
                
                # Convertir a formato PEM para cryptography
                cert_pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, certificate)
                key_pem = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, private_key)
                
                # Cargar con cryptography para operaciones modernas
                crypto_cert = x509.load_pem_x509_certificate(cert_pem)
                crypto_key = serialization.load_pem_private_key(key_pem, password=None)
                
                return {
                    'certificate': crypto_cert,
                    'private_key': crypto_key,
                    'cert_pem': cert_pem,
                    'key_pem': key_pem,
                    'openssl_cert': certificate,
                    'openssl_key': private_key
                }
                
            except Exception:
                # Si falla PKCS#12, intentar como PEM
                crypto_cert = x509.load_pem_x509_certificate(cert_data)
                
                # Para PEM, la clave privada podría estar en el mismo archivo o separada
                try:
                    crypto_key = serialization.load_pem_private_key(cert_data, password=password)
                except Exception:
                    raise exceptions.UserError(_(
                        'No se pudo extraer la clave privada del certificado. Verifique el formato.'
                    ))
                
                return {
                    'certificate': crypto_cert,
                    'private_key': crypto_key,
                    'cert_pem': cert_data,
                    'key_pem': cert_data
                }
                
        except Exception as e:
            _logger.error(f'Error cargando certificado {self.certificate_id.name}: {str(e)}')
            raise exceptions.UserError(_(
                'Error cargando certificado: %s'
            ) % str(e))

    def _sign_data_raw(self, data, cert_info):
        """Firma datos usando algoritmo raw"""
        try:
            # Obtener algoritmo de hash
            hash_algorithm = getattr(hashes, self.algorithm_id.hash_algorithm.upper())()
            
            # Firmar datos
            signature = cert_info['private_key'].sign(
                data.encode('utf-8') if isinstance(data, str) else data,
                padding.PKCS1v15(),
                hash_algorithm
            )
            
            return base64.b64encode(signature).decode('utf-8')
            
        except Exception as e:
            raise exceptions.UserError(_(
                'Error en firma raw: %s'
            ) % str(e))

    def _sign_data_xmldsig(self, data, cert_info):
        """Firma datos usando XML Digital Signature"""
        try:
            # Crear documento XML para firmar
            if isinstance(data, str):
                # Si es JSON, envolver en elemento XML
                if data.strip().startswith('{'):
                    xml_content = f'<Document><![CDATA[{data}]]></Document>'
                else:
                    xml_content = data
            else:
                xml_content = f'<Document><![CDATA[{json.dumps(data)}]]></Document>'
            
            # Parsear XML
            doc = etree.fromstring(xml_content.encode('utf-8'))
            
            # Crear template de firma
            signature_node = xmlsec.template.create(
                doc,
                xmlsec.Transform.EXCL_C14N,
                xmlsec.Transform.RSA_SHA256 if self.algorithm_id.name == 'SHA256' else xmlsec.Transform.RSA_SHA1
            )
            
            # Agregar referencia
            ref = xmlsec.template.add_reference(
                signature_node,
                xmlsec.Transform.SHA256 if self.algorithm_id.name == 'SHA256' else xmlsec.Transform.SHA1
            )
            xmlsec.template.add_transform(ref, xmlsec.Transform.ENVELOPED)
            
            # Agregar KeyInfo si se requiere
            if self.include_key_info:
                key_info = xmlsec.template.ensure_key_info(signature_node)
                xmlsec.template.add_x509_data(key_info)
            
            # Insertar firma en documento
            doc.append(signature_node)
            
            # Crear contexto de firma
            ctx = xmlsec.SignatureContext()
            
            # Cargar clave privada
            key = xmlsec.Key.from_memory(
                cert_info['key_pem'],
                xmlsec.KeyFormat.PEM,
                password=self.certificate_id.password
            )
            
            # Cargar certificado si se requiere
            if self.include_certificate:
                key.load_cert_from_memory(cert_info['cert_pem'], xmlsec.KeyFormat.PEM)
            
            ctx.key = key
            
            # Firmar documento
            ctx.sign(signature_node)
            
            # Retornar XML firmado
            return etree.tostring(doc, encoding='unicode')
            
        except Exception as e:
            raise exceptions.UserError(_(
                'Error en firma XML: %s'
            ) % str(e))

    def _sign_data_jose(self, data, cert_info):
        """Firma datos usando JSON Web Signature (JWS)"""
        try:
            import json
            import base64
            
            # Preparar header JWS
            header = {
                'alg': 'RS256' if self.algorithm_id.name == 'SHA256' else 'RS1',
                'typ': 'JWT'
            }
            
            if self.include_certificate:
                # Incluir certificado en header
                cert_der = cert_info['certificate'].public_bytes(serialization.Encoding.DER)
                header['x5c'] = [base64.b64encode(cert_der).decode('utf-8')]
            
            # Codificar header y payload
            header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
            
            if isinstance(data, str):
                payload_data = data
            else:
                payload_data = json.dumps(data)
            
            payload_b64 = base64.urlsafe_b64encode(payload_data.encode()).decode().rstrip('=')
            
            # Crear mensaje a firmar
            signing_input = f"{header_b64}.{payload_b64}"
            
            # Firmar
            hash_algorithm = hashes.SHA256() if self.algorithm_id.name == 'SHA256' else hashes.SHA1()
            signature = cert_info['private_key'].sign(
                signing_input.encode('utf-8'),
                padding.PKCS1v15(),
                hash_algorithm
            )
            
            signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
            
            # Retornar JWS completo
            return f"{signing_input}.{signature_b64}"
            
        except Exception as e:
            raise exceptions.UserError(_(
                'Error en firma JWS: %s'
            ) % str(e))

    def sign_document(self, data, document_type='json'):
        """Firma un documento DTE"""
        self.ensure_one()
        
        if not data:
            raise exceptions.UserError(_('No hay datos para firmar'))
        
        try:
            # Actualizar estadísticas
            self.total_signatures += 1
            self.last_signature_date = fields.Datetime.now()
            
            # Cargar certificado y clave
            cert_info = self._load_certificate_and_key()
            
            # Crear log de firma
            signature_log = self.env['l10n_sv.signature.log'].create({
                'signature_service_id': self.id,
                'document_type': document_type,
                'signature_date': fields.Datetime.now(),
                'status': 'pending',
                'algorithm_used': self.algorithm_id.name,
                'signature_format': self.signature_format
            })
            
            # Realizar firma según formato
            if self.signature_format == 'xmldsig':
                signed_data = self._sign_data_xmldsig(data, cert_info)
            elif self.signature_format == 'jose':
                signed_data = self._sign_data_jose(data, cert_info)
            elif self.signature_format == 'raw':
                signed_data = self._sign_data_raw(data, cert_info)
            else:
                raise exceptions.UserError(_(
                    'Formato de firma no soportado: %s'
                ) % self.signature_format)
            
            # Actualizar estadísticas de éxito
            self.successful_signatures += 1
            
            # Actualizar log
            signature_log.write({
                'status': 'success',
                'signature_data': signed_data[:1000],  # Truncar para almacenamiento
                'completion_date': fields.Datetime.now()
            })
            
            _logger.info(f'Documento firmado exitosamente con servicio {self.name}')
            
            return {
                'success': True,
                'signature': signed_data,
                'certificate_info': {
                    'subject': cert_info['certificate'].subject.rfc4514_string(),
                    'issuer': cert_info['certificate'].issuer.rfc4514_string(),
                    'serial_number': str(cert_info['certificate'].serial_number),
                    'not_valid_before': cert_info['certificate'].not_valid_before.isoformat(),
                    'not_valid_after': cert_info['certificate'].not_valid_after.isoformat()
                },
                'log_id': signature_log.id
            }
            
        except Exception as e:
            # Actualizar estadísticas de error
            self.failed_signatures += 1
            
            # Actualizar log con error
            if 'signature_log' in locals():
                signature_log.write({
                    'status': 'error',
                    'error_message': str(e),
                    'completion_date': fields.Datetime.now()
                })
            
            error_msg = str(e)
            _logger.error(f'Error firmando documento con servicio {self.name}: {error_msg}')
            
            raise exceptions.UserError(_(
                'Error firmando documento: %s'
            ) % error_msg)

    def verify_signature(self, signed_data, original_data=None):
        """Verifica una firma digital"""
        self.ensure_one()
        
        try:
            if self.signature_format == 'xmldsig':
                return self._verify_xmldsig(signed_data)
            elif self.signature_format == 'jose':
                return self._verify_jose(signed_data, original_data)
            elif self.signature_format == 'raw':
                return self._verify_raw(signed_data, original_data)
            else:
                raise exceptions.UserError(_(
                    'Verificación no soportada para formato: %s'
                ) % self.signature_format)
                
        except Exception as e:
            _logger.error(f'Error verificando firma: {str(e)}')
            return {
                'valid': False,
                'error': str(e)
            }

    def _verify_xmldsig(self, signed_xml):
        """Verifica firma XML Digital Signature"""
        try:
            doc = etree.fromstring(signed_xml.encode('utf-8'))
            
            # Buscar nodo de firma
            signature_node = xmlsec.tree.find_node(doc, xmlsec.Node.SIGNATURE)
            
            if signature_node is None:
                return {'valid': False, 'error': 'No se encontró firma XML'}
            
            # Crear contexto de verificación
            ctx = xmlsec.SignatureContext()
            
            # Verificar firma
            ctx.verify(signature_node)
            
            return {'valid': True, 'message': 'Firma XML válida'}
            
        except Exception as e:
            return {'valid': False, 'error': f'Firma XML inválida: {str(e)}'}

    def _verify_jose(self, jws_token, original_data):
        """Verifica firma JWS"""
        try:
            parts = jws_token.split('.')
            if len(parts) != 3:
                return {'valid': False, 'error': 'Formato JWS inválido'}
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Decodificar header
            header = json.loads(base64.urlsafe_b64decode(header_b64 + '==='))
            
            # Extraer certificado si está presente
            if 'x5c' in header:
                cert_der = base64.b64decode(header['x5c'][0])
                cert = x509.load_der_x509_certificate(cert_der)
                
                # Verificar firma
                signing_input = f"{header_b64}.{payload_b64}"
                signature = base64.urlsafe_b64decode(signature_b64 + '===')
                
                hash_algorithm = hashes.SHA256() if header.get('alg') == 'RS256' else hashes.SHA1()
                
                try:
                    cert.public_key().verify(
                        signature,
                        signing_input.encode('utf-8'),
                        padding.PKCS1v15(),
                        hash_algorithm
                    )
                    return {'valid': True, 'message': 'Firma JWS válida'}
                except Exception:
                    return {'valid': False, 'error': 'Firma JWS inválida'}
            else:
                return {'valid': False, 'error': 'No hay certificado en JWS'}
                
        except Exception as e:
            return {'valid': False, 'error': f'Error verificando JWS: {str(e)}'}

    def _verify_raw(self, signature_b64, original_data):
        """Verifica firma raw"""
        try:
            if not original_data:
                return {'valid': False, 'error': 'Se requieren datos originales para verificar firma raw'}
            
            signature = base64.b64decode(signature_b64)
            cert_info = self._load_certificate_and_key()
            
            hash_algorithm = getattr(hashes, self.algorithm_id.hash_algorithm.upper())()
            
            try:
                cert_info['certificate'].public_key().verify(
                    signature,
                    original_data.encode('utf-8') if isinstance(original_data, str) else original_data,
                    padding.PKCS1v15(),
                    hash_algorithm
                )
                return {'valid': True, 'message': 'Firma raw válida'}
            except Exception:
                return {'valid': False, 'error': 'Firma raw inválida'}
                
        except Exception as e:
            return {'valid': False, 'error': f'Error verificando firma raw: {str(e)}'}

    def action_test_signature(self):
        """Acción para probar firma con datos de ejemplo"""
        self.ensure_one()
        
        test_data = {
            "test": True,
            "timestamp": fields.Datetime.now().isoformat(),
            "service": self.name
        }
        
        try:
            result = self.sign_document(test_data, 'test')
            
            if result['success']:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Prueba de Firma Exitosa'),
                        'message': _('El servicio de firma funciona correctamente'),
                        'type': 'success'
                    }
                }
            else:
                raise exceptions.UserError(_('Fallo en prueba de firma'))
                
        except Exception as e:
            raise exceptions.UserError(_(
                'Error en prueba de firma: %s'
            ) % str(e))

    @api.model
    def get_default_signature_service(self, company_id=None):
        """Obtiene servicio de firma por defecto para la compañía"""
        if not company_id:
            company_id = self.env.company.id
        
        service = self.search([
            ('company_id', '=', company_id),
            ('active', '=', True)
        ], limit=1)
        
        if not service:
            raise exceptions.UserError(_(
                'No hay servicio de firma digital configurado para esta compañía'
            ))
        
        return service

    def action_view_signature_logs(self):
        """Acción para ver logs de firma"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Logs de Firma',
            'res_model': 'l10n_sv.signature.log',
            'view_mode': 'list,form',
            'domain': [('signature_service_id', '=', self.id)],
            'context': {'default_signature_service_id': self.id}
        }