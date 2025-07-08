import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class L10nSvSignatureAlgorithm(models.Model):
    """Algoritmos de firma digital soportados"""
    _name = 'l10n_sv.signature.algorithm'
    _description = 'Algoritmos de Firma Digital'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre del algoritmo de firma'
    )
    
    code = fields.Char(
        string='Código',
        required=True,
        help='Código técnico del algoritmo'
    )
    
    hash_algorithm = fields.Selection([
        ('sha1', 'SHA-1'),
        ('sha256', 'SHA-256'),
        ('sha384', 'SHA-384'),
        ('sha512', 'SHA-512'),
        ('md5', 'MD5')
    ], string='Algoritmo Hash', required=True,
       help='Algoritmo de hash utilizado')
    
    key_type = fields.Selection([
        ('rsa', 'RSA'),
        ('dsa', 'DSA'),
        ('ecdsa', 'ECDSA'),
        ('ed25519', 'Ed25519')
    ], string='Tipo de Clave', required=True, default='rsa',
       help='Tipo de clave criptográfica')
    
    min_key_size = fields.Integer(
        string='Tamaño Mínimo Clave',
        default=2048,
        help='Tamaño mínimo de clave en bits'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción del algoritmo y su uso'
    )
    
    # Compatibilidad con estándares
    xmldsig_compatible = fields.Boolean(
        string='Compatible XML-DSig',
        default=True,
        help='Compatible con XML Digital Signature'
    )
    
    jose_compatible = fields.Boolean(
        string='Compatible JOSE',
        default=True,
        help='Compatible con JSON Object Signing and Encryption'
    )
    
    pkcs7_compatible = fields.Boolean(
        string='Compatible PKCS#7',
        default=True,
        help='Compatible con PKCS#7/CMS'
    )
    
    # Información técnica
    oid = fields.Char(
        string='OID',
        help='Object Identifier del algoritmo'
    )
    
    uri = fields.Char(
        string='URI',
        help='URI estándar del algoritmo (para XML-DSig)'
    )
    
    jose_alg = fields.Char(
        string='JOSE Algorithm',
        help='Identificador del algoritmo en JOSE/JWT'
    )
    
    # Validación de seguridad
    security_level = fields.Selection([
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('very_high', 'Muy Alto')
    ], string='Nivel de Seguridad', default='high',
       help='Nivel de seguridad del algoritmo')
    
    deprecated = fields.Boolean(
        string='Deprecado',
        default=False,
        help='Algoritmo deprecado o no recomendado'
    )
    
    deprecation_date = fields.Date(
        string='Fecha de Deprecación',
        help='Fecha en que el algoritmo fue deprecado'
    )
    
    # Uso recomendado
    recommended_for_new = fields.Boolean(
        string='Recomendado para Nuevos',
        default=True,
        help='Recomendado para nuevas implementaciones'
    )
    
    government_approved = fields.Boolean(
        string='Aprobado por Gobierno',
        default=False,
        help='Aprobado por autoridades gubernamentales'
    )

    @api.constrains('code')
    def _check_unique_code(self):
        """Asegura que el código sea único"""
        for algorithm in self:
            if self.search_count([('code', '=', algorithm.code), ('id', '!=', algorithm.id)]) > 0:
                raise exceptions.ValidationError(_(
                    'Ya existe un algoritmo con el código %s'
                ) % algorithm.code)

    @api.constrains('min_key_size', 'key_type')
    def _check_key_size(self):
        """Valida tamaño mínimo de clave según tipo"""
        for algorithm in self:
            if algorithm.key_type == 'rsa' and algorithm.min_key_size < 1024:
                raise exceptions.ValidationError(_(
                    'RSA requiere tamaño mínimo de clave de 1024 bits'
                ))
            elif algorithm.key_type == 'dsa' and algorithm.min_key_size < 1024:
                raise exceptions.ValidationError(_(
                    'DSA requiere tamaño mínimo de clave de 1024 bits'
                ))

    def get_cryptography_hash(self):
        """Obtiene objeto hash de cryptography"""
        self.ensure_one()
        
        try:
            from cryptography.hazmat.primitives import hashes
            
            hash_map = {
                'sha1': hashes.SHA1(),
                'sha256': hashes.SHA256(),
                'sha384': hashes.SHA384(),
                'sha512': hashes.SHA512(),
                'md5': hashes.MD5()
            }
            
            return hash_map.get(self.hash_algorithm)
            
        except ImportError:
            raise exceptions.UserError(_(
                'Librería cryptography no disponible'
            ))

    def get_xmlsec_transform(self):
        """Obtiene transform de xmlsec"""
        self.ensure_one()
        
        try:
            import xmlsec
            
            transform_map = {
                'rsa_sha1': xmlsec.Transform.RSA_SHA1,
                'rsa_sha256': xmlsec.Transform.RSA_SHA256,
                'rsa_sha384': xmlsec.Transform.RSA_SHA384,
                'rsa_sha512': xmlsec.Transform.RSA_SHA512,
                'dsa_sha1': xmlsec.Transform.DSA_SHA1,
                'dsa_sha256': xmlsec.Transform.DSA_SHA256
            }
            
            key = f"{self.key_type}_{self.hash_algorithm}"
            return transform_map.get(key)
            
        except ImportError:
            raise exceptions.UserError(_(
                'Librería xmlsec no disponible'
            ))

    def validate_certificate_compatibility(self, certificate):
        """Valida que un certificado sea compatible con este algoritmo"""
        self.ensure_one()
        
        try:
            from cryptography import x509
            
            # Obtener información de la clave pública del certificado
            public_key = certificate.public_key()
            
            # Verificar tipo de clave
            if self.key_type == 'rsa':
                from cryptography.hazmat.primitives.asymmetric import rsa
                if not isinstance(public_key, rsa.RSAPublicKey):
                    return False, _('Certificado no es RSA')
                
                # Verificar tamaño de clave
                if public_key.key_size < self.min_key_size:
                    return False, _('Tamaño de clave insuficiente: %d < %d') % (
                        public_key.key_size, self.min_key_size
                    )
                    
            elif self.key_type == 'dsa':
                from cryptography.hazmat.primitives.asymmetric import dsa
                if not isinstance(public_key, dsa.DSAPublicKey):
                    return False, _('Certificado no es DSA')
                    
            elif self.key_type == 'ecdsa':
                from cryptography.hazmat.primitives.asymmetric import ec
                if not isinstance(public_key, ec.EllipticCurvePublicKey):
                    return False, _('Certificado no es ECDSA')
            
            return True, _('Certificado compatible')
            
        except Exception as e:
            return False, _('Error validando compatibilidad: %s') % str(e)

    @api.model
    def get_recommended_algorithms(self):
        """Obtiene algoritmos recomendados para uso actual"""
        return self.search([
            ('active', '=', True),
            ('deprecated', '=', False),
            ('recommended_for_new', '=', True),
            ('security_level', 'in', ['high', 'very_high'])
        ])

    @api.model
    def get_government_approved_algorithms(self):
        """Obtiene algoritmos aprobados por el gobierno"""
        return self.search([
            ('active', '=', True),
            ('government_approved', '=', True)
        ])

    def action_view_signatures(self):
        """Acción para ver firmas que usan este algoritmo"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Firmas con Algoritmo %s') % self.name,
            'res_model': 'l10n_sv.digital.signature',
            'view_mode': 'tree,form',
            'domain': [('algorithm_id', '=', self.id)]
        }

    def action_view_signature_logs(self):
        """Acción para ver logs de firmas con este algoritmo"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Logs de Firmas - %s') % self.name,
            'res_model': 'l10n_sv.signature.log',
            'view_mode': 'tree,form',
            'domain': [('algorithm_used', '=', self.name)]
        }

    @api.model
    def setup_default_algorithms(self):
        """Configura algoritmos por defecto"""
        
        default_algorithms = [
            {
                'name': 'RSA-SHA256',
                'code': 'RSA_SHA256',
                'hash_algorithm': 'sha256',
                'key_type': 'rsa',
                'min_key_size': 2048,
                'security_level': 'high',
                'description': 'RSA con SHA-256 - Recomendado para la mayoría de usos',
                'oid': '1.2.840.113549.1.1.11',
                'uri': 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256',
                'jose_alg': 'RS256',
                'government_approved': True,
                'recommended_for_new': True
            },
            {
                'name': 'RSA-SHA512',
                'code': 'RSA_SHA512',
                'hash_algorithm': 'sha512',
                'key_type': 'rsa',
                'min_key_size': 2048,
                'security_level': 'very_high',
                'description': 'RSA con SHA-512 - Máxima seguridad',
                'oid': '1.2.840.113549.1.1.13',
                'uri': 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha512',
                'jose_alg': 'RS512',
                'government_approved': True,
                'recommended_for_new': True
            },
            {
                'name': 'RSA-SHA1',
                'code': 'RSA_SHA1',
                'hash_algorithm': 'sha1',
                'key_type': 'rsa',
                'min_key_size': 1024,
                'security_level': 'medium',
                'description': 'RSA con SHA-1 - Compatibilidad con sistemas legacy',
                'oid': '1.2.840.113549.1.1.5',
                'uri': 'http://www.w3.org/2000/09/xmldsig#rsa-sha1',
                'jose_alg': 'RS1',
                'deprecated': True,
                'recommended_for_new': False,
                'deprecation_date': '2020-01-01'
            }
        ]
        
        for alg_data in default_algorithms:
            # Verificar si ya existe
            existing = self.search([('code', '=', alg_data['code'])])
            if not existing:
                self.create(alg_data)
                _logger.info(f"Algoritmo creado: {alg_data['name']}")

    @api.model
    def get_best_algorithm_for_certificate(self, certificate):
        """Obtiene el mejor algoritmo para un certificado dado"""
        recommended = self.get_recommended_algorithms()
        
        for algorithm in recommended:
            compatible, message = algorithm.validate_certificate_compatibility(certificate)
            if compatible:
                return algorithm
        
        # Si no hay compatibles en recomendados, buscar en todos
        all_algorithms = self.search([('active', '=', True)])
        for algorithm in all_algorithms:
            compatible, message = algorithm.validate_certificate_compatibility(certificate)
            if compatible:
                return algorithm
        
        raise exceptions.UserError(_(
            'No se encontró algoritmo compatible con el certificado'
        ))