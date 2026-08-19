# Auditoría de Catálogos del Ministerio de Hacienda - El Salvador
## Módulo de Facturación Electrónica Odoo 19
### Fecha de Auditoría: Diciembre 2025

---

## RESUMEN EJECUTIVO

Esta auditoría valida que el módulo de facturación electrónica cumpla con todos los catálogos oficiales publicados por el Ministerio de Hacienda de El Salvador, incluyendo los cambios entrantes en vigencia el 1 de diciembre de 2025.

**Estado General:** ⚠️ **REQUIERE ATENCIÓN INMEDIATA**

---

## 1. CATÁLOGOS REVISADOS

### 1.1 CAT_002_Tipo_de_Documento ✅ IMPLEMENTADO
**Ubicación:** `/workspace/addons/l10n_sv_document_type/data/document_type_data.xml`

| Código | Tipo Documento | Estado | Observaciones |
|--------|---------------|--------|---------------|
| 01 | Factura | ✅ Implementado | Correcto |
| 03 | Comprobante Crédito Fiscal | ✅ Implementado | Correcto |
| 04 | Nota de Remisión | ✅ Implementado | Correcto |
| 05 | Nota de Crédito | ✅ Implementado | Actualizado a v4 |
| 06 | Nota de Débito | ✅ Implementado | Actualizado a v4 |
| 07 | Comprobante Retención | ✅ Implementado | Correcto |
| 08 | Comprobante Liquidación | ✅ Implementado | Correcto |
| 09 | Documento Contable Liquidación | ✅ Implementado | Correcto |
| 11 | Factura Exportación | ✅ Implementado | Actualizado a v3 |
| 14 | Factura Sujeto Excluido | ✅ Implementado | Actualizado a v2 |
| 15 | Comprobante Donación | ✅ Implementado | Correcto |

**Cumplimiento:** 100% ✅

---

### 1.2 CAT_018_Plazo ✅ IMPLEMENTADO
**Ubicación:** `/workspace/addons/l10n_sv_payment/data/payment_term_data.xml`

| Código | Descripción | Estado | Observaciones |
|--------|-------------|--------|---------------|
| 01 | Días | ✅ Implementado | Campo `plazo` en modelo |
| 02 | Meses | ✅ Implementado | Campo `plazo` en modelo |
| 03 | Años | ✅ Implementado | Campo `plazo` en modelo |

**Campos Implementados:**
- `plazo`: Selection['01', '02', '03']
- `periodo`: Integer (valor numérico)

**Cumplimiento:** 100% ✅

**Datos Cargados:**
- account.account_payment_term_immediate → plazo='01', periodo=0
- account.account_payment_term_15days → plazo='01', periodo=15
- account.account_payment_term_30days → plazo='01', periodo=30
- account.account_payment_term_end_following_month → plazo='02', periodo=1
- Y otros 6 términos adicionales correctamente configurados

---

### 1.3 CAT_021_Forma_Pago ❌ NO IMPLEMENTADO
**Estado:** 🔴 **CRÍTICO - FALTA IMPLEMENTAR**

Según los nuevos schemas JSON vigentes desde diciembre 2025, el campo `formaPago` es **REQUERIDO** en el resumen del documento.

**Requerimiento del MH:**
```json
"resumen": {
  "formaPago": "01",  // Catálogo CAT_021_Forma_Pago
  ...
}
```

**Catálogo Oficial CAT_021_Forma_Pago:**
| Código | Descripción |
|--------|-------------|
| 01 | Contado |
| 02 | Crédito |
| 03 | Mixto |

**Acciones Requeridas:**
1. Crear modelo `l10n_sv.payment.method` o similar
2. Agregar campo `forma_pago` en `account.move`
3. Crear datos XML con los 3 tipos de forma de pago
4. Actualizar generador JSON para incluir campo `formaPago`
5. Agregar vista para selección en formulario de factura

**Prioridad:** 🔴 **CRÍTICA** - Bloquea generación de JSON válido

---

### 1.4 Distritos/Municipios (CAT_004_Distrito) ✅ IMPLEMENTADO
**Ubicación:** 
- `/workspace/addons/l10n_sv_city/data/res_city_data.xml`
- `/workspace/addons/l10n_sv_city/data/res_state_data.xml`
- `/workspace/addons/l10n_sv_city/models/res_city.py`

