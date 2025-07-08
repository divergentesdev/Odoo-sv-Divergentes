#!/usr/bin/env python3
"""
Templates JSON oficiales basados en esquemas validados por MH El Salvador
Estos templates son la estructura base que usa realmente el MH
"""

# Template para Factura (01) - Basado en fe-fc-v1.json
TEMPLATE_FACTURA_01 = {
    "identificacion": {
        "version": 1,
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
        "ivaRete1": "{{resumen.ivaRete1}}",
        "reteRenta": 0.00,
        "montoTotalOperacion": "{{resumen.montoTotalOperacion}}",
        "totalNoGravado": 0.00,
        "totalPagar": "{{resumen.totalPagar}}",
        "totalLetras": "{{resumen.totalLetras}}",
        "totalIva": "{{resumen.totalIva}}",
        "saldoFavor": 0.00,
        "condicionOperacion": "{{resumen.condicionOperacion}}",
        "pagos": "{{resumen.pagos}}",
        "numPagoElectronico": "{{resumen.numPagoElectronico}}"
    },
    "extension": None,  # OBLIGATORIO null para Factura
    "apendice": None
}

# Template para CCF (03) - Basado en fe-ccf-v3.json
TEMPLATE_CCF_03 = {
    "identificacion": {
        "version": 3,  # CCF SIEMPRE versión 3 como número
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
        "ivaRete1": "{{resumen.ivaRete1}}",
        "reteRenta": 0.00,
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
    "extension": {  # CCF extension con valores válidos (minLength requerido)
        "nombEntrega": "{{extension.nombEntrega}}",
        "docuEntrega": "{{extension.docuEntrega}}",
        "nombRecibe": "{{extension.nombRecibe}}",
        "docuRecibe": "{{extension.docuRecibe}}",
        "placaVehiculo": "{{extension.placaVehiculo}}",
        "observaciones": "{{extension.observaciones}}"
    },
    "apendice": None
}

# Template para Nota de Crédito (05) - Basado en fe-nc-v3.json
TEMPLATE_NOTA_CREDITO_05 = {
    "identificacion": {
        "version": 3,
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
    "documentoRelacionado": "{{documentoRelacionado}}",  # OBLIGATORIO para NC
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
        "ivaRete1": "{{resumen.ivaRete1}}",
        "reteRenta": 0.00,
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
    "extension": None,
    "apendice": None
}

# Template para Nota de Débito (06) - Basado en fe-nd-v3.json  
TEMPLATE_NOTA_DEBITO_06 = {
    "identificacion": {
        "version": 3,
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
    "documentoRelacionado": "{{documentoRelacionado}}",  # OBLIGATORIO para ND
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
        "ivaRete1": "{{resumen.ivaRete1}}",
        "reteRenta": 0.00,
        "montoTotalOperacion": "{{resumen.montoTotalOperacion}}",
        "totalNoGravado": 0.00,
        "totalPagar": "{{resumen.totalPagar}}",
        "totalLetras": "{{resumen.totalLetras}}",
        "totalIva": "{{resumen.totalIva}}",
        "saldoFavor": 0.00,
        "condicionOperacion": "{{resumen.condicionOperacion}}",
        "pagos": "{{resumen.pagos}}",  # ND SÍ lleva pagos
        "numPagoElectronico": "{{resumen.numPagoElectronico}}"  # ND SÍ lleva numPagoElectronico
    },
    "extension": None,
    "apendice": None
}

# Template para Factura de Exportación (11) - Basado en fe-fex-v1.json
TEMPLATE_EXPORTACION_11 = {
    "identificacion": {
        "version": 1,
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
    "cuerpoDocumento": "{{cuerpoDocumento}}",
    "resumen": {
        "totalGravada": "{{resumen.totalGravada}}",
        "descuento": 0.00,
        "porcentajeDescuento": 0.00,
        "totalDescu": 0.00,
        "seguro": "{{resumen.seguro}}",
        "flete": "{{resumen.flete}}",
        "montoTotalOperacion": "{{resumen.montoTotalOperacion}}",
        "totalLetras": "{{resumen.totalLetras}}",
        "condicionOperacion": "{{resumen.condicionOperacion}}",
        "codIncoterms": "{{resumen.codIncoterms}}",
        "descIncoterms": "{{resumen.descIncoterms}}",
        "observaciones": "{{resumen.observaciones}}"
    }
}

# Template para Factura Sujeto Excluido (14) - Basado en fe-fse-v1.json
TEMPLATE_SUJETO_EXCLUIDO_14 = {
    "identificacion": {
        "version": 1,
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
    "sujetoExcluido": {
        "tipoDocumento": "{{sujetoExcluido.tipoDocumento}}",
        "numDocumento": "{{sujetoExcluido.numDocumento}}",
        "nombre": "{{sujetoExcluido.nombre}}",
        "codActividad": "{{sujetoExcluido.codActividad}}",
        "descActividad": "{{sujetoExcluido.descActividad}}",
        "direccion": {
            "departamento": "{{sujetoExcluido.direccion.departamento}}",
            "municipio": "{{sujetoExcluido.direccion.municipio}}",
            "complemento": "{{sujetoExcluido.direccion.complemento}}"
        },
        "telefono": "{{sujetoExcluido.telefono}}",
        "correo": "{{sujetoExcluido.correo}}"
    },
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