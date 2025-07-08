# REGLAS CRÍTICAS DE SEPARACIÓN POR TIPO DE DOCUMENTO DTE

## ⚠️ ADVERTENCIA CRÍTICA
**NUNCA MEZCLAR LÓGICAS ENTRE TIPOS DE DOCUMENTO**

Cada tipo de documento DTE tiene reglas específicas que NO deben interferir entre sí.

## 📋 TIPOS DE DOCUMENTO Y SUS REGLAS

### 1. CCF - CRÉDITO FISCAL (document_type = '03')
```
Esquema: fe-ccf-v1.json
Reglas específicas:
- codTributo: SIEMPRE null
- tributos: ["20"] si hay IVA, null si no hay IVA
- ivaItem: NO se incluye en el JSON (CCF no tiene este campo)
- Cálculo IVA: venta_gravada * 0.13
```

### 2. FCF - FACTURA CONSUMIDOR FINAL (document_type = '01' + is_final_consumer = true)
```
Esquema: fe-fc-v1.json
Reglas específicas:
- codTributo: SIEMPRE null
- tributos: ["20"] si hay IVA, null si no hay IVA (SEGÚN ERROR MH)
- ivaItem: OBLIGATORIO incluir en JSON
- Cálculo IVA: venta_gravada * 0.13
- Receptor: puede tener datos null para montos < $1,095
```

### 3. FACTURA NORMAL (document_type = '01' + is_final_consumer = false)
```
Esquema: fe-factura-v1.json
Reglas específicas:
- codTributo: SIEMPRE null
- tributos: ["20"] si hay IVA, null si no hay IVA
- ivaItem: OBLIGATORIO incluir en JSON
- Cálculo IVA: venta_gravada * 0.13
- Receptor: datos obligatorios del contribuyente
```

## 🔒 IMPLEMENTACIÓN ESTRICTA

### Estructura de Código OBLIGATORIA:
```python
if document_type == '03':
    # ===== SOLO LÓGICA CCF =====
    # NO mezclar con otras lógicas
    
elif document_type == '01':
    if fiscal_position.l10n_sv_is_final_consumer:
        # ===== SOLO LÓGICA FCF =====
        # NO mezclar con CCF ni Factura Normal
    else:
        # ===== SOLO LÓGICA FACTURA NORMAL =====
        # NO mezclar con CCF ni FCF
else:
    # ===== OTROS TIPOS =====
```

## ❌ ANTI-PATRONES PROHIBIDOS

### 1. Verificar FCF dentro de lógica genérica
```python
# ❌ MAL - FCF verificado dentro de lógica general
if tributos:
    if fiscal_position.l10n_sv_is_final_consumer:
        # ESTO CAUSA CONFLICTOS
```

### 2. Múltiples condiciones para el mismo documento
```python
# ❌ MAL - Múltiples paths para FCF
elif fiscal_position.l10n_sv_is_final_consumer:
    # Primera lógica FCF
elif tributos and document_type == '01':
    # Segunda lógica que puede afectar FCF
```

### 3. Lógica genérica al final
```python
# ❌ MAL - Catch-all que interfiere
else:
    if document_type == '01' and venta_gravada > 0:
        # Esto puede sobreescribir lógica específica
```

## ✅ VALIDACIÓN DE CUMPLIMIENTO

Antes de cada modificación, verificar:

1. **Un solo path**: Cada documento pasa por UNA SOLA lógica
2. **No solapamiento**: Las condiciones son mutuamente excluyentes  
3. **Específico primero**: Lógicas específicas antes que genéricas
4. **Sin catch-all**: No usar `else` que pueda interferir

## 🛠️ DEBUGGING

Para verificar separación correcta:
```python
_logger.info(f"DOCUMENTO: {document_type}")
_logger.info(f"FCF: {fiscal_position.l10n_sv_is_final_consumer if fiscal_position else False}")
_logger.info(f"PATH EJECUTADO: [CCF|FCF|FACTURA_NORMAL|OTRO]")
```

## 🔄 MANTENIMIENTO

**SIEMPRE:**
1. Documentar cambios de reglas en este archivo
2. Probar cada tipo de documento por separado
3. Verificar que un cambio NO afecte otros tipos
4. Mantener esquemas JSON separados por tipo

**NUNCA:**
1. Crear lógica "genérica" que afecte múltiples tipos
2. Asumir que reglas de un tipo aplican a otro
3. Usar variables compartidas entre tipos sin validar
4. Hacer cambios sin probar todos los tipos de documento

---
**Fecha última actualización:** 2025-07-08
**Motivo:** Error MH "El iva calculado es diferente al proporcionado" - FCF requiere tributos ["20"]