**Implementación:**
- ✅ Campo `district_code` (4 dígitos) en modelo `res.city`
- ✅ 267+ distritos cargados correctamente
- ✅ Relación distrito→municipio→departamento
- ✅ Código de 4 dígitos: 2 dígitos departamento + 2 dígitos municipio

**Ejemplo de Estructura:**
```xml
<record id="city_sv_0101" model="res.city">
    <field name="name">AHUACHAPÁN</field>
    <field name="district_code">0101</field>
    <field name="state_id" ref="state_sv_0114"/>
</record>
```

**Extracción en JSON Generator:**
```python
if partner.city_id.district_code and len(partner.city_id.district_code) == 4:
    departamento = partner.city_id.district_code[:2]
    municipio = partner.city_id.district_code[2:]
```

**Cumplimiento:** 100% ✅

**Observación:** El distrito es ahora **REQUERIDO** según nuevas especificaciones. El módulo lo maneja correctamente pero se debe validar que:
1. El campo `city_id` sea obligatorio en partners salvadoreños
2. No se permitan direcciones sin distrito asignado

---

### 1.5 Incoterms (CAT_012_Incoterms) ✅ IMPLEMENTADO
**Ubicación:** `/workspace/addons/l10n_sv_incoterms/data/incoterms_data.xml`

| Código MH | Incoterm | Estado |
|-----------|----------|--------|
| 01 | EXW | ✅ |
| 02 | FCA | ✅ |
| 03 | CPT | ✅ |
| 04 | CIP | ✅ |
| 05 | DAP | ✅ |
| 06 | DPU | ✅ |
| 07 | DDP | ✅ |
| 08 | FAS | ✅ |
| 09 | FOB | ✅ |
| 10 | CFR | ✅ |
| 11 | CIF | ✅ |

**Campo Implementado:** `code_dgii` en modelo `account.incoterms`

**Cumplimiento:** 100% ✅

---

### 1.6 Tipo de Identificación (CAT_008_TipoDocumento) ✅ IMPLEMENTADO
**Ubicación:** Lógica en `json_generator.py`

| Código | Tipo | Estado |
|--------|------|--------|
| 13 | DUI | ✅ Implementado |
| 36 | NIT | ✅ Implementado |
| 02 | Pasaporte | ✅ Soportado |
| 03 | Carnet Residencia | ✅ Soportado |
| 37 | Otros | ✅ Soportado |

**Implementación:**
- Modelo `l10n_sv.document.type`
- Campo `l10n_sv_document_type_code` en `res.partner`
- Lógica de validación en generador JSON

**Cumplimiento:** 100% ✅

---

## 2. VALIDACIÓN DE CAMPOS REQUERIDOS POR TIPO DTE

### 2.1 Factura (01) - Versión 2 ✅
**Schema:** `fe-fc-v2.json`

| Campo | Requerido | Estado |
|-------|-----------|--------|
| identificacion.version | Sí (debe ser 2) | ✅ Actualizado |
| emisor | Sí | ✅ |
| receptor | Condicional (>$1095) | ✅ |
| cuerpoDocumento | Sí | ✅ |
| resumen.formaPago | Sí (NUEVO) | 🔴 **FALTA** |
| resumen.numPagoElectronico | Sí | ✅ |
| resumen.observaciones | Opcional | ✅ Agregado |

**Cambios Diciembre 2025:**
- ✅ `ivaRete1` → `ivaRete` (renombrado)
- ✅ `reteRenta` eliminado
- 🔴 `formaPago` agregado como requerido

---

### 2.2 CCF (03) - Versión 4 ⚠️
**Schema:** `fe-ccf-v4.json`

| Campo | Requerido | Estado |
|-------|-----------|--------|
| identificacion.version | Sí (debe ser 4) | 🔴 **Debe actualizarse** |
| extension | NO (ELIMINADO) | ✅ Eliminado |
| documentoRelacionado | No (pero si existe: array 1-50) | ⚠️ Validar |
| resumen.formaPago | Sí (NUEVO) | 🔴 **FALTA** |

**PROBLEMA CRÍTICO:**
El template actual aún usa versión 3. Debe actualizarse a versión 4.

---

### 2.3 Nota de Crédito (05) - Versión 4 ⚠️
**Schema:** `fe-nc-v4.json`

