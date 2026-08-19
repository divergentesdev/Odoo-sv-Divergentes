# 📋 AUDITORÍA DE RETENCIONES Y PERCEPCIONES - FACTURACIÓN ELECTRÓNICA EL SALVADOR

## 🎯 OBJETIVO
Validar que el módulo de facturación electrónica:
1. **NO tenga impuestos hardcoded** (ej. `0.13` para IVA)
2. **Tome la configuración de impuestos desde los modelos de Odoo**
3. **Implemente correctamente retenciones (IVA y Renta)**
4. **Implemente correctamente percepciones (IVA Percibido)**
5. **Cumpla con esquemas JSON vigentes desde diciembre 2025**

---

## 🔍 HALLAZGOS CRÍTICOS

### ❌ PROBLEMAS DETECTADOS

#### 1. **IMPUESTOS HARDCODED - ALTA PRIORIDAD**

**Ubicación:** `/workspace/addons/l10n_sv_edi_json/models/json_generator.py`

| Línea | Código Problemático | Impacto |
|-------|---------------------|---------|
| 667 | `float(item['ventaGravada']) * 0.13` | Solo log, no crítico |
| 1285 | `line.price_unit * 0.13` | **Cálculo directo sin usar tax.amount** |
| 1312 | `venta_gravada * 0.13` | **Cálculo directo sin usar tax.amount** |
| 1393 | `base_gravada * 0.13` | **Cálculo directo sin usar tax.amount** |
| 1399 | `line.price_subtotal * 0.13` | **Cálculo directo sin usar tax.amount** |
| 1413 | `line.price_subtotal * 0.13` | **Cálculo directo sin usar tax.amount** |

**Problema:** El código asume que IVA es siempre 13%, pero:
- La tasa podría cambiar por ley
- No respeta la configuración del impuesto en Odoo (`tax.amount`)
- Dificulta mantenimiento y auditoría

**Solución Requerida:**
```python
# ❌ INCORRECTO (hardcoded)
iva_item = utils.format_currency_amount(venta_gravada * 0.13)

# ✅ CORRECTO (desde configuración)
iva_tax = self.env['account.tax'].search([('code_dgii', '=', '20')], limit=1)
iva_rate = iva_tax.amount / 100 if iva_tax else 0.13
iva_item = utils.format_currency_amount(venta_gravada * iva_rate)
```

---

#### 2. **RETENCIONES - IMPLEMENTACIÓN PARCIAL**

**Estado Actual:**
- ✅ Campo `l10n_sv_retention_amount` definido en `account.move`
- ✅ Campo `l10n_sv_retention_rate` definido en `account.move`
- ✅ Impuestos de retención configurados en datos XML (`tax_retencion_iva`, `tax_retencion_renta_*`)
- ✅ Modelo `account.tax` extiende con `l10n_sv_is_withholding` y `l10n_sv_withholding_type`

**Problemas Detectados:**

##### 2.1 Cálculo Automático de Retenciones
**Ubicación:** `json_generator.py` línea 835
```python
"ivaRete": utils.format_summary_amount(move.l10n_sv_retention_amount) if move.l10n_sv_retention_amount else 0.00
```

**Problema:** 
- El campo `l10n_sv_retention_amount` es manual, no se calcula automáticamente
- No hay lógica que detecte si el partner es agente de retención
- No se calcula basado en impuestos de retención aplicados

**Solución Requerida:**
```python
# Calcular retenciones automáticamente desde líneas
def _calculate_retentions(self, move):
    retention_vat = 0.0
    retention_income = 0.0
    
    for line in move.invoice_line_ids:
        for tax in line.tax_ids:
            if tax.l10n_sv_is_withholding:
                if tax.l10n_sv_withholding_type == 'vat':
                    retention_vat += abs(line.price_subtotal * tax.amount / 100)
                elif tax.l10n_sv_withholding_type == 'income':
                    retention_income += abs(line.price_subtotal * tax.amount / 100)
    
    return retention_vat, retention_income
```

##### 2.2 Campo `reteRenta` Eliminado pero Documentado
**Ubicación:** `json_generator.py` línea 836
```python
# "reteRenta": 0.00,  # ELIMINADO en v2/v4 (desde 01/12/2025)
```

**Validación:** ✅ CORRECTO - El campo está comentado correctamente según nuevas versiones JSON v2/v4

---

#### 3. **PERCEPCIONES (IVA Percibido) - IMPLEMENTACIÓN INCOMPLETA**

**Estado Actual:**
- ✅ Campo `ivaPerci1` agregado al resumen para CCF (línea 851)
- ✅ Marcado como requerido en `DTE_RULES` para CCF (línea 43)

