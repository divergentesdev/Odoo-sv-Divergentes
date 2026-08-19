#!/usr/bin/env python3
"""
Templates JSON oficiales basados en esquemas validados por MH El Salvador
Estos templates son la estructura base que usa realmente el MH
"""

# Template para Factura (01) - Basado en fe-fc-v2.json (Vigencia desde 01/12/2025)
TEMPLATE_FACTURA_01 = {
    "identificacion": {
        "version": 2,  # Actualizado a v2 para vigencia desde 01/12/2025
        "ambiente": "{{ambiente}}",
        "tipoDte": "01", 
        "numeroControl": "{{numeroControl}}",
        "codigoGeneracion": "{{codigoGeneracion}}",
        "tipoModelo": 1,
        "tipoOperacion": 1,
        "tipoContingencia": None,
        "motivoContin": None,
        "fecEmi": "{{fecEmi}}",
        "horEmi": "{{horEmi}}",
        "tipoMoneda": "USD"
    },
    "documentoRelacionado": None,
    "emisor": {
        "nit": "{{emisor.nit}}",
        "nrc": "{{emisor.nrc}}",
        "nombre": "{{emisor.nombre}}",
        "codActividad": "{{emisor.codActividad}}",
        "descActividad": "{{emisor.descActividad}}",
        "nombreComercial": "{{emisor.nombreComercial}}",
        "tipoEstablecimiento": "01",
        "direccion": {
            "departamento": "{{emisor.direccion.departamento}}",
            "municipio": "{{emisor.direccion.municipio}}",
            "complemento": "{{emisor.direccion.complemento}}"
        },
        "telefono": "{{emisor.telefono}}",
        "correo": "{{emisor.correo}}",
        "codEstableMH": "{{emisor.codEstableMH}}",
        "codEstable": "{{emisor.codEstable}}",
        "codPuntoVentaMH": "{{emisor.codPuntoVentaMH}}",
        "codPuntoVenta": "{{emisor.codPuntoVenta}}"
    },
    "receptor": "{{receptor}}",  # Dinámico: consumidor final o contribuyente
    "otrosDocumentos": None,
    "ventaTercero": None,
    "cuerpoDocumento": "{{cuerpoDocumento}}",  # Array dinámico
    "resumen": {
        "totalNoSuj": "{{resumen.totalNoSuj}}",
        "totalExenta": "{{resumen.totalExenta}}",
        "totalGravada": "{{resumen.totalGravada}}",
        "subTotalVentas": "{{resumen.subTotalVentas}}",
        "descuNoSuj": 0.00,
        "descuExenta": 0.00,
        "descuGravada": 0.00,
        "porcentajeDescuento": 0.00,
        "totalDescu": 0.00,
        "tributos": "{{resumen.tributos}}",  # null para consumidor final
        "subTotal": "{{resumen.subTotal}}",
        "ivaRete": "{{resumen.ivaRete}}",  # Renombrado de ivaRete1 a ivaRete en v2
        # "reteRenta": 0.00,  # ELIMINADO en v2
        "montoTotalOperacion": "{{resumen.montoTotalOperacion}}",
        "totalNoGravado": 0.00,
        "totalPagar": "{{resumen.totalPagar}}",
        "totalLetras": "{{resumen.totalLetras}}",
        "totalIva": "{{resumen.totalIva}}",
        "saldoFavor": 0.00,
        "condicionOperacion": "{{resumen.condicionOperacion}}",
        "pagos": "{{resumen.pagos}}",
        "numPagoElectronico": "{{resumen.numPagoElectronico}}",
        "observaciones": None  # Nuevo campo opcional en v2
    },
    "extension": None,  # OBLIGATORIO null para Factura
    "apendice": None
}

