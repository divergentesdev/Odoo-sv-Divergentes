{
    'name': 'El Salvador - Tipos de Documentos DTE',
    'version': '18.0.1.0.0',
    'summary': 'Tipos de documentos tributarios electrónicos para El Salvador',
    'description': '''
        Módulo para gestionar los tipos de documentos tributarios electrónicos (DTE)
        según las especificaciones del Ministerio de Hacienda de El Salvador.
        
        Funcionalidades:
        * Catálogo CAT_002_Tipo_de_Documento del MH
        * Secuencias automáticas por tipo de documento
        * Validaciones específicas por tipo DTE
        * Integración con catálogos existentes (UOM, Payment, Incoterms, etc.)
        * Configuración de establecimientos y puntos de emisión
        * Manejo de correlativo por tipo de documento
    ''',
    'category': 'Accounting/Localizations/EDI',
    'author': 'Divergentes Media S.A.S. de C.V.',
    'website': 'https://www.divergentesmedia.com',
    'maintainer': 'Divergentes Media S.A.S. de C.V.',
    'support': 'info@divergentesmedia.com',
    'license': 'LGPL-3',
    'depends': [
        'l10n_sv_edi_base',    # Módulo base EDI
        'l10n_sv_cta',         # Plan de cuentas El Salvador
        'l10n_latam_sv',       # Tipos de identificación
        'l10n_sv_city',        # Municipios
        'l10n_sv_uom',         # Unidades de medida
        'l10n_sv_payment',     # Términos de pago
        'l10n_sv_incoterms',   # Incoterms
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/document_type_data.xml',
        'data/ir_sequence_data.xml',
        'views/document_type_views.xml',
        'views/establishment_views.xml',
        'views/res_company_views.xml',
        'views/account_move_views_improved.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}