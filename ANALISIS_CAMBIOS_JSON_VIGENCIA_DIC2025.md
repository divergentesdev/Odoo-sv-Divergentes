# Análisis de Nuevas Versiones JSON - Ministerio de Hacienda El Salvador
## Fecha de Vigencia: 1 de Diciembre 2025

---

## 📋 RESUMEN EJECUTIVO

Se han identificado **CAMBIOS CRÍTICOS** en los schemas JSON oficiales descargados del portal de Hacienda (factura.gob.sv) que entrarán en vigencia el **1 de diciembre de 2025**.

El módulo actual de facturación electrónica **NO ES COMPATIBLE** con las nuevas versiones y requiere actualización inmediata.

---

## 🔄 CAMBIOS DE VERSIÓN POR TIPO DE DOCUMENTO

| Tipo DTE | Documento | Versión Actual | Nueva Versión | Estado |
|----------|-----------|----------------|---------------|---------|
| 01 | Factura (FC) | v1 | **v2** | ⚠️ REQUIERE CAMBIOS |
| 03 | CCF | v3 | **v4** | ❌ CAMBIOS CRÍTICOS |
| 05 | Nota de Crédito (NC) | v3 | **v4** | ❌ CAMBIOS CRÍTICOS |
| 06 | Nota de Débito (ND) | v3 | **v4** | ❌ CAMBIOS CRÍTICOS |
| 11 | Factura Exportación (FEX) | v1 | **v3** | ⚠️ REQUIERE CAMBIOS |
| 14 | Sujeto Excluido (FSE) | v1 | **v2** | ⚠️ REQUIERE CAMBIOS |

---

## 🚨 CAMBIOS CRÍTICOS DETALLADOS

### 1. CCF, NC, ND (Versión 4) - CAMBIOS MAYORES

#### 🔴 ELIMINACIÓN DEL CAMPO `extension`
- **Versión 3**: Incluía campo `extension` con datos de entrega/recibo
- **Versión 4**: **EL CAMPO HA SIDO ELIMINADO COMPLETAMENTE**
- **Impacto**: Los templates actuales incluirán un campo inválido que causará rechazo

```python
# ACTUAL (INCORRECTO para v4)
TEMPLATE_CCF_03 = {
    ...
    "extension": {  # ❌ ESTE CAMPO YA NO EXISTE EN V4
        "nombEntrega": "...",
        "docuEntrega": "...",
        "nombRecibe": "...",
        "docuRecibe": "...",
        "placaVehiculo": "...",
        "observaciones": "..."
    },
    ...
}

# NUEVO (CORRECTO para v4)
TEMPLATE_CCF_03 = {
    ...
    # Sin campo extension
    ...
}
```

#### 🟡 CAMBIO EN `documentoRelacionado`
- **Versión 3**: Podía ser `None` o tener estructura simple
- **Versión 4**: Ahora es **ARRAY** obligatorio con:
  - `minItems: 1`
  - `maxItems: 50`
  - Cada item debe tener: `tipoDocumento`, `tipoGeneracion`, `numeroDocumento`, `fechaEmision`

```python
# ACTUAL (INCORRECTO)
"documentoRelacionado": None

# NUEVO (CORRECTO para v4)
"documentoRelacionado": [
    {
        "tipoDocumento": "01",
        "tipoGeneracion": 1,
        "numeroDocumento": "0000000000000001",
        "fechaEmision": "2025-12-01"
    }
]
```

#### 🟡 CAMBIO EN VERSIÓN NUMÉRICA
```python
# ACTUAL
"version": 3

# NUEVO
"version": 4  # Debe ser exactamente 4
```

---

### 2. Factura (Versión 2) - CAMBIOS MODERADOS

#### 🟡 CAMBIO EN VERSIÓN NUMÉRICA
```python
# ACTUAL
"version": 1

# NUEVO
"version": 2
```

#### 🟡 CAMBIOS EN `resumen`
- **Campo eliminado**: `reteRenta` (ya no existe en v2)
- **Campo modificado**: `ivaRete1` → `ivaRete` (sin el "1")
- **Campo nuevo**: `observaciones` (opcional)

```python
# ACTUAL (INCORRECTO)
"resumen": {
    "reteRenta": 0.00,  # ❌ No existe en v2
    "ivaRete1": "0.00",  # ❌ Nombre incorrecto
    ...
}

# NUEVO (CORRECTO)
"resumen": {
    # "reteRenta": 0.00,  # Eliminado
    "ivaRete": "0.00",  # ✓ Nombre correcto
    "observaciones": None,  # Nuevo campo opcional
    ...
}
```