# Template para CCF (03) - Basado en fe-ccf-v4.json (Vigencia desde 01/12/2025)
TEMPLATE_CCF_03 = {
    "identificacion": {
        "version": 4,  # Actualizado a v4 para vigencia desde 01/12/2025 - CAMBIO CRÍTICO
        "ambiente": "{{ambiente}}",
        "tipoDte": "03",
        "numeroControl": "{{numeroControl}}",
        "codigoGeneracion": "{{codigoGeneracion}}",
        "tipoModelo": 1,
        "tipoOperacion": 1,
        "tipoContingencia": None,
        "motivoContin": None,
        "fecEmi": "{{fecEmi}}",
        "horEmi": "{{horEmi}}",
        "tipoMoneda": "USD"
    },
    "documentoRelacionado": "{{documentoRelacionado}}",  # AHORA ES ARRAY OBLIGATORIO (minItems:1, maxItems:50) en v4
    "emisor": {
        "nit": "{{emisor.nit}}",
        "nrc": "{{emisor.nrc}}",
        "nombre": "{{emisor.nombre}}",
        "codActividad": "{{emisor.codActividad}}",
        "descActividad": "{{emisor.descActividad}}",
        "nombreComercial": "{{emisor.nombreComercial}}",
        "tipoEstablecimiento": "01",
        "direccion": {
            "departamento": "{{emisor.direccion.departamento}}",
            "municipio": "{{emisor.direccion.municipio}}",
            "complemento": "{{emisor.direccion.complemento}}"
        },
        "telefono": "{{emisor.telefono}}",
        "correo": "{{emisor.correo}}",
        "codEstableMH": "{{emisor.codEstableMH}}",
        "codEstable": "{{emisor.codEstable}}",
        "codPuntoVentaMH": "{{emisor.codPuntoVentaMH}}",
        "codPuntoVenta": "{{emisor.codPuntoVenta}}"
    },
    "receptor": {  # CCF para ambiente certificación (00) - Estructura específica
        "tipoDocumento": "{{receptor.tipoDocumento}}",  # Requerido en certificación
        "numDocumento": "{{receptor.numDocumento}}",  # Requerido en certificación
        "nrc": "{{receptor.nrc}}",
        "nombre": "{{receptor.nombre}}",
        "codActividad": "{{receptor.codActividad}}",
        "descActividad": "{{receptor.descActividad}}",
        "direccion": {
            "departamento": "{{receptor.direccion.departamento}}",
            "municipio": "{{receptor.direccion.municipio}}",
            "complemento": "{{receptor.direccion.complemento}}"
        },
        "telefono": "{{receptor.telefono}}",
        "correo": "{{receptor.correo}}"
    },
    "otrosDocumentos": None,
    "ventaTercero": None,
    "cuerpoDocumento": "{{cuerpoDocumento}}",
    "resumen": {
        "totalNoSuj": "{{resumen.totalNoSuj}}",
        "totalExenta": "{{resumen.totalExenta}}",
        "totalGravada": "{{resumen.totalGravada}}",
        "subTotalVentas": "{{resumen.subTotalVentas}}",
        "descuNoSuj": 0.00,
        "descuExenta": 0.00,
        "descuGravada": 0.00,
        "porcentajeDescuento": 0.00,
        "totalDescu": 0.00,
        "tributos": "{{resumen.tributos}}",  # Requerido para CCF
        "subTotal": "{{resumen.subTotal}}",
        "ivaRete": "{{resumen.ivaRete}}",  # Renombrado de ivaRete1 a ivaRete
        # "reteRenta": 0.00,  # ELIMINADO en v4
        "montoTotalOperacion": "{{resumen.montoTotalOperacion}}",
        "totalNoGravado": 0.00,
        "totalPagar": "{{resumen.totalPagar}}",
        "totalLetras": "{{resumen.totalLetras}}",
        "totalIva": "{{resumen.totalIva}}",
        "saldoFavor": 0.00,
        "condicionOperacion": "{{resumen.condicionOperacion}}",
        "pagos": [],  # CCF pagos como array vacío
        "numPagoElectronico": None  # CCF no lleva numPagoElectronico
    },
    # "extension": {...},  # ELIMINADO COMPLETAMENTE EN V4 - NO AGREGAR ESTE CAMPO
    "apendice": None
}

