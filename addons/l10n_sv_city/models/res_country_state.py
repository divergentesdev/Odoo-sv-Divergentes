# -*- coding: utf-8 -*-

from odoo import models, api

class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Personaliza la búsqueda de nombres para mostrar primero los municipios de El Salvador"""
        args = args or []
        context = self._context or {}
        
        # Si estamos en el contexto de priorizar El Salvador
        if context.get('sv_first'):
            # Obtener el ID del país El Salvador
            sv_country_id = self.env.ref('base.sv').id
            
            # Obtener el país del contexto si está disponible
            country_id = context.get('country_id')
            
            # Si no hay país seleccionado o el país es El Salvador
            if not country_id or country_id == sv_country_id:
                # Buscar primero los municipios de El Salvador
                sv_states = self.search([('country_id', '=', sv_country_id), 
                                         ('name', operator, name)], limit=limit)
                
                # Obtener los resultados en el formato correcto para name_search
                sv_result = [(state.id, state.name) for state in sv_states]
                
                # Si encontramos todos los resultados necesarios, devolver solo esos
                if len(sv_result) >= limit:
                    return sv_result
                
                # Si necesitamos más resultados, buscar en otros países
                limit2 = limit - len(sv_result)
                if limit2:
                    other_args = args + [('country_id', '!=', sv_country_id)]
                    other_result = super(ResCountryState, self).name_search(
                        name, other_args, operator, limit=limit2)
                    return sv_result + other_result
                
                return sv_result
        
        # Comportamiento estándar si no estamos priorizando El Salvador
        return super(ResCountryState, self).name_search(name, args, operator, limit=limit)