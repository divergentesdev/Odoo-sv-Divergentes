# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('sv')
    def _get_sv_template_data(self):
        return {
            'property_account_receivable_id': 'sv_110200',
            'property_account_payable_id': 'sv_210200',
            'property_account_expense_categ_id': 'sv_520100',
            'property_account_income_categ_id': 'sv_410100',
        }

    @template('sv', 'res.company')
    def _get_sv_res_company(self):
        return {
            self.env.company.id: {
                'anglo_saxon_accounting': False,
                'account_fiscal_country_id': 'base.sv',
                'cash_account_code_prefix': '110101',
                'bank_account_code_prefix': '110102',
                'transfer_account_code_prefix': '110103',
                'account_default_pos_receivable_account_id': 'sv_110201',
                'income_currency_exchange_account_id': 'sv_410300',
                'expense_currency_exchange_account_id': 'sv_520600',
                'account_journal_early_pay_discount_loss_account_id': 'sv_510400',
                'account_journal_early_pay_discount_gain_account_id': 'sv_410600',
                'account_sale_tax_id': 'l10n_sv_cta.tax_iva_13_venta',
                'account_purchase_tax_id': 'l10n_sv_cta.tax_iva_13_compra',
                'default_cash_difference_income_account_id': 'sv_410400',
                'default_cash_difference_expense_account_id': 'sv_520700',
            },
        }