# Template para Nota de Crédito (05) - Basado en fe-nc-v4.json (Vigencia desde 01/12/2025)
TEMPLATE_NOTA_CREDITO_05 = {
    "identificacion": {
        "version": 4,  # Actualizado a v4 para vigencia desde 01/12/2025 - CAMBIO CRÍTICO
        "ambiente": "{{ambiente}}",
        "tipoDte": "05",
        "numeroControl": "{{numeroControl}}",
        "codigoGeneracion": "{{codigoGeneracion}}",
        "tipoModelo": 1,
        "tipoOperacion": 1,
        "tipoContingencia": None,
        "motivoContin": None,
        "fecEmi": "{{fecEmi}}",
        "horEmi": "{{horEmi}}",
        "tipoMoneda": "USD"
    },
    "documentoRelacionado": "{{documentoRelacionado}}",  # AHORA ES ARRAY OBLIGATORIO (minItems:1, maxItems:50) en v4
    "emisor": {
        "nit": "{{emisor.nit}}",
        "nrc": "{{emisor.nrc}}",
        "nombre": "{{emisor.nombre}}",
        "codActividad": "{{emisor.codActividad}}",
        "descActividad": "{{emisor.descActividad}}",
        "nombreComercial": "{{emisor.nombreComercial}}",
        "tipoEstablecimiento": "01",
        "direccion": {
            "departamento": "{{emisor.direccion.departamento}}",
            "municipio": "{{emisor.direccion.municipio}}",
            "complemento": "{{emisor.direccion.complemento}}"
        },
        "telefono": "{{emisor.telefono}}",
        "correo": "{{emisor.correo}}",
        "codEstableMH": "{{emisor.codEstableMH}}",
        "codEstable": "{{emisor.codEstable}}",
        "codPuntoVentaMH": "{{emisor.codPuntoVentaMH}}",
        "codPuntoVenta": "{{emisor.codPuntoVenta}}"
    },
    "receptor": "{{receptor}}",
    "otrosDocumentos": None,
    "ventaTercero": None,
    "cuerpoDocumento": "{{cuerpoDocumento}}",
    "resumen": {
        "totalNoSuj": "{{resumen.totalNoSuj}}",
        "totalExenta": "{{resumen.totalExenta}}",
        "totalGravada": "{{resumen.totalGravada}}",
        "subTotalVentas": "{{resumen.subTotalVentas}}",
        "descuNoSuj": 0.00,
        "descuExenta": 0.00,
        "descuGravada": 0.00,
        "porcentajeDescuento": 0.00,
        "totalDescu": 0.00,
        "tributos": "{{resumen.tributos}}",
        "subTotal": "{{resumen.subTotal}}",
        "ivaRete": "{{resumen.ivaRete}}",  # Renombrado de ivaRete1 a ivaRete
        # "reteRenta": 0.00,  # ELIMINADO en v4
        "montoTotalOperacion": "{{resumen.montoTotalOperacion}}",
        "totalNoGravado": 0.00,
        "totalPagar": "{{resumen.totalPagar}}",
        "totalLetras": "{{resumen.totalLetras}}",
        "totalIva": "{{resumen.totalIva}}",
        "saldoFavor": 0.00,
        "condicionOperacion": "{{resumen.condicionOperacion}}",
        "pagos": None,  # Notas de crédito no llevan pagos
        "numPagoElectronico": None
    },
    # "extension": {...},  # ELIMINADO COMPLETAMENTE EN V4 - NO AGREGAR ESTE CAMPO
    "apendice": None
}

# Template para Nota de Débito (06) - Basado en fe-nd-v4.json (Vigencia desde 01/12/2025)
TEMPLATE_NOTA_DEBITO_06 = {
    "identificacion": {
        "version": 4,  # Actualizado a v4 para vigencia desde 01/12/2025 - CAMBIO CRÍTICO
        "ambiente": "{{ambiente}}",
        "tipoDte": "06",
        "numeroControl": "{{numeroControl}}",
        "codigoGeneracion": "{{codigoGeneracion}}",
        "tipoModelo": 1,
        "tipoOperacion": 1,
        "tipoContingencia": None,
        "motivoContin": None,
        "fecEmi": "{{fecEmi}}",
        "horEmi": "{{horEmi}}",
        "tipoMoneda": "USD"
    },
    "documentoRelacionado": "{{documentoRelacionado}}",  # AHORA ES ARRAY OBLIGATORIO (minItems:1, maxItems:50) en v4
    "emisor": {
        "nit": "{{emisor.nit}}",
        "nrc": "{{emisor.nrc}}",
        "nombre": "{{emisor.nombre}}",
        "codActividad": "{{emisor.codActividad}}",
        "descActividad": "{{emisor.descActividad}}",
        "nombreComercial": "{{emisor.nombreComercial}}",
        "tipoEstablecimiento": "01",
        "direccion": {
            "departamento": "{{emisor.direccion.departamento}}",
            "municipio": "{{emisor.direccion.municipio}}",
            "complemento": "{{emisor.direccion.complemento}}"
        },
        "telefono": "{{emisor.telefono}}",
        "correo": "{{emisor.correo}}",
        "codEstableMH": "{{emisor.codEstableMH}}",
        "codEstable": "{{emisor.codEstable}}",
        "codPuntoVentaMH": "{{emisor.codPuntoVentaMH}}",
        "codPuntoVenta": "{{emisor.codPuntoVenta}}"
    },
    "receptor": "{{receptor}}",
    "otrosDocumentos": None,
    "ventaTercero": None,
    "cuerpoDocumento": "{{cuerpoDocumento}}",
    "resumen": {
        "totalNoSuj": "{{resumen.totalNoSuj}}",
        "totalExenta": "{{resumen.totalExenta}}",
        "totalGravada": "{{resumen.totalGravada}}",
        "subTotalVentas": "{{resumen.subTotalVentas}}",
        "descuNoSuj": 0.00,
        "descuExenta": 0.00,
        "descuGravada": 0.00,
        "porcentajeDescuento": 0.00,
        "totalDescu": 0.00,
        "tributos": "{{resumen.tributos}}",
        "subTotal": "{{resumen.subTotal}}",
        "ivaRete": "{{resumen.ivaRete}}",  # Renombrado de ivaRete1 a ivaRete
        # "reteRenta": 0.00,  # ELIMINADO en v4
        "montoTotalOperacion": "{{resumen.montoTotalOperacion}}",
        "totalNoGravado": 0.00,
        "totalPagar": "{{resumen.totalPagar}}",
        "totalLetras": "{{resumen.totalLetras}}",
        "totalIva": "{{resumen.totalIva}}",
        "saldoFavor": 0.00,
        "condicionOperacion": "{{resumen.condicionOperacion}}",
        "pagos": "{{resumen.pagos}}",  # ND SÍ lleva pagos
        "numPagoElectronico": "{{resumen.numPagoElectronico}}",  # ND SÍ lleva numPagoElectronico
        "observaciones": None  # Nuevo campo opcional en v4
    },
    # "extension": {...},  # ELIMINADO COMPLETAMENTE EN V4 - NO AGREGAR ESTE CAMPO
    "apendice": None
}