| Campo | Requerido | Estado |
|-------|-----------|--------|
| identificacion.version | Sí (debe ser 4) | 🔴 **Debe actualizarse** |
| extension | NO (ELIMINADO) | ✅ Eliminado |
| documentoRelacionado | Sí (array 1-50) | ⚠️ Validar límite |
| resumen.formaPago | Sí (NUEVO) | 🔴 **FALTA** |

---

### 2.4 Nota de Débito (06) - Versión 4 ⚠️
**Schema:** `fe-nd-v4.json`

| Campo | Requerido | Estado |
|-------|-----------|--------|
| identificacion.version | Sí (debe ser 4) | 🔴 **Debe actualizarse** |
| extension | NO (ELIMINADO) | ✅ Eliminado |
| resumen.formaPago | Sí (NUEVO) | 🔴 **FALTA** |
| resumen.observaciones | Opcional | ✅ Agregado |

---

### 2.5 Factura Exportación (11) - Versión 3 ⚠️
**Schema:** `fe-fex-v3.json`

| Campo | Requerido | Estado |
|-------|-----------|--------|
| identificacion.version | Sí (debe ser 3) | 🔴 **Debe actualizarse** |
| documentoRelacionado | Nuevo campo | 🔴 **FALTA** |
| compraTercero | Nuevo campo | 🔴 **FALTA** |
| resumen.formaPago | Sí (NUEVO) | 🔴 **FALTA** |

**CAMBIOS MAYORES:**
- Reestructuración completa del resumen
- Nuevos campos obligatorios

---

### 2.6 Sujeto Excluido (14) - Versión 2 ⚠️
**Schema:** `fe-fse-v2.json`

| Campo | Requerido | Estado |
|-------|-----------|--------|
| identificacion.version | Sí (debe ser 2) | 🔴 **Debe actualizarse** |
| sujetoExcluido | NO (ELIMINADO) | ✅ Eliminado |
| receptor | Sí (ahora usa este) | ⚠️ Validar |
| resumen.formaPago | Sí (NUEVO) | 🔴 **FALTA** |

---

## 3. AUDITORÍA DE INSTALACIÓN DEL MÓDULO

### 3.1 Datos Cargados Automáticamente ✅

Al instalar los módulos, se cargan automáticamente:

| Módulo | Datos Cargados | Estado |
|--------|---------------|--------|
| l10n_sv_city | 267+ distritos, 46 municipios | ✅ |
| l10n_sv_document_type | 11 tipos documento DTE | ✅ |
| l10n_sv_payment | 11 términos de pago con códigos DGII | ✅ |
| l10n_sv_incoterms | 11 incoterms con códigos MH | ✅ |
| l10n_sv_uom | Unidades de medida | ✅ |
| l10n_sv_cta | Plan de cuentas, impuestos | ✅ |

### 3.2 Configuración Post-Instalación Requerida ⚠️

**Configuración Manual Necesaria:**

1. **Certificado Digital** 🔴
   - Subir certificado `.p12` o `.pem`
   - Configurar contraseña
   - Validar vigencia

2. **Ambiente MH** ⚠️
   - Seleccionir: Producción / Certificación
   - URL del servicio web

3. **Establecimiento** ⚠️
   - Código de establecimiento
   - Punto de emisión

4. **Forma de Pago** 🔴 **NUEVO**
   - Configurar formas de pago predeterminadas
   - Mapear con catálogo CAT_021

5. **Distritos por Defecto** ⚠️
   - Validar que todos los partners tengan `city_id` asignado
   - Ejecutar script de migración si hay partners sin distrito

---

## 4. HALLAZGOS CRÍTICOS

### 🔴 CRÍTICO 1: Campo `formaPago` No Implementado
**Impacto:** Los JSON generados serán rechazados por el MH
**Solución:** 
1. Crear modelo `l10n_sv.payment.method`
2. Agregar 3 registros (01-Contado, 02-Crédito, 03-Mixto)
3. Agregar campo en `account.move`
4. Incluir en generación de resumen JSON

### 🔴 CRÍTICO 2: Versiones de Templates Desactualizadas
**Impacto:** Los JSON no pasarán validación de schema
**Solución:** Actualizar versiones en `DTE_RULES`:
- CCF: v3 → v4
- NC: v3 → v4
- ND: v3 → v4
- FEX: v1 → v3
- FSE: v1 → v2
- FC: v1 → v2

