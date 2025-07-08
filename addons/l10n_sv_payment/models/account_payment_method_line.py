# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountPaymentMethodLine(models.Model):
    _inherit = 'account.payment.method.line'
    
    formasDePagos = fields.Selection([
        ('01', 'Efectivo'),
        ('02', 'Tarjeta Débito'),
        ('03', 'Tarjeta Crédito'),
        ('04', 'Cheque'),
        ('05', 'Transferencia'),
        ('06', 'Depósito en Cuenta'),
        ('07', 'Giro Bancario'),
        ('08', 'Letra de Cambio'),
        ('09', 'Nota de Crédito'),
        ('10', 'Nota de Débito'),
        ('11', 'Voucher'),
        ('12', 'Bono o Certificado de Regalo'),
        ('13', 'Pago por Aplicación Móvil'),
        ('14', 'Dinero Electrónico'),
        ('15', 'Monedero Electrónico'),
        ('16', 'Pago por Internet')
    ], string="Forma de Pago DGII", 
       help="Código de forma de pago según catálogo de la Dirección General de Impuestos Internos de El Salvador")