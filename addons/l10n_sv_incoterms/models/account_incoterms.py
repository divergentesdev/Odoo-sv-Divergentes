# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountIncoterms(models.Model):
    _inherit = 'account.incoterms'

    code_dgii = fields.Char(
        string="Código DGII",
        help="Código utilizado por la Dirección General de Impuestos Internos de El Salvador"
    )