---

### 3. Exportación FEX (Versión 3) - CAMBIOS SIGNIFICATIVOS

#### 🟡 CAMBIO EN VERSIÓN NUMÉRICA
```python
# ACTUAL
"version": 1

# NUEVO
"version": 3
```

#### 🟡 ESTRUCTURA MODIFICADA
- **Nuevo campo root**: `documentoRelacionado` (ahora requerido)
- **Nuevo campo root**: `compraTercero` (para compras a terceros)
- **Eliminado**: Campo `totalNoSuj` del resumen
- **Nuevos campos en resumen**: 
  - `descuGravada`
  - `totalNoOnerosas`
  - `tributos`
  - `observaciones`

```python
# ACTUAL (INCOMPLETO)
TEMPLATE_EXPORTACION_11 = {
    "identificacion": {"version": 1, ...},  # ❌ Versión incorrecta
    "emisor": {...},
    "receptor": {...},
    "cuerpoDocumento": {...},
    "resumen": {
        "totalGravada": "...",
        "descuento": 0.00,  # ❌ Campo eliminado
        ...
    }
}

# NUEVO (CORRECTO)
TEMPLATE_EXPORTACION_11 = {
    "identificacion": {"version": 3, ...},  # ✓ Versión correcta
    "documentoRelacionado": [...],  # ✓ Nuevo campo
    "emisor": {...},
    "receptor": {...},
    "otrosDocumentos": None,
    "ventaTercero": None,
    "compraTercero": None,  # ✓ Nuevo campo
    "cuerpoDocumento": {...},
    "resumen": {
        "totalGravada": "...",
        "descuGravada": 0.00,  # ✓ Nuevo nombre
        "porcentajeDescuento": 0.00,
        "totalDescu": 0.00,
        "seguro": "...",
        "flete": "...",
        "tributos": None,  # ✓ Nuevo campo
        "montoTotalOperacion": "...",
        "totalNoGravado": 0.00,
        "totalNoOnerosas": 0.00,  # ✓ Nuevo campo
        "totalPagar": "...",
        "totalLetras": "...",
        "saldoFavor": 0.00,
        "condicionOperacion": "...",
        "pagos": [...],
        "codIncoterms": "...",
        "descIncoterms": "...",
        "numPagoElectronico": "...",
        "observaciones": None  # ✓ Nuevo campo
    }
}
```

---

### 4. Sujeto Excluido FSE (Versión 2) - CAMBIO CRÍTICO

#### 🔴 ELIMINACIÓN DEL CAMPO `sujetoExcluido`
- **Versión 1**: Incluía campo `sujetoExcluido` con datos del comprador
- **Versión 2**: **EL CAMPO HA SIDO ELIMINADO**, ahora usa `receptor`

```python
# ACTUAL (INCORRECTO para v2)
TEMPLATE_SUJETO_EXCLUIDO_14 = {
    ...
    "sujetoExcluido": {  # ❌ ESTE CAMPO YA NO EXISTE EN V2
        "tipoDocumento": "...",
        "numDocumento": "...",
        "nombre": "...",
        ...
    },
    ...
}

# NUEVO (CORRECTO para v2)
TEMPLATE_SUJETO_EXCLUIDO_14 = {
    "identificacion": {"version": 2, ...},
    "emisor": {...},
    "receptor": {  # ✓ Usar receptor en lugar de sujetoExcluido
        "tipoDocumento": "...",
        "numDocumento": "...",
        "nombre": "...",
        ...
    },
    "cuerpoDocumento": {...},
    "resumen": {
        "totalCompra": "...",
        "descu": 0.00,
        "totalDescu": 0.00,
        "totalPagar": "...",
        "totalLetras": "...",
        "condicionOperacion": "..."
    }
}
```

---

## 📝 ARCHIVOS QUE REQUIEREN MODIFICACIÓN

### Prioridad CRÍTICA (Bloqueantes)

1. **`/workspace/addons/templates_oficiales_mh.py`**
   - `TEMPLATE_CCF_03`: Eliminar `extension`, cambiar versión a 4
   - `TEMPLATE_NOTA_CREDITO_05`: Eliminar `extension`, cambiar versión a 4
   - `TEMPLATE_NOTA_DEBITO_06`: Eliminar `extension`, cambiar versión a 4
   - `TEMPLATE_FACTURA_01`: Cambiar versión a 2, ajustar campos resumen
   - `TEMPLATE_EXPORTACION_11`: Cambiar versión a 3, reestructurar completamente
   - `TEMPLATE_SUJETO_EXCLUIDO_14`: Cambiar versión a 2, reemplazar `sujetoExcluido` por `receptor`

