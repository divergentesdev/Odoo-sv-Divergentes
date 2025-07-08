{
    'name': 'El Salvador - Reportes DTE',
    'version': '18.0.1.0.0',
    'summary': 'Reportes PDF con códigos QR para documentos tributarios electrónicos de El Salvador',
    'description': '''
        Módulo para generar reportes PDF personalizados de documentos tributarios electrónicos (DTE)
        según las especificaciones del Ministerio de Hacienda de El Salvador.
        
        Funcionalidades:
        * Reportes PDF con diseño oficial DTE El Salvador
        * Códigos QR con información completa del DTE
        * Integración con firma digital y sello del MH
        * Plantillas personalizables por tipo de documento
        * Información de estado EDI y trazabilidad
        * Marcas de agua para estados de documento
        * Códigos de barras adicionales (Code128, EAN13)
        * Exportación en múltiples formatos (PDF, PNG, JPEG)
        * Impresión masiva de documentos DTE
        * Personalización de logos y datos de empresa
        * Cumplimiento con formato oficial MH
    ''',
    'category': 'Accounting/Localizations/EDI',
    'author': 'Divergentes Media S.A.S. de C.V.',
    'website': 'https://www.divergentesmedia.com',
    'maintainer': 'Divergentes Media S.A.S. de C.V.',
    'support': 'info@divergentesmedia.com',
    'license': 'LGPL-3',
    'depends': [
        'l10n_sv_edi_base',           # Infraestructura EDI base
        'l10n_sv_edi_json',          # Generador JSON DTE
        'l10n_sv_api_client',        # Comunicación MH
        'l10n_sv_digital_signature', # Firma digital
        'account',                   # Módulo de contabilidad
        'web',                       # Framework web
    ],
    'external_dependencies': {
        'python': [
            'qrcode',
            'Pillow',
            'reportlab',
            'python-barcode',
        ]
    },
    'data': [
        'security/ir.model.access.csv',
        'data/report_template_data.xml',
        'data/email_template_data.xml',
        'views/qr_code_generator_views.xml',
        'views/report_template_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
        'reports/invoice_dte_template.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'l10n_sv_reports/static/src/css/report_style.css',
        ],
        'web.report_assets_pdf': [
            'l10n_sv_reports/static/src/css/report_pdf.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}