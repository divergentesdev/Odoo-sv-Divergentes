# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nSvPaymentMethod(models.Model):
    """
    Modelo para el catálogo CAT_021_Forma_Pago del Ministerio de Hacienda de El Salvador.
    
    Este modelo implementa las formas de pago oficiales requeridas para la facturación
    electrónica vigente desde diciembre 2025.
    
    Catálogo CAT_021_Forma_Pago:
    - 01: Contado
    - 02: Crédito  
    - 03: Mixto
    """
    _name = 'l10n_sv.payment.method'
    _description = 'El Salvador Payment Method (CAT_021)'
    _order = 'sequence, code'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, size=2, help='Código de 2 dígitos según catálogo MH')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description', translate=True)

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'El código de forma de pago debe ser único.'),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals_list):
        # Asegurar que el código tenga 2 dígitos
        if isinstance(vals_list, list):
            for vals in vals_list:
                if vals.get('code'):
                    vals['code'] = vals['code'].zfill(2)
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('code'):
            vals['code'] = vals['code'].zfill(2)
        return super().write(vals)


class AccountMove(models.Model):
    """Extender account.move para agregar campo formaPago"""
    _inherit = 'account.move'

    l10n_sv_payment_method_id = fields.Many2one(
        'l10n_sv.payment.method',
        string='Payment Method (CAT_021)',
        help='Forma de pago según catálogo CAT_021 del Ministerio de Hacienda',
        copy=False,
    )

    @api.onchange('invoice_payment_term_id')
    def _onchange_invoice_payment_term_id(self):
        """Determinar automáticamente la forma de pago según las condiciones de pago"""
        if self.invoice_payment_term_id:
            # Verificar si hay líneas con días > 0 (crédito)
            has_credit = any(line.nb_days > 0 for line in self.invoice_payment_term_id.line_ids)
            
            payment_method_model = self.env['l10n_sv.payment.method']
            
            if has_credit:
                # Si tiene crédito, es "Crédito" (02) o "Mixto" (03)
                # Por defecto usamos Crédito
                credit_method = payment_method_model.search([('code', '=', '02')], limit=1)
                if credit_method:
                    self.l10n_sv_payment_method_id = credit_method.id
            else:
                # Si no tiene crédito, es "Contado" (01)
                cash_method = payment_method_model.search([('code', '=', '01')], limit=1)
                if cash_method:
                    self.l10n_sv_payment_method_id = cash_method.id

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move, vals in zip(moves, vals_list):
            # Si no se especificó forma de pago, intentar determinarla automáticamente
            if not move.l10n_sv_payment_method_id and move.invoice_payment_term_id:
                move._onchange_invoice_payment_term_id()
        return moves