**Problemas Detectados:**

##### 3.1 Valor Hardcoded a Cero
**Ubicación:** `json_generator.py` líneas 851, 1488
```python
resumen["ivaPerci1"] = 0.00  # IVA Percibido requerido para CCF
```

**Problema:**
- Siempre es 0.00, no se calcula desde impuestos de percepción
- No hay modelo `account.tax` para percepciones (solo retenciones)
- No hay campo en `account.move` para almacenar percepciones

**Solución Requerida:**
1. Agregar campo `l10n_sv_perception_amount` en `account.move`
2. Agregar impuestos de percepción en datos XML
3. Extender `account.tax` con `l10n_sv_is_perception`
4. Calcular automáticamente desde líneas

```python
# En account_move.py
l10n_sv_perception_amount = fields.Monetary(
    string='Monto Percepción',
    currency_field='currency_id',
    help='Monto de percepción de IVA aplicado'
)

# En json_generator.py
resumen["ivaPerci1"] = utils.format_summary_amount(move.l10n_sv_perception_amount)
```

---

#### 4. **INCONSISTENCIA EN CÁLCULO DE IVA**

**Problema:** Múltiples fórmulas diferentes para calcular IVA

| Ubicación | Fórmula | Contexto |
|-----------|---------|----------|
| Línea 702 | `base_gravada * 13 / 113` | Consumidor final (extraer IVA incluido) |
| Línea 712 | `line.price_subtotal * 13 / 113` | FCF con precio incluido |
| Línea 718 | `utils.calculate_iva_amount(line.price_subtotal)` | Contribuyente normal |
| Línea 1293 | `venta_gravada * 13 / 113` | FCF en cuerpo documento |
| Línea 1393 | `base_gravada * 0.13` | Resumen FCF |
| Línea 1399 | `line.price_subtotal * 0.13` | Resumen contribuyente |

**Inconsistencia:**
- Algunas usan `13/113` (para extraer IVA de precio incluido)
- Otras usan `0.13` (para calcular IVA sobre base)
- Debería usarse consistentemente `tax.amount` desde configuración

**Solución:**
```python
# Unificar usando método de utils que respeta configuración
iva_amount = utils.calculate_iva_from_tax(tax, base_amount)
```

---

## ✅ ASPECTOS CORRECTOS

### 1. **Estructura de Datos de Impuestos**
- ✅ Modelo `account.tax` extendido con `code_dgii`
- ✅ Impuestos configurados vía XML con códigos DGII correctos
- ✅ Grupos de impuestos para retenciones definidos

### 2. **Campos de Retención en Account Move**
- ✅ `l10n_sv_retention_amount` definido correctamente
- ✅ `l10n_sv_retention_rate` definido correctamente
- ✅ Campos monetarios con currency_field apropiado

### 3. **Actualización a Nuevas Versiones JSON**
- ✅ Campo `ivaRete` renombrado de `ivaRete1` (v2/v4)
- ✅ Campo `reteRenta` eliminado correctamente (comentado)
- ✅ Versión dinámica según tipo de documento

---

## 📝 PLAN DE ACCIÓN

### Fase 1: Eliminar Hardcoding de Impuestos (PRIORIDAD CRÍTICA)

**Archivos a modificar:**
- `/workspace/addons/l10n_sv_edi_json/models/json_generator.py`

**Cambios:**
1. Reemplazar `0.13` por `tax.amount / 100`
2. Crear método `_get_iva_rate_from_tax()` que obtenga tasa desde configuración
3. Usar `utils.calculate_iva_amount()` consistentemente

**Código ejemplo:**
```python
def _get_iva_tax_rate(self, move):
    """Obtiene tasa de IVA desde configuración de impuestos"""
    iva_tax = self.env['account.tax'].search([
        ('code_dgii', '=', '20'),
        ('company_id', '=', move.company_id.id)
    ], limit=1)
    return iva_tax.amount / 100 if iva_tax else 13.0 / 100

# Uso en cálculos
iva_rate = self._get_iva_tax_rate(move)
iva_item = utils.format_currency_amount(venta_gravada * iva_rate)
```

---

### Fase 2: Implementar Cálculo Automático de Retenciones

**Archivos a modificar:**
- `/workspace/addons/l10n_sv_document_type/models/account_move.py`
- `/workspace/addons/l10n_sv_edi_json/models/json_generator.py`

**Cambios:**
1. Agregar método `_compute_retention_amounts()` en account.move
2. Calcular automáticamente basado en impuestos de retención en líneas
3. Hacer campos `l10n_sv_retention_amount` computados (no manuales)

