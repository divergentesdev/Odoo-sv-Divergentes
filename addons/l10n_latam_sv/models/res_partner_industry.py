# -*- coding: utf-8 -*-
from odoo import fields, models

class ResPartnerIndustry(models.Model):
    _inherit = 'res.partner.industry'
    
    code = fields.Char(string='Código', size=10, help='Código identificador del giro')