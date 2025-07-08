# -*- coding: utf-8 -*-

from odoo import models, fields, api
    
class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _set_default_country(self):
        return self.env.company.country_id.id

    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=_set_default_country)

    @api.onchange('state_id')
    def _onchange_state_id(self):
        """Al cambiar el municipio, seleccionar automáticamente el primer distrito disponible"""
        if self.state_id and self.country_id and self.country_id.code == 'SV':
            # Limpiar el valor actual de city_id para evitar mantener valores incorrectos
            self.city_id = False
            self.city = False
            
            # Buscar el primer distrito disponible para el municipio seleccionado
            first_city = self.env['res.city'].search([
                ('state_id', '=', self.state_id.id)
            ], limit=1)
            
            if first_city:
                self.city_id = first_city.id
                self.city = first_city.name