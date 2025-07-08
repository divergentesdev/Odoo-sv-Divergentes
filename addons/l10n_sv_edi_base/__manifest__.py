{
    'name': 'El Salvador - EDI Base',
    'version': '18.0.1.0.0',
    'summary': 'Infraestructura base para facturación electrónica de El Salvador',
    'description': '''
        Módulo base para la implementación de facturación electrónica (DTE) 
        según las especificaciones del Ministerio de Hacienda de El Salvador.
        
        Funcionalidades:
        * Gestión de certificados digitales .cert del MH
        * Configuración de ambientes (certificación/producción)
        * Infraestructura base para DTE (Documentos Tributarios Electrónicos)
        * Integración con API del Ministerio de Hacienda
    ''',
    'category': 'Accounting/Localizations/EDI',
    'author': 'Divergentes Media S.A.S. de C.V.',
    'website': 'https://www.divergentesmedia.com',
    'maintainer': 'Divergentes Media S.A.S. de C.V.',
    'support': 'info@divergentesmedia.com',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'base',
        'l10n_sv_cta',  # Plan de cuentas El Salvador
        'l10n_latam_sv',  # Localización El Salvador con campos de empresa
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/edi_environment_data.xml',
        'views/edi_certificate_views.xml',
        'views/edi_configuration_views.xml',
        'views/res_company_views.xml',
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