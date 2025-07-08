{
    'name': 'El Salvador - Cliente API MH',
    'version': '18.0.1.0.0',
    'summary': 'Cliente API para comunicación con Ministerio de Hacienda de El Salvador',
    'description': '''
        Módulo para comunicación directa con la API del Ministerio de Hacienda de El Salvador
        para el envío y recepción de documentos tributarios electrónicos (DTE).
        
        Funcionalidades:
        * Autenticación con certificados digitales .cert del MH
        * Envío de DTE en formato JSON al MH
        * Recepción y procesamiento de respuestas del MH
        * Manejo de contingencias y estados de documento
        * Consulta de estado de DTE enviados
        * Logs detallados de comunicación con el MH
        * Reintento automático en caso de errores de red
        * Validación de respuestas del MH
        * Soporte para ambientes de certificación y producción
    ''',
    'category': 'Accounting/Localizations/EDI',
    'author': 'Divergentes Media S.A.S. de C.V.',
    'website': 'https://www.divergentesmedia.com',
    'maintainer': 'Divergentes Media S.A.S. de C.V.',
    'support': 'info@divergentesmedia.com',
    'license': 'LGPL-3',
    'depends': [
        'l10n_sv_edi_base',        # Infraestructura EDI base
        'l10n_sv_edi_json',       # Generador JSON DTE
    ],
    'external_dependencies': {
        'python': [
            'requests',
            'cryptography',
            'OpenSSL',
        ]
    },
    'data': [
        'security/ir.model.access.csv',
        'data/api_endpoint_data.xml',
        'views/api_client_views.xml',
        'views/api_log_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}