# -*- coding: utf-8 -*-
{
    'name': 'El Salvador - Payment Terms DGII',
    'version': '18.0.1.0.2',
    'summary': 'Extensión de Términos de Pago para El Salvador',
    'description': """
Este módulo extiende el modelo account.payment.term añadiendo el campo plazo
para la clasificación según la Dirección General de Impuestos Internos de El Salvador.
Implementa el catálogo CAT_018_Plazo con opciones: Días, Meses, Años.
""",
    'author': 'miliky',
    'maintainer': 'José Emilio Flores Meléndez',
    'website': 'https://github.com/miliky/odoo18',
    'category': 'Accounting/Localizations',
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'price': 0.0,
    'currency': 'USD',
    'depends': ['account'],
    'data': [
        'views/account_payment_term_views.xml',
        'data/payment_term_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}