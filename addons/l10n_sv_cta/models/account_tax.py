# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    code_dgii = fields.Char(
        string="Código DGII",
        help="Código utilizado por la Dirección General de Impuestos Internos de El Salvador"
    )