# -*- coding: utf-8 -*-
from odoo import fields, models


class UomUom(models.Model):
    _inherit = 'uom.uom'

    code = fields.Integer(
        string="Código",
        help="Código utilizado para identificar la unidad de medida según normativa salvadoreña"
    )