2. **`/workspace/addons/l10n_sv_edi_json/models/json_generator.py`**
   - Validar que no se esté generando el campo `extension` para CCF/NC/ND
   - Actualizar lógica de `documentoRelacionado` para usar array
   - Actualizar campos de resumen según nueva estructura

3. **`/workspace/addons/l10n_sv_edi_json/models/dte_utils.py`**
   - Revisar validaciones de versión
   - Actualizar reglas de negocio para nuevos campos

### Prioridad ALTA (Recomendados)

4. **`/workspace/addons/l10n_sv_edi_json/data/json_template_data.xml`**
   - Actualizar datos semilla si existen referencias a estructuras viejas

5. **`/workspace/addons/l10n_sv_reports/`**
   - Verificar que los reportes no dependan de campos eliminados

---

## ✅ CHECKLIST DE VALIDACIÓN

### Para CCF, NC, ND (v4):
- [ ] Eliminar campo `extension` de todos los templates
- [ ] Cambiar `version` de 3 a 4
- [ ] Asegurar que `documentoRelacionado` sea array (no null)
- [ ] Validar que cada item del array tenga los 4 campos requeridos
- [ ] Remover referencia a `numPagoElectronico` en CCF (si aplica)

### Para Factura (v2):
- [ ] Cambiar `version` de 1 a 2
- [ ] Eliminar campo `reteRenta` del resumen
- [ ] Renombrar `ivaRete1` a `ivaRete`
- [ ] Agregar campo `observaciones` (opcional)

### Para Exportación FEX (v3):
- [ ] Cambiar `version` de 1 a 3
- [ ] Agregar campo `documentoRelacionado`
- [ ] Agregar campo `compraTercero`
- [ ] Actualizar estructura de `resumen` con nuevos campos
- [ ] Eliminar campo `descuento` (ahora es `descuGravada`)

### Para Sujeto Excluido FSE (v2):
- [ ] Cambiar `version` de 1 a 2
- [ ] Eliminar campo `sujetoExcluido`
- [ ] Usar campo `receptor` en su lugar
- [ ] Mantener estructura simplificada

---

## 🧪 PRUEBAS REQUERIDAS

1. **Pruebas Unitarias**
   - Generar JSON para cada tipo de DTE con nuevas versiones
   - Validar contra schemas oficiales v2/v3/v4
   - Verificar que no haya campos eliminados

2. **Pruebas de Integración**
   - Conectar con ambiente de certificación del MH
   - Enviar documentos de prueba de cada tipo
   - Validar aceptación sin errores de schema

3. **Pruebas de Regresión**
   - Verificar que documentos ya generados no se vean afectados
   - Validar backward compatibility si es necesario

---

## 📅 CRONOGRAMA RECOMENDADO

| Semana | Actividad |
|--------|-----------|
| Semana 1 | Actualizar templates_oficiales_mh.py |
| Semana 2 | Actualizar json_generator.py y validaciones |
| Semana 3 | Pruebas unitarias y ajustes |
| Semana 4 | Pruebas en ambiente de certificación MH |
| Semana 5 | Despliegue a producción (antes de Dic 1) |

---

## 🔗 REFERENCIAS

- **Portal Oficial**: https://factura.gob.sv/informacion-tecnica-y-funcional/
- **JSON Schemas Oficiales**: Descargar desde el portal (archivo: `3-json-schemas-anexo-al-manual-tecnico...`)
- **Fecha Límite**: 1 de diciembre de 2025

---

## ⚠️ ADVERTENCIA IMPORTANTE

**NO IMPLEMENTAR EN PRODUCCIÓN SIN PRUEBAS PREVIAS**

Estos cambios son **ROMPEN COMPATIBILIDAD** con la versión actual. Se recomienda:

1. Crear rama específica para migración v2/v3/v4
2. Implementar cambios gradualmente por tipo de documento
3. Mantener capacidad de generar versiones anteriores durante transición
4. Coordinar con contador/certificador antes de desplegar

---

*Documento generado el: Agosto 2025*
*Fuente: Schemas oficiales descargados de factura.gob.sv*
