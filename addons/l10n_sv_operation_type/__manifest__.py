# -*- coding: utf-8 -*-
{
    'name': 'El Salvador - Operation Types for Electronic Billing',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
El Salvador - Operation Types (CAT_023_TipoOperacion)
=====================================================

Este módulo implementa el catálogo oficial CAT_023_TipoOperacion del Ministerio de Hacienda de El Salvador.

Características:
----------------
* Tipos de operación oficiales según normativa MH
* Integración con facturación electrónica DTE
* Campo tipoOperacion en resumen de documentos electrónicos
* Determinación automática según país del partner
* Configuración automática al instalar

Tipos de Operación Incluidos:
------------------------------
* 1 - Operaciones Internas (gravadas y no gravadas)
* 2 - Exportaciones

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
        'data/operation_type_data.xml',
        'views/operation_type_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
