# -*- coding: utf-8 -*-
{
    'name': 'El Salvador - Cities',
    'version': '18.0.1.0.2',
    'summary': 'Municipalities / Districts for El Salvador',
    'description': """
Este módulo añade los Municipios y Distritos de El Salvador al módulo base_address_extended.
Oculta el campo de código postal (zip) cuando el país seleccionado es El Salvador.
Útil para localización y gestión geográfica en Odoo.
""",
    'author': 'miliky',
    'maintainer': 'José Emilio flores Meléndez',
    'website': 'https://github.com/miliky/odoo18',
    'category': 'Localization',
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'support': 'jefm@outlook.com',
    'price': 0.0,
    'currency': 'USD',
    'depends': ['base', 'base_address_extended', 'contacts'],
    'data': [
        'data/res_state_data.xml',
        'data/res_city_data.xml',
        'data/res_country_data.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
}