# Template para Factura de Exportación (11) - Basado en fe-fex-v3.json (Vigencia desde 01/12/2025)
TEMPLATE_EXPORTACION_11 = {
    "identificacion": {
        "version": 3,  # Actualizado a v3 para vigencia desde 01/12/2025
        "ambiente": "{{ambiente}}",
        "tipoDte": "11",
        "numeroControl": "{{numeroControl}}",
        "codigoGeneracion": "{{codigoGeneracion}}",
        "tipoModelo": 1,
        "tipoOperacion": 1,
        "fecEmi": "{{fecEmi}}",
        "horEmi": "{{horEmi}}",
        "tipoMoneda": "USD"
    },
    "documentoRelacionado": "{{documentoRelacionado}}",  # Nuevo campo requerido en v3
    "emisor": {
        "nit": "{{emisor.nit}}",
        "nrc": "{{emisor.nrc}}",
        "nombre": "{{emisor.nombre}}",
        "codActividad": "{{emisor.codActividad}}",
        "descActividad": "{{emisor.descActividad}}",
        "nombreComercial": "{{emisor.nombreComercial}}",
        "tipoEstablecimiento": "01",
        "direccion": {
            "departamento": "{{emisor.direccion.departamento}}",
            "municipio": "{{emisor.direccion.municipio}}",
            "complemento": "{{emisor.direccion.complemento}}"
        },
        "telefono": "{{emisor.telefono}}",
        "correo": "{{emisor.correo}}",
        "codEstableMH": "{{emisor.codEstableMH}}",
        "codEstable": "{{emisor.codEstable}}",
        "codPuntoVentaMH": "{{emisor.codPuntoVentaMH}}",
        "codPuntoVenta": "{{emisor.codPuntoVenta}}"
    },
    "receptor": "{{receptor}}",  # Condicional >= $10,000
    "otrosDocumentos": None,
    "ventaTercero": None,
    "compraTercero": None,  # Nuevo campo en v3
    "cuerpoDocumento": "{{cuerpoDocumento}}",
    "resumen": {
        "totalGravada": "{{resumen.totalGravada}}",
        "descuGravada": 0.00,  # Renombrado de descuento a descuGravada en v3
        "porcentajeDescuento": 0.00,
        "totalDescu": 0.00,
        "seguro": "{{resumen.seguro}}",
        "flete": "{{resumen.flete}}",
        "tributos": None,  # Nuevo campo en v3
        "montoTotalOperacion": "{{resumen.montoTotalOperacion}}",
        "totalNoGravado": 0.00,
        "totalNoOnerosas": 0.00,  # Nuevo campo en v3
        "totalPagar": "{{resumen.totalPagar}}",
        "totalLetras": "{{resumen.totalLetras}}",
        "saldoFavor": 0.00,  # Nuevo campo en v3
        "condicionOperacion": "{{resumen.condicionOperacion}}",
        "pagos": "{{resumen.pagos}}",  # Nuevo campo en v3
        "codIncoterms": "{{resumen.codIncoterms}}",
        "descIncoterms": "{{resumen.descIncoterms}}",
        "numPagoElectronico": "{{resumen.numPagoElectronico}}",  # Nuevo campo en v3
        "observaciones": "{{resumen.observaciones}}"
    }
}

