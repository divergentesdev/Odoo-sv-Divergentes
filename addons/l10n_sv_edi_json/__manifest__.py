{
    'name': 'El Salvador - Generador de JSON DTE',
    'version': '18.0.1.0.4',  # Incremento versión para forzar recarga
    'summary': 'Generador de JSON para documentos tributarios electrónicos de El Salvador',
    'description': '''
        Módulo para generar documentos tributarios electrónicos (DTE) en formato JSON
        según las especificaciones técnicas del Ministerio de Hacienda de El Salvador.
        Funcionalidades:
        * Generación de JSON DTE para todos los tipos de documentos
        * Interfaz web para ver y descargar documentos DTE
        * Integración con contabilidad de Odoo
        * Reportes de contingencia
        * Anulación de documentos
        * Integración con API del Ministerio de Hacienda
    ''',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'category': 'Accounting/Localizations',
    'depends': ['account', 'base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/json_generator_views.xml',
        'views/contingency_views.xml',
        'views/cancellation_views.xml',
        'views/menu_views.xml',
        'data/l10n_sv_edi_json_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'l10n_sv_edi_json/static/src/css/contingency_emergency_fix.css',
        ],
    },
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}