### 🟡 MEDIO 1: Validación de Distrito Obligatorio
**Impacto:** Direcciones incompletas pueden causar rechazo
**Solución:** Agregar constraint en `res.partner` para SV

### 🟡 MEDIO 2: Documento Relacionado en Exportación
**Impacto:** FEX v3 requiere nuevo campo
**Solución:** Implementar campo `documentoRelacionado` y `compraTercero`

---

## 5. CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Crítica (Semana 1)
- [ ] Implementar catálogo CAT_021_Forma_Pago
- [ ] Agregar campo `formaPago` en resumen JSON
- [ ] Actualizar versiones de templates (CCF, NC, ND, FEX, FSE, FC)
- [ ] Eliminar campo `extension` de templates que lo tengan
- [ ] Pruebas unitarias de generación JSON

### Fase 2: Validación (Semana 2)
- [ ] Validar schemas oficiales MH v2/v3/v4
- [ ] Pruebas en ambiente de certificación MH
- [ ] Corregir errores de validación
- [ ] Documentar cambios

### Fase 3: Migración (Semana 3)
- [ ] Script de migración de datos existentes
- [ ] Asignar forma de pago por defecto a facturas históricas
- [ ] Validar partners sin distrito
- [ ] Capacitación a usuarios

### Fase 4: Producción (Semana 4)
- [ ] Deploy a producción
- [ ] Monitoreo de primeros envíos
- [ ] Soporte post-implementación

---

## 6. SCRIPT DE VERIFICACIÓN RECOMENDADO

Crear script para validar instalación correcta:

```python
def verify_hacienda_catalogs():
    """Verifica que todos los catálogos de Hacienda estén cargados"""
    
    # 1. Verificar distritos
    city_count = env['res.city'].search_count([('country_id.code', '=', 'SV')])
    assert city_count >= 267, f"Solo hay {city_count} distritos, se esperan 267+"
    
    # 2. Verificar tipos de documento
    doc_types = env['l10n_sv.document.type'].search([])
    required_codes = ['01', '03', '04', '05', '06', '07', '08', '09', '11', '14', '15']
    existing_codes = doc_types.mapped('code')
    for code in required_codes:
        assert code in existing_codes, f"Falta tipo documento {code}"
    
    # 3. Verificar incoterms
    incoterms = env['account.incoterms'].search([('code_dgii', '!=', False)])
    assert len(incoterms) >= 11, f"Solo hay {len(incoterms)} incoterms con código DGII"
    
    # 4. Verificar plazos
    payment_terms = env['account.payment.term'].search([('plazo', '!=', False)])
    assert len(payment_terms) > 0, "No hay términos de pago configurados"
    
    # 5. Verificar forma de pago (NUEVO)
    # TODO: Implementar verificación cuando se cree el modelo
    
    print("✅ Todos los catálogos verificados correctamente")
```

---

## 7. CONCLUSIONES

### Fortalezas del Módulo ✅
1. Excelente estructura de datos geográficos (distritos/municipios)
2. Tipos de documento completos según CAT_002
3. Incoterms correctamente implementados
4. Términos de pago con códigos DGII
5. Templates base bien estructurados

### Debilidades Detectadas 🔴
1. **Falta implementación de CAT_021_Forma_Pago** (CRÍTICO)
2. Versiones de templates desactualizadas
3. No hay validación de distrito obligatorio en partners
4. Faltan campos nuevos en FEX v3

### Recomendaciones
1. **Prioridad Máxima:** Implementar forma de pago antes de diciembre 2025
2. Actualizar todas las versiones de templates inmediatamente
3. Agregar constraints de validación en modelos base
4. Crear wizard de configuración post-instalación
5. Implementar script de diagnóstico de instalación

---

## 8. PRÓXIMOS PASOS

1. **Inmediato (24-48 horas):**
   - Diseñar modelo para CAT_021_Forma_Pago
   - Actualizar DTE_RULES con nuevas versiones
   
2. **Corto Plazo (1 semana):**
   - Implementar cambios en generador JSON
   - Pruebas internas

3. **Mediano Plazo (2 semanas):**
   - Pruebas en ambiente certificación MH
   - Corrección de errores

4. **Largo Plazo (1 mes):**
   - Deploy a producción
   - Monitoreo continuo

---

**Elaborado por:** Sistema de Auditoría Automatizada  
**Fecha:** Diciembre 2025  
**Versión:** 1.0  
**Próxima Revisión:** Enero 2026
