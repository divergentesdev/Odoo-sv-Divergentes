{
    'name': 'El Salvador - Posiciones Fiscales DTE',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Posiciones fiscales automáticas para El Salvador según normativa DTE',
    'description': '''
El Salvador - Posiciones Fiscales DTE
=====================================

Este módulo implementa las posiciones fiscales específicas para El Salvador 
según la normativa del Ministerio de Hacienda para Documentos Tributarios Electrónicos (DTE).

Características principales:
---------------------------
* Posiciones fiscales automáticas según tipo de contribuyente
* Mapeo automático de impuestos (IVA, retenciones, FOVIAL, COTRANS)
* Determinación automática de tipo de documento DTE
* Aplicación automática de retenciones según normativa
* Integración completa con módulos EDI existentes

Posiciones fiscales incluidas:
------------------------------
* Consumidor Final → Factura (01)
* Contribuyente con NIT → CCF (03)
* Exportación → Factura de Exportación (11)
* Sujeto Excluido → Factura de Sujeto Excluido (14)
* Agente Retenedor → Aplicación automática de retenciones

Impuestos configurados:
-----------------------
* IVA 13% para operaciones gravadas
* Exención IVA para exportaciones y sujetos excluidos
* Retenciones de renta (1%, 5%, 10%)
* Retenciones de IVA (1%)
* FOVIAL, COTRANS según corresponda
* Impuesto al turismo 5%

Automatización:
---------------
* Asignación automática de posición fiscal según partner
* Aplicación automática de impuestos según operación
* Determinación automática de documento DTE
* Cálculo automático de retenciones
''',
    'author': 'Divergentes Media S.A.S. de C.V.',
    'website': 'https://www.divergentesmedia.com',
    'maintainer': 'Divergentes Media S.A.S. de C.V.',
    'support': 'info@divergentesmedia.com',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_sv_cta',
        'l10n_sv_document_type',
        'l10n_sv_edi_base',
        'l10n_latam_sv'
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'data/account_fiscal_position_data.xml',  # Creadas dinámicamente en post_init_hook
        'data/account_tax_data_simple.xml',  # Impuestos básicos sin campos personalizados
        'views/account_fiscal_position_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
    ],
    # 'demo': [
    #     'demo/fiscal_position_demo.xml'
    # ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': '_setup_fiscal_positions',
}