**Código ejemplo:**
```python
@api.depends('invoice_line_ids.tax_ids', 'invoice_line_ids.price_subtotal')
def _compute_retention_amounts(self):
    for move in self:
        retention_vat = 0.0
        retention_income = 0.0
        
        for line in move.invoice_line_ids:
            if line.display_type not in ('line_section', 'line_note'):
                for tax in line.tax_ids:
                    if tax.l10n_sv_is_withholding:
                        amount = abs(line.price_subtotal * tax.amount / 100)
                        if tax.l10n_sv_withholding_type == 'vat':
                            retention_vat += amount
                        elif tax.l10n_sv_withholding_type == 'income':
                            retention_income += amount
        
        move.l10n_sv_retention_amount = retention_vat + retention_income
```

---

### Fase 3: Implementar Percepciones

**Archivos nuevos/modificados:**
- `/workspace/addons/l10n_sv_fiscal_position/data/account_tax_data.xml` (agregar impuestos percepción)
- `/workspace/addons/l10n_sv_fiscal_position/models/account_tax.py` (agregar campo is_perception)
- `/workspace/addons/l10n_sv_document_type/models/account_move.py` (agregar campo perception)
- `/workspace/addons/l10n_sv_edi_json/models/json_generator.py` (usar campo perception)

**Cambios:**
1. Agregar `l10n_sv_is_perception` en account.tax
2. Crear impuestos de percepción en datos XML
3. Agregar campo `l10n_sv_perception_amount` en account.move
4. Calcular automáticamente en `_compute_perception_amounts()`
5. Usar en resumen JSON: `resumen["ivaPerci1"] = move.l10n_sv_perception_amount`

---

### Fase 4: Unificar Cálculo de IVA

**Archivo a modificar:**
- `/workspace/addons/l10n_sv_edi_json/models/dte_utils.py`

**Agregar método:**
```python
def calculate_iva_from_tax(self, tax_ids, base_amount):
    """Calcula IVA usando configuración de impuestos"""
    for tax in tax_ids:
        if hasattr(tax, 'code_dgii') and tax.code_dgii == '20':
            if tax.price_include:
                # Extraer IVA de precio incluido
                return base_amount * tax.amount / (100 + tax.amount)
            else:
                # Calcular IVA sobre base
                return base_amount * tax.amount / 100
    return 0.0
```

---

## 🧪 PRUEBAS REQUERIDAS

### Prueba 1: Validar No-Hardcoding
```python
# Test unitario
def test_no_hardcoded_taxes():
    """Verifica que no haya tasas hardcoded en json_generator"""
    with open('json_generator.py', 'r') as f:
        content = f.read()
        # Buscar patrones de hardcoded
        assert '* 0.13' not in content or '* 0.13' solo en comentarios
        assert '13 / 113' solo donde corresponda (IVA incluido)
```

### Prueba 2: Cálculo Automático Retenciones
```python
# Caso: Factura con retención 1%
move = create_invoice(amount=1000, withholding_tax=True)
move.action_post()
assert move.l10n_sv_retention_amount == 10.0  # 1% de 1000
```

### Prueba 3: Percepciones en CCF
```python
# Caso: CCF con percepción
ccf = create_ccf(amount=1000, perception_tax=True)
json_data = generator.generate_json_dte(ccf.id)
assert json_data['resumen']['ivaPerci1'] > 0
```

---

## 📊 RESUMEN DE CUMPLIMIENTO

| Requisito | Estado | Prioridad |
|-----------|--------|-----------|
| No hardcoded taxes | ❌ Parcial | **CRÍTICA** |
| Retenciones automáticas | ⚠️ Parcial | **ALTA** |
| Percepciones implementadas | ❌ No | **ALTA** |
| Campos JSON actualizados | ✅ Sí | - |
| Cálculo consistente IVA | ❌ No | **MEDIA** |
| Configuración desde modelos | ⚠️ Parcial | **ALTA** |

---

## 🎯 CONCLUSIÓN

El módulo tiene una **base sólida** pero requiere correcciones críticas:

1. **Eliminar hardcoded de 0.13** inmediatamente (riesgo de mantenimiento y auditoría)
2. **Automatizar cálculo de retenciones** desde impuestos configurados
3. **Implementar percepciones** completamente (requerido para CCF)
4. **Unificar fórmulas de IVA** para consistencia

**Tiempo estimado de implementación:** 8-12 horas
**Riesgo de no corregir:** Rechazo de DTE en certificación MH, problemas en auditorías fiscales

---

*Generado: 2025-12-XX*
*Auditor: Sistema de Revisión de Código*
*Módulo: l10n_sv_edi_json, l10n_sv_document_type, l10n_sv_fiscal_position*
