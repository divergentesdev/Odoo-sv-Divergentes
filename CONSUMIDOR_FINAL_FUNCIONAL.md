# Documentación: Formato JSON Consumidor Final - FUNCIONAL

## Información General
- **Tipo de Documento**: 01 (Factura)
- **Versión**: 1
- **Fecha de Validación**: 29/06/2025
- **Estado**: FUNCIONANDO CORRECTAMENTE

## Estructura JSON Validada

### 1. Identificación
```json
{
  "identificacion": {
    "version": 1,
    "ambiente": "00",  // 00=Producción, 01=Pruebas
    "tipoDte": "01",
    "numeroControl": "DTE-01-XXXXXXXX-000000001",
    "codigoGeneracion": "UUID-v4",
    "tipoModelo": 1,   // 1=Transmisión normal
    "tipoOperacion": 1, // 1=Transmisión normal
    "tipoContingencia": null,
    "motivoContin": null,
    "fecEmi": "2025-06-29",
    "horEmi": "12:00:00",
    "tipoMoneda": "USD"
  }
}
```

### 2. Receptor - CRÍTICO PARA CONSUMIDOR FINAL
```json
{
  "receptor": {
    "tipoDocumento": null,      // DEBE SER NULL
    "numDocumento": null,       // DEBE SER NULL
    "nrc": null,                // DEBE SER NULL
    "nombre": "Consumidor final", // TEXTO FIJO
    "codActividad": null,       // DEBE SER NULL
    "descActividad": null,      // DEBE SER NULL
    "direccion": null,          // DEBE SER NULL
    "telefono": null,           // DEBE SER NULL
    "correo": "consumidor@factura.gob.sv" // Correo por defecto o del cliente
  }
}
```

### 3. Cuerpo del Documento
```json
{
  "cuerpoDocumento": [
    {
      "numItem": 1,
      "tipoItem": 2,  // 2=Servicio, 1=Bien, 3=Ambos, 4=Otro
      "numeroDocumento": null,
      "cantidad": 1.00,
      "codigo": null,
      "codTributo": null,  // NULL para consumidor final
      "uniMedida": 99,     // 99=Otros
      "descripcion": "Descripción del producto/servicio",
      "precioUni": 113.00, // Precio CON IVA incluido
      "montoDescu": 0.00,
      "ventaNoSuj": 0.00,
      "ventaExenta": 0.00,
      "ventaGravada": 113.00, // Total CON IVA
      "tributos": null,    // NULL para consumidor final
      "psv": 0.00,
      "noGravado": 0.00,
      "ivaItem": 13.00     // IVA = ventaGravada * 13/113
    }
  ]
}
```

### 4. Resumen - CRÍTICO
```json
{
  "resumen": {
    "totalNoSuj": 0.00,
    "totalExenta": 0.00,
    "totalGravada": 113.00,     // Suma de ventaGravada (CON IVA)
    "subTotalVentas": 113.00,   // = totalNoSuj + totalExenta + totalGravada
    "descuNoSuj": 0.00,
    "descuExenta": 0.00,
    "descuGravada": 0.00,
    "porcentajeDescuento": 0.00,
    "totalDescu": 0.00,
    "tributos": null,           // DEBE SER NULL para consumidor final
    "subTotal": 113.00,
    "ivaRete1": 0.00,
    "reteRenta": 0.00,
    "montoTotalOperacion": 113.00,
    "totalNoGravado": 0.00,
    "totalPagar": 113.00,
    "totalLetras": "CIENTO TRECE DOLARES",
    "totalIva": 13.00,          // Total IVA extraído
    "saldoFavor": 0.00,
    "condicionOperacion": 1,    // 1=Contado, 2=Crédito
    "pagos": [
      {
        "codigo": "01",         // 01=Efectivo
        "montoPago": 113.00,
        "referencia": null,
        "plazo": "01",
        "periodo": null
      }
    ],
    "numPagoElectronico": "N/A"
  }
}
```

## Reglas de Negocio Críticas

### 1. Cálculo del IVA para Consumidor Final
- **ventaGravada** = Precio total CON IVA incluido
- **ivaItem** = ventaGravada * 13/113
- **Precio sin IVA** = ventaGravada - ivaItem

### 2. Campos que DEBEN ser NULL
En el receptor:
- tipoDocumento
- numDocumento
- nrc
- codActividad
- descActividad
- direccion
- telefono

En el resumen:
- **tributos** (CRÍTICO: debe ser null, no un array vacío)

En cuerpoDocumento:
- codTributo
- tributos
- numeroDocumento

### 3. Campos Requeridos aunque sean NULL
Estos campos DEBEN estar presentes en el JSON aunque su valor sea null:
- documentoRelacionado
- extension
- apendice
- otrosDocumentos
- ventaTercero
- tipoContingencia
- motivoContin

### 4. Validación de Montos
- montoTotalOperacion = totalPagar (ambos incluyen IVA)
- subTotalVentas = totalNoSuj + totalExenta + totalGravada
- totalGravada ya incluye el IVA

## Código Clave en json_generator.py

### Método _get_receptor_consumidor_final (líneas 223-238)
```python
def _get_receptor_consumidor_final(self, partner, move):
    """Receptor para consumidor final - LÓGICA VALIDADA 29/06/2025"""
    return {
        "tipoDocumento": None,
        "numDocumento": None,
        "nrc": None,
        "nombre": "Consumidor final",
        "codActividad": None,
        "descActividad": None,
        "direccion": None,
        "telefono": None,
        "correo": partner.email or "consumidor@factura.gob.sv"
    }
```

### Lógica de Tributos en Resumen (líneas 474-487)
```python
# Aplicar lógica validada para tributos en resumen según LOGICA_VALIDADA.md
if fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
    # Para consumidor final: tributos = null (estrictamente según LOGICA_VALIDADA.md)
    tributos = None
else:
    # Para contribuyentes: calcular tributos normalmente
    tributos = []
    if total_iva > 0:
        tributos = [{
            "codigo": "20",
            "descripcion": "Impuesto al Valor Agregado 13%",
            "valor": utils.format_currency_amount(total_iva)
        }]
```

### Cálculo de IVA para Consumidor Final (líneas 419-423)
```python
if fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
    # Para consumidor final: totalGravada = precio con IVA (según ejemplo N1CO)
    total_gravada += line.price_subtotal
    # IVA se extrae del total: total * 13/113
    total_iva += (line.price_subtotal * 13 / 113)
```

## Configuración en Odoo

### 1. Posición Fiscal
- Debe tener marcado `l10n_sv_is_final_consumer = True`
- Se asigna automáticamente a clientes sin NIT

### 2. Tipo de Documento
- Código: 01
- Nombre: Factura
- Versión: 1

### 3. Secuencia de Número de Control
- Formato: DTE-01-XXXXXXXX-000000001
- Donde XXXXXXXX es el código del establecimiento y punto de venta

## Archivos Relacionados
- `/opt/odoo18-dte/addons/l10n_sv_edi_json/models/json_generator.py`
- `/opt/odoo18-dte/addons/l10n_sv_edi_json/models/dte_utils.py`
- `/opt/odoo18-dte/LOGICA_VALIDADA.md`