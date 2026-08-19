# -*- coding: utf-8 -*-
{
    'name': 'El Salvador - Payment Methods for Electronic Billing',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
El Salvador - Payment Methods (CAT_021_Forma_Pago)
===================================================

Este módulo implementa el catálogo oficial CAT_021_Forma_Pago del Ministerio de Hacienda de El Salvador.

Características:
----------------
* Formas de pago oficiales según normativa MH
* Integración con facturación electrónica DTE
* Campo formaPago en resumen de documentos electrónicos
* Configuración automática al instalar

Formas de Pago Incluidas:
-------------------------
* 01 - Contado
* 02 - Crédito
* 03 - Mixto

Requerido para facturación electrónica vigente desde diciembre 2025.
    """,
    'author': 'Odoo SA, Contribuyentes Locales',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'l10n_sv_edi_json',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_method_data.xml',
        'views/payment_method_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
