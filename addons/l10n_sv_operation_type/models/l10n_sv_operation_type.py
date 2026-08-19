# -*- coding: utf-8 -*-

from odoo import models, fields, api


class L10nSvOperationType(models.Model):
    """
    Modelo para el catálogo CAT_023_TipoOperacion del Ministerio de Hacienda de El Salvador.
    
    Este modelo implementa los tipos de operación oficiales requeridos para la facturación
    electrónica vigente desde diciembre 2025.
    
    Catálogo CAT_023_TipoOperacion:
    - 1: Operaciones Internas (gravadas y no gravadas)
    - 2: Exportaciones
    """
    _name = 'l10n_sv.operation.type'
    _description = 'El Salvador Operation Type (CAT_023)'
    _order = 'sequence, code'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, size=1, help='Código de 1 dígito según catálogo MH')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description', translate=True)

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'El código de tipo de operación debe ser único.'),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals_list):
        # Asegurar que el código tenga 1 dígito
        if isinstance(vals_list, list):
            for vals in vals_list:
                if vals.get('code'):
                    vals['code'] = vals['code'].zfill(1)
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('code'):
            vals['code'] = vals['code'].zfill(1)
        return super().write(vals)


class AccountMove(models.Model):
    """Extender account.move para agregar campo tipoOperacion"""
    _inherit = 'account.move'

    l10n_sv_operation_type_id = fields.Many2one(
        'l10n_sv.operation.type',
        string='Operation Type (CAT_023)',
        help='Tipo de operación según catálogo CAT_023 del Ministerio de Hacienda',
        copy=False,
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_for_operation_type(self):
        """Determinar automáticamente el tipo de operación según el partner"""
        if self.partner_id and self.move_type in ['out_invoice', 'out_refund']:
            operation_type_model = self.env['l10n_sv.operation.type']
            
            # Si el partner es extranjero, es exportación (2)
            if self.partner_id.country_id and self.partner_id.country_id.code != 'SV':
                export_method = operation_type_model.search([('code', '=', '2')], limit=1)
                if export_method:
                    self.l10n_sv_operation_type_id = export_method.id
            else:
                # Si es nacional, es operaciones internas (1)
                internal_method = operation_type_model.search([('code', '=', '1')], limit=1)
                if internal_method:
                    self.l10n_sv_operation_type_id = internal_method.id

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move, vals in zip(moves, vals_list):
            # Si no se especificó tipo de operación, intentar determinarlo automáticamente
            if not move.l10n_sv_operation_type_id and move.move_type in ['out_invoice', 'out_refund']:
                move._onchange_partner_id_for_operation_type()
        return moves
