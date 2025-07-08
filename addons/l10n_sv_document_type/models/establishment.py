import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class L10nSvEstablishment(models.Model):
    """Establecimientos y puntos de emisión para DTE"""
    _name = 'l10n_sv.establishment'
    _description = 'Establecimiento DTE El Salvador'
    _order = 'code'

    name = fields.Char(
        string='Nombre del Establecimiento',
        required=True,
        help='Nombre descriptivo del establecimiento'
    )
    
    code = fields.Char(
        string='Código',
        required=True,
        size=4,
        help='Código del establecimiento (4 dígitos)'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía a la que pertenece este establecimiento'
    )
    
    # Información de ubicación usando catálogos existentes
    street = fields.Char(
        string='Dirección',
        help='Dirección del establecimiento'
    )
    
    city_id = fields.Many2one(
        'res.city',
        string='Ciudad/Municipio',
        help='Ciudad del establecimiento'
    )
    
    state_id = fields.Many2one(
        'res.country.state',
        string='Departamento',
        help='Departamento del establecimiento'
    )
    
    country_id = fields.Many2one(
        'res.country',
        string='País',
        default=lambda self: self.env.ref('base.sv'),
        help='País del establecimiento'
    )
    
    # Códigos para DTE usando catálogos l10n_sv_city
    departamento_code = fields.Char(
        string='Código Departamento',
        size=2,
        help='Código del departamento según catálogo MH'
    )
    
    municipio_code = fields.Char(
        string='Código Municipio',
        size=2,
        help='Código del municipio según catálogo MH'
    )
    
    # Puntos de venta asociados
    point_of_sale_ids = fields.One2many(
        'l10n_sv.point.of.sale',
        'establishment_id',
        string='Puntos de Venta'
    )
    
    # Configuración de secuencias por tipo de documento
    sequence_config_ids = fields.One2many(
        'l10n_sv.establishment.sequence',
        'establishment_id',
        string='Configuración de Secuencias'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Determina si este establecimiento está activo'
    )
    
    is_main = fields.Boolean(
        string='Establecimiento Principal',
        default=False,
        help='Indica si este es el establecimiento principal'
    )

    def action_show_establishment_info(self):
        """Acción para mostrar información del establecimiento"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Establecimiento: {self.code}',
            'view_mode': 'form',
            'res_model': 'l10n_sv.establishment',
            'res_id': self.id,
            'target': 'new',
        }

    def action_view_points_of_sale(self):
        """Acción para ver puntos de venta del establecimiento"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Puntos de Venta - {self.name}',
            'view_mode': 'list,form',
            'res_model': 'l10n_sv.point.of.sale',
            'domain': [('establishment_id', '=', self.id)],
            'context': {'default_establishment_id': self.id},
        }

    @api.onchange('city_id')
    def _onchange_city_id(self):
        """Actualiza códigos de departamento y municipio al cambiar ciudad"""
        if self.city_id:
            # Usar el código del distrito de l10n_sv_city
            if hasattr(self.city_id, 'district_code') and self.city_id.district_code:
                district_code = self.city_id.district_code
                if len(district_code) == 4:
                    self.departamento_code = district_code[:2]
                    self.municipio_code = district_code[2:]
            
            # Actualizar estado
            if self.city_id.state_id:
                self.state_id = self.city_id.state_id

    @api.constrains('code', 'company_id')
    def _check_unique_code(self):
        """Validar que el código sea único por compañía"""
        for establishment in self:
            domain = [
                ('code', '=', establishment.code),
                ('company_id', '=', establishment.company_id.id),
                ('id', '!=', establishment.id)
            ]
            if self.search_count(domain) > 0:
                raise exceptions.ValidationError(_(
                    'Ya existe un establecimiento con el código %s para esta compañía'
                ) % establishment.code)

    @api.constrains('is_main', 'company_id')
    def _check_unique_main(self):
        """Validar que solo haya un establecimiento principal por compañía"""
        for establishment in self:
            if establishment.is_main:
                domain = [
                    ('is_main', '=', True),
                    ('company_id', '=', establishment.company_id.id),
                    ('id', '!=', establishment.id)
                ]
                if self.search_count(domain) > 0:
                    raise exceptions.ValidationError(_(
                        'Solo puede haber un establecimiento principal por compañía'
                    ))

    def name_get(self):
        """Personaliza la visualización del nombre"""
        result = []
        for establishment in self:
            name = f"[{establishment.code}] {establishment.name}"
            result.append((establishment.id, name))
        return result


