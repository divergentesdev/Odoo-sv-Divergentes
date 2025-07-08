# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountTax(models.Model):
    _inherit = 'account.tax'
    
    # Campos personalizados para El Salvador
    l10n_sv_is_withholding = fields.Boolean(
        string='Es Retención',
        help='Marcar si este impuesto es una retención'
    )
    
    l10n_sv_withholding_type = fields.Selection([
        ('income', 'Retención de Renta'),
        ('vat', 'Retención de IVA'),
    ], string='Tipo de Retención',
        help='Tipo de retención que aplica este impuesto'
    )