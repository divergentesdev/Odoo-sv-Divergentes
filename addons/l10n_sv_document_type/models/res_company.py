from odoo import models, fields


class ResCompany(models.Model):
    """Extiende res.company para agregar establecimientos"""
    _inherit = 'res.company'

    l10n_sv_establishment_ids = fields.One2many(
        'l10n_sv.establishment',
        'company_id',
        string='Establecimientos',
        help='Establecimientos registrados para esta compañía'
    )

    def get_main_establishment(self):
        """Obtiene el establecimiento principal de la compañía"""
        self.ensure_one()
        main_establishment = self.l10n_sv_establishment_ids.filtered('is_main')
        if main_establishment:
            return main_establishment[0]
        elif self.l10n_sv_establishment_ids:
            return self.l10n_sv_establishment_ids[0]
        return False

    def get_default_establishment(self):
        """Obtiene el establecimiento por defecto"""
        return self.get_main_establishment()