# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    plazo = fields.Selection([
        ('01', 'Días'),
        ('02', 'Meses'),
        ('03', 'Años')
    ], string="Código DGII", 
       help="Código utilizado por la Dirección General de Impuestos Internos de El Salvador según catálogo CAT_018_Plazo")
    
    periodo = fields.Integer(
        string="Valor DGII",
        help="Valor numérico asociado al plazo para la Dirección General de Impuestos Internos de El Salvador"
    )