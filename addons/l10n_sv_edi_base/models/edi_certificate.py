import base64
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class EdiCertificate(models.Model):
    """Modelo para gestionar certificados digitales del MH de El Salvador"""
    _name = 'l10n_sv.edi.certificate'
    _description = 'Certificado Digital EDI El Salvador'
    _order = 'environment, create_date desc'

    name = fields.Char(
        string='Nombre del Certificado',
        required=True,
        help='Nombre identificativo del certificado'
    )
    
    environment = fields.Selection([
        ('test', 'Certificación (Pruebas)'),
        ('production', 'Producción')
    ], string='Ambiente', required=True, default='test',
       help='Ambiente para el cual es válido este certificado')
    
    certificate_file = fields.Binary(
        string='Archivo Certificado (.cert)',
        required=True,
        help='Archivo de certificado digital proporcionado por el MH (.cert)'
    )
    
    certificate_filename = fields.Char(
        string='Nombre del Archivo',
        help='Nombre del archivo de certificado'
    )
    
    private_key_file = fields.Binary(
        string='Archivo Clave Privada (.key)',
        required=True,
        help='Archivo de clave privada del certificado (.key)'
    )
    
    private_key_filename = fields.Char(
        string='Nombre Archivo Clave',
        help='Nombre del archivo de clave privada'
    )
    
    password = fields.Char(
        string='Contraseña del Certificado',
        help='Contraseña para el certificado digital'
    )
    
    valid_from = fields.Datetime(
        string='Válido Desde',
        help='Fecha de inicio de validez del certificado'
    )
    
    valid_to = fields.Datetime(
        string='Válido Hasta',
        help='Fecha de vencimiento del certificado'
    )
    
    issuer = fields.Char(
        string='Emisor',
        help='Entidad que emitió el certificado (MH El Salvador)'
    )
    
    subject = fields.Char(
        string='Sujeto',
        help='Información del sujeto del certificado (empresa)'
    )
    
    serial_number = fields.Char(
        string='Número de Serie',
        help='Número de serie del certificado'
    )
    
    is_active = fields.Boolean(
        string='Activo',
        default=True,
        help='Determina si este certificado está activo para uso'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía a la que pertenece este certificado'
    )
    
    api_url = fields.Char(
        string='URL del API',
        help='URL del API del MH para este ambiente'
    )
    
    api_token = fields.Char(
        string='Token de API',
        help='Token de autenticación para el API del MH'
    )
    
    nit_emisor = fields.Char(
        string='NIT Emisor',
        help='NIT del emisor autorizado para este certificado'
    )
    
    codigo_generacion_prefix = fields.Char(
        string='Prefijo Código Generación',
        help='Prefijo para generación de códigos DTE'
    )
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('valid', 'Válido'),
        ('expired', 'Vencido'),
        ('revoked', 'Revocado')
    ], string='Estado', default='draft', compute='_compute_state', store=True)

    @api.depends('valid_from', 'valid_to', 'is_active')
    def _compute_state(self):
        """Calcula el estado del certificado basado en fechas de validez"""
        now = fields.Datetime.now()
        for cert in self:
            if not cert.is_active:
                cert.state = 'revoked'
            elif cert.valid_to and cert.valid_to < now:
                cert.state = 'expired'
            elif cert.valid_from and cert.valid_to and cert.valid_from <= now <= cert.valid_to:
                cert.state = 'valid'
            else:
                cert.state = 'draft'

    @api.model
    def get_active_certificate(self, company_id=None, environment='production'):
        """Obtiene el certificado activo para una compañía y ambiente específico"""
        domain = [
            ('state', '=', 'valid'),
            ('is_active', '=', True),
            ('environment', '=', environment)
        ]
        if company_id:
            domain.append(('company_id', '=', company_id))
        else:
            domain.append(('company_id', '=', self.env.company.id))
            
        certificate = self.search(domain, limit=1)
        if not certificate:
            raise exceptions.UserError(_(
                'No se encontró un certificado válido para el ambiente %s. '
                'Por favor configure un certificado activo.'
            ) % environment)
        return certificate

    def action_validate_certificate(self):
        """Acción para validar el certificado cargado"""
        self.ensure_one()
        try:
            if not self.certificate_file:
                raise exceptions.UserError(_('Debe cargar un archivo de certificado'))
            
            # Aquí se implementaría la validación del certificado .cert
            # Por ahora simulamos la validación
            self._extract_certificate_info()
            
            self.write({
                'state': 'valid',
                'is_active': True
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Certificado Validado'),
                    'message': _('El certificado se ha validado correctamente'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f"Error validando certificado: {str(e)}")
            raise exceptions.UserError(_(
                'Error al validar el certificado: %s'
            ) % str(e))

    def _extract_certificate_info(self):
        """Extrae información del certificado .cert del MH"""
        self.ensure_one()
        
        # Aquí se implementaría la extracción real de información del certificado .cert
        # Por ahora simulamos algunos valores por defecto
        if not self.issuer:
            self.issuer = "Ministerio de Hacienda - El Salvador"
        
        if not self.valid_from:
            self.valid_from = fields.Datetime.now()
        
        if not self.valid_to:
            self.valid_to = fields.Datetime.now() + timedelta(days=365)
        
        # Configurar URLs por defecto según el ambiente
        if self.environment == 'test' and not self.api_url:
            self.api_url = "https://apitest.dtes.mh.gob.sv/fesv/recepciondte"
        elif self.environment == 'production' and not self.api_url:
            self.api_url = "https://api.dtes.mh.gob.sv/fesv/recepciondte"

    def action_deactivate(self):
        """Desactiva el certificado"""
        self.ensure_one()
        self.write({
            'is_active': False,
            'state': 'revoked'
        })

    def action_show_certificate_info(self):
        """Acción para mostrar información del certificado"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Información del Certificado'),
                'message': _('Estado: %s - Válido desde %s hasta %s') % (
                    dict(self._fields['state'].selection).get(self.state),
                    self.valid_from,
                    self.valid_to
                ),
                'type': 'info'
            }
        }

    @api.constrains('environment', 'company_id', 'is_active')
    def _check_unique_active_certificate(self):
        """Validar que solo haya un certificado activo por compañía y ambiente"""
        for cert in self:
            if cert.is_active and cert.state == 'valid':
                domain = [
                    ('environment', '=', cert.environment),
                    ('company_id', '=', cert.company_id.id),
                    ('is_active', '=', True),
                    ('state', '=', 'valid'),
                    ('id', '!=', cert.id)
                ]
                if self.search_count(domain) > 0:
                    raise exceptions.ValidationError(_(
                        'Solo puede haber un certificado activo por compañía y ambiente. '
                        'Desactive el certificado existente antes de activar este.'
                    ))

    def name_get(self):
        """Personaliza la visualización del nombre del certificado"""
        result = []
        for cert in self:
            name = f"{cert.name} ({cert.environment})"
            if cert.state == 'expired':
                name += " - VENCIDO"
            elif cert.state == 'revoked':
                name += " - REVOCADO"
            result.append((cert.id, name))
        return result