class L10nSvPointOfSale(models.Model):
    """Puntos de venta dentro de un establecimiento"""
    _name = 'l10n_sv.point.of.sale'
    _description = 'Punto de Venta DTE'
    _order = 'establishment_id, code'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre del punto de venta'
    )
    
    code = fields.Char(
        string='Código',
        required=True,
        size=3,
        help='Código del punto de venta (3 dígitos)'
    )
    
    establishment_id = fields.Many2one(
        'l10n_sv.establishment',
        string='Establecimiento',
        required=True,
        help='Establecimiento al que pertenece este punto de venta'
    )
    
    company_id = fields.Many2one(
        related='establishment_id.company_id',
        string='Compañía',
        store=True
    )
    
    user_ids = fields.Many2many(
        'res.users',
        string='Usuarios Autorizados',
        help='Usuarios que pueden emitir documentos desde este punto de venta'
    )
    
    journal_ids = fields.Many2many(
        'account.journal',
        string='Diarios Contables',
        help='Diarios contables asociados a este punto de venta'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Determina si este punto de venta está activo'
    )

    @api.constrains('code', 'establishment_id')
    def _check_unique_code(self):
        """Validar que el código sea único por establecimiento"""
        for pos in self:
            domain = [
                ('code', '=', pos.code),
                ('establishment_id', '=', pos.establishment_id.id),
                ('id', '!=', pos.id)
            ]
            if self.search_count(domain) > 0:
                raise exceptions.ValidationError(_(
                    'Ya existe un punto de venta con el código %s en este establecimiento'
                ) % pos.code)

    def name_get(self):
        """Personaliza la visualización del nombre"""
        result = []
        for pos in self:
            name = f"[{pos.establishment_id.code}-{pos.code}] {pos.name}"
            result.append((pos.id, name))
        return result


class L10nSvEstablishmentSequence(models.Model):
    """Configuración de secuencias por establecimiento y tipo de documento"""
    _name = 'l10n_sv.establishment.sequence'
    _description = 'Secuencias por Establecimiento'
    _rec_name = 'document_type_id'

    establishment_id = fields.Many2one(
        'l10n_sv.establishment',
        string='Establecimiento',
        required=True
    )
    
    document_type_id = fields.Many2one(
        'l10n_sv.document.type',
        string='Tipo de Documento',
        required=True
    )
    
    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia',
        required=True
    )
    
    last_number = fields.Integer(
        string='Último Número',
        default=0,
        help='Último número emitido para este establecimiento y tipo de documento'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Determina si esta configuración de secuencia está activa'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Crear secuencia automáticamente si no existe"""
        # Crear secuencias antes de crear los registros
        for vals in vals_list:
            if not vals.get('sequence_id'):
                # Crear secuencia temporal para obtener los datos
                establishment_id = vals.get('establishment_id')
                document_type_id = vals.get('document_type_id')
                
                if establishment_id and document_type_id:
                    establishment = self.env['l10n_sv.establishment'].browse(establishment_id)
                    document_type = self.env['l10n_sv.document.type'].browse(document_type_id)
                    
                    sequence_vals = {
                        'name': f'{establishment.name} - {document_type.name}',
                        'code': f'l10n_sv.dte.{establishment.code}.{document_type.code}',
                        'prefix': f'DTE-{document_type.code}-{establishment.code}-',
                        'suffix': '',
                        'padding': 15,
                        'number_next': 1,
                        'number_increment': 1,
                        'implementation': 'standard',
                        'company_id': establishment.company_id.id,
                    }
                    sequence = self.env['ir.sequence'].create(sequence_vals)
                    vals['sequence_id'] = sequence.id
        
        return super().create(vals_list)

    def _create_sequence(self):
        """Crea secuencia específica para establecimiento y tipo de documento"""
        self.ensure_one()
        sequence_vals = {
            'name': f'{self.establishment_id.name} - {self.document_type_id.name}',
            'code': f'l10n_sv.dte.{self.establishment_id.code}.{self.document_type_id.code}',
            'prefix': f'DTE-{self.document_type_id.code}-{self.establishment_id.code}-',
            'suffix': '',
            'padding': 15,
            'number_next': 1,
            'number_increment': 1,
            'implementation': 'standard',
            'company_id': self.establishment_id.company_id.id,
        }
        self.sequence_id = self.env['ir.sequence'].create(sequence_vals)

    def get_next_number(self):
        """Obtiene el siguiente número de la secuencia"""
        self.ensure_one()
        if not self.sequence_id:
            self._create_sequence()
        
        number = self.sequence_id.next_by_id()
        self.last_number = int(number.split('-')[-1]) if '-' in number else 0
        return number

    @api.constrains('establishment_id', 'document_type_id')
    def _check_unique_sequence(self):
        """Validar que no haya secuencias duplicadas"""
        for config in self:
            domain = [
                ('establishment_id', '=', config.establishment_id.id),
                ('document_type_id', '=', config.document_type_id.id),
                ('id', '!=', config.id)
            ]
            if self.search_count(domain) > 0:
                raise exceptions.ValidationError(_(
                    'Ya existe una configuración de secuencia para este establecimiento y tipo de documento'
                ))