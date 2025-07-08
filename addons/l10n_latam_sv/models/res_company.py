# -*- coding: utf-8 -*-
from odoo import fields, models, api

class ResCompanyLO(models.Model):
	_inherit = 'res.company'

	nombre_comercial = fields.Char(string='Nombre Comercial', help='Nombre comercial de la empresa, diferente a la razón social')
	industry_id = fields.Many2one('res.partner.industry', string='Giro', help='Actividad Económica')
	nit_9 = fields.Char(string='NIT homologado', size=9, help='Numero del DUI de la persona natural')
	is_withholding_agent = fields.Boolean(string='Es agente de retención', default=False, 
		help='Indica si la compañía es un agente de retención de impuestos')
	
	@api.onchange('industry_id')
	def _change_data_fiscal(self):
		if self.partner_id:
			self.partner_id.write({
				'industry_id': self.industry_id,
			})
	
	@api.model_create_multi
	def create(self, vals_list):
		companies = super(ResCompanyLO, self).create(vals_list)
		for company in companies:
			if company.industry_id and company.partner_id:
				company.partner_id.write({
					'industry_id': company.industry_id.id,
				})
		return companies
	
	def write(self, vals):
		result = super(ResCompanyLO, self).write(vals)
		if 'industry_id' in vals and self.partner_id:
			self.partner_id.write({
				'industry_id': self.industry_id.id,
			})
		return result
	
	@api.onchange('is_withholding_agent')
	def _onchange_is_withholding_agent(self):
		if self.partner_id:
			self.partner_id.write({
				'is_withholding_agent': self.is_withholding_agent,
			})
	