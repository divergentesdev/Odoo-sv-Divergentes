from . import models

def _setup_fiscal_positions(env):
    """
    Hook de post-instalación para crear posiciones fiscales y mapeos de impuestos.
    Crea automáticamente las posiciones fiscales estándar de El Salvador.
    """
    # Primero actualizar impuestos existentes con campos personalizados
    _update_tax_custom_fields(env)
    
    # Luego crear las posiciones fiscales básicas
    _create_fiscal_positions(env)
    
    # Finalmente configurar los mapeos de impuestos
    _setup_tax_mappings(env)

def _create_fiscal_positions(env):
    """
    Crea las posiciones fiscales estándar para El Salvador
    """
    # Buscar la compañía que tiene impuestos de El Salvador (con código DGII)
    sv_company = env['account.tax'].search([('code_dgii', '!=', False)], limit=1).company_id
    if not sv_company:
        # Si no hay impuestos con código DGII, usar la compañía actual
        sv_company = env.company
    
    # Cambiar el contexto a la compañía de El Salvador
    env = env(context=dict(env.context, allowed_company_ids=[sv_company.id]))
    
    # Buscar módulo de tipos de documento
    try:
        doc_type_01 = env.ref('l10n_sv_document_type.document_type_01_factura', False)
        doc_type_03 = env.ref('l10n_sv_document_type.document_type_03_ccf', False) 
        doc_type_11 = env.ref('l10n_sv_document_type.document_type_11_exportacion', False)
        doc_type_14 = env.ref('l10n_sv_document_type.document_type_14_sujeto_excluido', False)
    except:
        doc_type_01 = doc_type_03 = doc_type_11 = doc_type_14 = False
    
    country_sv = env.ref('base.sv')
    
    # Definir posiciones fiscales estándar
    positions_data = [
        {
            'xml_id': 'fiscal_position_consumidor_final',
            'name': 'El Salvador - Consumidor Final',
            'code': 'SV_FINAL_CONSUMER',
            'l10n_sv_is_final_consumer': True,
            'l10n_sv_document_type_id': doc_type_01.id if doc_type_01 else False,
            'note': 'Para ventas a consumidores finales sin NIT. Genera Factura (01).'
        },
        {
            'xml_id': 'fiscal_position_contribuyente',
            'name': 'El Salvador - Contribuyente',
            'code': 'SV_TAXPAYER', 
            'l10n_sv_is_taxpayer': True,
            'l10n_sv_document_type_id': doc_type_03.id if doc_type_03 else False,
            'note': 'Para ventas a contribuyentes con NIT. Genera CCF (03).'
        },
        {
            'xml_id': 'fiscal_position_exportacion',
            'name': 'El Salvador - Exportación',
            'code': 'SV_EXPORT',
            'l10n_sv_is_export': True,
            'l10n_sv_document_type_id': doc_type_11.id if doc_type_11 else False,
            'note': 'Para operaciones de exportación. Genera Factura de Exportación (11).'
        },
        {
            'xml_id': 'fiscal_position_sujeto_excluido',
            'name': 'El Salvador - Sujeto Excluido',
            'code': 'SV_EXCLUDED',
            'l10n_sv_is_excluded_subject': True,
            'l10n_sv_document_type_id': doc_type_14.id if doc_type_14 else False,
            'note': 'Para sujetos excluidos del IVA. Genera Factura de Sujeto Excluido (14).'
        },
        {
            'xml_id': 'fiscal_position_agente_retenedor_renta',
            'name': 'El Salvador - Agente Retenedor (Renta)',
            'code': 'SV_WITHHOLDING_INCOME',
            'l10n_sv_is_withholding_agent': True,
            'l10n_sv_withholding_type': 'income',
            'l10n_sv_auto_apply': False,
            'note': 'Para compras donde se debe aplicar retención de renta.'
        },
        {
            'xml_id': 'fiscal_position_agente_retenedor_iva',
            'name': 'El Salvador - Agente Retenedor (IVA)',
            'code': 'SV_WITHHOLDING_VAT',
            'l10n_sv_is_withholding_agent': True,
            'l10n_sv_withholding_type': 'vat',
            'l10n_sv_auto_apply': False,
            'note': 'Para compras donde se debe aplicar retención de IVA.'
        },
        {
            'xml_id': 'fiscal_position_agente_retenedor_ambas',
            'name': 'El Salvador - Agente Retenedor (Completo)',
            'code': 'SV_WITHHOLDING_BOTH',
            'l10n_sv_is_withholding_agent': True,
            'l10n_sv_withholding_type': 'both',
            'l10n_sv_auto_apply': False,
            'note': 'Para compras donde se aplican ambas retenciones.'
        }
    ]
    
    # Crear posiciones fiscales
    for data in positions_data:
        xml_id = data.pop('xml_id')
        data.update({
            'country_id': country_sv.id,
            'company_id': sv_company.id,
            'l10n_sv_auto_apply': data.get('l10n_sv_auto_apply', True)
        })
        
        # Verificar si ya existe
        existing = env['account.fiscal.position'].search([('code', '=', data['code'])], limit=1)
        if not existing:
            position = env['account.fiscal.position'].create(data)
            # Crear external ID para referencia
            env['ir.model.data'].create({
                'name': xml_id,
                'module': 'l10n_sv_fiscal_position',
                'model': 'account.fiscal.position',
                'res_id': position.id,
                'noupdate': True
            })

