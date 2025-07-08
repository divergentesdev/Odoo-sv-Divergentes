# -*- coding: utf-8 -*-
{
    'name': 'El Salvador - Incoterms DGII',
    'version': '18.0.1.0.0',
    'summary': 'Extensión de Incoterms para El Salvador',
    'description': """
Este módulo extiende el modelo account.incoterms añadiendo el campo code_dgii
para la clasificación según la Dirección General de Impuestos Internos de El Salvador.
""",
    'author': 'miliky',
    'maintainer': 'José Emilio Flores Meléndez',
    'website': 'https://github.com/miliky/odoo18',
    'category': 'Localization',
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'support': 'jefm@outlook.com',
    'price': 0.0,
    'currency': 'USD',
    'depends': ['account'],
    'data': [
        'views/account_incoterms_views.xml',
        'data/incoterms_data.xml',
    ],
    'installable': True,
    'application': False,
}