# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'El Salvador - Accounting',
    'icon': '/account/static/description/l10n.png',
    'countries': ['sv'],
    'version': '18.0.1.0.4',
    'category': 'Accounting/Localizations/Account Charts',
    'description': 'Salvadorian Accounting and Tax Preconfiguration',
    'author': 'miliky',
    'maintainer': 'José Emilio flores Meléndez',
    'website': 'https://github.com/miliky/odoo18',
    'images': ['static/description/banner.jpg'],
    'price': 0.0,
    'currency': 'USD',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'data/res_currency_data.xml',
        'views/account_tax_views.xml',
    ],
    'auto_install': ['account'],
    # 'demo': [
    #     'demo/demo_company.xml',
    # ],
    'license': 'LGPL-3',
}