def _setup_tax_mappings(env):
    """
    Configura los mapeos de impuestos automáticamente
    """
    # Buscar la compañía que tiene impuestos de El Salvador
    sv_company = env['account.tax'].search([('code_dgii', '!=', False)], limit=1).company_id
    if not sv_company:
        return  # No hay impuestos de El Salvador configurados
    
    # Cambiar el contexto a la compañía de El Salvador  
    env = env(context=dict(env.context, allowed_company_ids=[sv_company.id]))
    
    # Buscar impuestos por código DGII (estándar para El Salvador)
    AccountTax = env['account.tax'].with_context(company_id=sv_company.id)
    
    # Variables para almacenar impuestos encontrados
    iva_venta = None
    iva_compra = None
    retencion_renta = None
    retencion_iva = None
    exportacion_tax = None
    
    # Buscar IVA 13% venta (código DGII: 20)
    iva_venta = AccountTax.search([
        ('code_dgii', '=', '20'),
        ('type_tax_use', '=', 'sale'),
        ('amount', '=', 13.0)
    ], limit=1)
    
    # Buscar IVA 13% compra (código DGII: 20)
    iva_compra = AccountTax.search([
        ('code_dgii', '=', '20'),
        ('type_tax_use', '=', 'purchase'),
        ('amount', '=', 13.0)
    ], limit=1)
    
    # Buscar impuesto de exportación (código DGII: C3)
    exportacion_tax = AccountTax.search([
        ('code_dgii', '=', 'C3'),
        ('type_tax_use', '=', 'sale'),
        ('amount', '=', 0.0)
    ], limit=1)
    
    # Buscar retención de renta 10%
    retencion_renta = AccountTax.search([
        ('amount', '=', -10.0),
        ('type_tax_use', '=', 'purchase')
    ], limit=1)
    
    # Buscar retención de IVA 1% (código DGII: 22 o por nombre)
    retencion_iva = AccountTax.search([
        ('code_dgii', '=', '22'),
        ('type_tax_use', '=', 'purchase'),
        ('amount', '=', -1.0)
    ], limit=1)
    
    # Si no se encuentra por código, buscar por nombre
    if not retencion_iva:
        retencion_iva = AccountTax.search([
            ('name', 'ilike', 'Retención IVA'),
            ('type_tax_use', '=', 'purchase'),
            ('amount', '=', -1.0)
        ], limit=1)
    
    # Mapear impuestos para exportación
    export_position = env.ref('l10n_sv_fiscal_position.fiscal_position_exportacion', False)
    if export_position:
        # IVA 13% venta → Exportación (0%)
        if iva_venta and exportacion_tax:
            env['account.fiscal.position.tax'].create({
                'position_id': export_position.id,
                'tax_src_id': iva_venta.id,
                'tax_dest_id': exportacion_tax.id,  # Usar impuesto de exportación
            })
        elif iva_venta:
            # Si no hay impuesto de exportación, mapear a sin impuesto
            env['account.fiscal.position.tax'].create({
                'position_id': export_position.id,
                'tax_src_id': iva_venta.id,
                'tax_dest_id': False,
            })
    
    # Mapear impuestos para sujeto excluido
    excluded_position = env.ref('l10n_sv_fiscal_position.fiscal_position_sujeto_excluido', False)
    if excluded_position:
        # IVA 13% venta → Sin impuesto (sujetos excluidos)
        if iva_venta:
            env['account.fiscal.position.tax'].create({
                'position_id': excluded_position.id,
                'tax_src_id': iva_venta.id,
                'tax_dest_id': False,  # Sin impuesto para excluidos
            })
        
        # IVA 13% compra → Sin impuesto (sujetos excluidos)
        if iva_compra:
            env['account.fiscal.position.tax'].create({
                'position_id': excluded_position.id,
                'tax_src_id': iva_compra.id,
                'tax_dest_id': False,  # Sin impuesto para excluidos
            })
    
    # Mapear retenciones para agente retenedor de renta
    # Para retenciones necesitamos mapear DESDE un impuesto base HACIA la retención
    income_position = env.ref('l10n_sv_fiscal_position.fiscal_position_agente_retenedor_renta', False)
    if income_position and retencion_renta and iva_compra:
        # Mapear IVA compra hacia retención de renta
        env['account.fiscal.position.tax'].create({
            'position_id': income_position.id,
            'tax_src_id': iva_compra.id,
            'tax_dest_id': retencion_renta.id,  # Reemplazar IVA con retención renta
        })
    
    # Mapear retenciones para agente retenedor de IVA
    vat_position = env.ref('l10n_sv_fiscal_position.fiscal_position_agente_retenedor_iva', False)
    if vat_position and retencion_iva and iva_compra:
        # Mapear IVA compra hacia retención de IVA
        env['account.fiscal.position.tax'].create({
            'position_id': vat_position.id,
            'tax_src_id': iva_compra.id,
            'tax_dest_id': retencion_iva.id,  # Reemplazar IVA con retención IVA
        })
    
    # Mapear retenciones para agente retenedor completo
    both_position = env.ref('l10n_sv_fiscal_position.fiscal_position_agente_retenedor_ambas', False)
    if both_position and iva_compra:
        # Para agente retenedor completo, crear grupo de impuestos combinado
        if retencion_renta and retencion_iva:
            # Buscar o crear grupo de impuestos combinado
            combined_tax_group = AccountTax.search([
                ('name', '=', 'Retenciones Combinadas (Renta + IVA)'),
                ('type_tax_use', '=', 'purchase')
            ], limit=1)
            
            if not combined_tax_group:
                # Crear grupo de impuestos combinado si no existe
                combined_tax_group = AccountTax.create({
                    'name': 'Retenciones Combinadas (Renta + IVA)',
                    'amount': 0,  # Es un grupo, no tiene cantidad propia
                    'type_tax_use': 'purchase',
                    'amount_type': 'group',
                    'children_tax_ids': [(6, 0, [retencion_renta.id, retencion_iva.id])]
                })
            
            # Mapear IVA compra hacia retenciones combinadas
            env['account.fiscal.position.tax'].create({
                'position_id': both_position.id,
                'tax_src_id': iva_compra.id,
                'tax_dest_id': combined_tax_group.id,  # Usar grupo combinado
            })
        elif retencion_renta:
            # Solo retención de renta disponible
            env['account.fiscal.position.tax'].create({
                'position_id': both_position.id,
                'tax_src_id': iva_compra.id,
                'tax_dest_id': retencion_renta.id,
            })
        elif retencion_iva:
            # Solo retención de IVA disponible
            env['account.fiscal.position.tax'].create({
                'position_id': both_position.id,
                'tax_src_id': iva_compra.id,
                'tax_dest_id': retencion_iva.id,
            })

def _update_tax_custom_fields(env):
    """
    Actualiza los impuestos existentes con campos personalizados de El Salvador
    """
    # Buscar impuestos de retención por descripción y actualizar campos personalizados
    tax_updates = [
        {
            'description': 'RENT_1',
            'l10n_sv_is_withholding': True,
            'l10n_sv_withholding_type': 'income'
        },
        {
            'description': 'RENT_5', 
            'l10n_sv_is_withholding': True,
            'l10n_sv_withholding_type': 'income'
        },
        {
            'description': 'RENT_10',
            'l10n_sv_is_withholding': True,
            'l10n_sv_withholding_type': 'income'
        },
        {
            'description': 'RET_IVA',
            'l10n_sv_is_withholding': True,
            'l10n_sv_withholding_type': 'vat'
        }
    ]
    
    # Actualizar cada impuesto
    for update_data in tax_updates:
        description = update_data.pop('description')
        tax = env['account.tax'].search([('description', '=', description)], limit=1)
        
        if tax:
            try:
                tax.write(update_data)
                print(f"Impuesto actualizado: {tax.name} - {description}")
            except Exception as e:
                print(f"Error actualizando impuesto {description}: {e}")