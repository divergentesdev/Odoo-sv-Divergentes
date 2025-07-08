# -*- coding: utf-8 -*-
{
    'name': 'El Salvador - Units of measurement',
    'version': '18.0.1.0.2',
    'summary': 'Extensión de Unidades de Medida para El Salvador',
    'description': """
Este módulo extiende el modelo uom.uom añadiendo el campo code
para la identificación según normativa de El Salvador (CAT_014_Unidad_de_Medida).
""",
    'author': 'miliky',
    'maintainer': 'José Emilio Flores Meléndez',
    'website': 'https://github.com/miliky/odoo18',
    'category': 'Inventory/Localizations',
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'price': 0.0,
    'currency': 'USD',
    'depends': ['uom'],
    'data': [
        'views/uom_views.xml',
        'data/uom_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}