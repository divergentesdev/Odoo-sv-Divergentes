{
    'name': 'El Salvador - Firma Digital DTE',
    'version': '18.0.1.0.0',
    'summary': 'Firma digital para documentos tributarios electrónicos de El Salvador',
    'description': '''
        Módulo para firma digital de documentos tributarios electrónicos (DTE)
        según las especificaciones técnicas del Ministerio de Hacienda de El Salvador.
        
        Funcionalidades:
        * Firma digital de JSON DTE con certificados .cert del MH
        * Validación de firmas digitales existentes
        * Integración con generación de JSON DTE
        * Manejo de cadenas de certificados
        * Verificación de validez temporal de certificados
        * Algoritmos de firma compatibles con especificaciones MH
        * Logs de operaciones de firma
        * Soporte para múltiples algoritmos de hash (SHA-256, SHA-512)
        * Verificación de integridad de documentos firmados
        * Gestión de certificados raíz y cadenas de confianza
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
            'cryptography',
            'OpenSSL',
            'xmlsec',
            'lxml',
        ]
    },
    'data': [
        'security/ir.model.access.csv',
        'data/signature_algorithm_data.xml',
        'views/digital_signature_views.xml',
        'views/signature_log_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
        'demo/real_certificate_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}