# Template para Factura Sujeto Excluido (14) - Basado en fe-fse-v2.json (Vigencia desde 01/12/2025)
TEMPLATE_SUJETO_EXCLUIDO_14 = {
    "identificacion": {
        "version": 2,  # Actualizado a v2 para vigencia desde 01/12/2025 - CAMBIO CRÍTICO
        "ambiente": "{{ambiente}}",
        "tipoDte": "14",
        "numeroControl": "{{numeroControl}}",
        "codigoGeneracion": "{{codigoGeneracion}}",
        "tipoModelo": 1,
        "tipoOperacion": 1,
        "fecEmi": "{{fecEmi}}",
        "horEmi": "{{horEmi}}",
        "tipoMoneda": "USD"
    },
    "emisor": {
        "nombre": "{{emisor.nombre}}",
        "codActividad": "{{emisor.codActividad}}",
        "descActividad": "{{emisor.descActividad}}",
        "direccion": {
            "departamento": "{{emisor.direccion.departamento}}",
            "municipio": "{{emisor.direccion.municipio}}",
            "complemento": "{{emisor.direccion.complemento}}"
        },
        "telefono": "{{emisor.telefono}}",
        "correo": "{{emisor.correo}}"
    },
    "receptor": {  # CAMBIO CRÍTICO: Ahora usa receptor en lugar de sujetoExcluido en v2
        "tipoDocumento": "{{receptor.tipoDocumento}}",
        "numDocumento": "{{receptor.numDocumento}}",
        "nombre": "{{receptor.nombre}}",
        "codActividad": "{{receptor.codActividad}}",
        "descActividad": "{{receptor.descActividad}}",
        "direccion": {
            "departamento": "{{receptor.direccion.departamento}}",
            "municipio": "{{receptor.direccion.municipio}}",
            "complemento": "{{receptor.direccion.complemento}}"
        },
        "telefono": "{{receptor.telefono}}",
        "correo": "{{receptor.correo}}"
    },
    # "sujetoExcluido": {...},  # ELIMINADO EN V2 - USAR receptor EN SU LUGAR
    "cuerpoDocumento": "{{cuerpoDocumento}}",
    "resumen": {
        "totalCompra": "{{resumen.totalCompra}}",
        "descu": 0.00,
        "totalDescu": 0.00,
        "totalPagar": "{{resumen.totalPagar}}",
        "totalLetras": "{{resumen.totalLetras}}",
        "condicionOperacion": "{{resumen.condicionOperacion}}"
    }
}

# Mapeo de tipos de documento a templates
TEMPLATES_OFICIALES = {
    "01": TEMPLATE_FACTURA_01,
    "03": TEMPLATE_CCF_03,
    "05": TEMPLATE_NOTA_CREDITO_05,
    "06": TEMPLATE_NOTA_DEBITO_06,
    "11": TEMPLATE_EXPORTACION_11,
    "14": TEMPLATE_SUJETO_EXCLUIDO_14
}

if __name__ == "__main__":
    import json
    
    print("📋 Templates JSON Oficiales del MH:")
    for tipo, template in TEMPLATES_OFICIALES.items():
        print(f"\n🔹 Tipo {tipo}:")
        print(f"   Versión: {template['identificacion']['version']}")
        print(f"   Campos únicos: {len(template.keys())}")
        
        # Verificar campos específicos por tipo
        if tipo == "01":
            print(f"   ✅ Extension: {template.get('extension')} (debe ser null)")
        elif tipo == "03":
            print(f"   ✅ ivaPerci1: {'ivaPerci1' in template['resumen']}")
            print(f"   ✅ Pagos: {template['resumen']['pagos']} (debe ser null)")
        elif tipo in ["05", "06"]:
            print(f"   ✅ DocumentoRelacionado: {'documentoRelacionado' in template}")
        elif tipo == "11":
            print(f"   ✅ Incoterms: {'codIncoterms' in template['resumen']}")
        elif tipo == "14":
            print(f"   ✅ SujetoExcluido: {'sujetoExcluido' in template}")
    
    print("\n✅ Templates basados en esquemas oficiales validados por MH")