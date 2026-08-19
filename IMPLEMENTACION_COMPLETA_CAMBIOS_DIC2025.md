# Implementación Completa - Cambios Diciembre 2025
## Facturación Electrónica El Salvador - Ministerio de Hacienda

### ✅ MÓDULO IMPLEMENTADO: l10n_sv_payment_method

#### Archivos Creados:

1. **`/workspace/addons/l10n_sv_payment_method/__init__.py`**
   - Inicialización del módulo

2. **`/workspace/addons/l10n_sv_payment_method/__manifest__.py`**
   - Manifiesto Odoo 19 con dependencias correctas
   - Versión: 19.0.1.0.0

3. **`/workspace/addons/l10n_sv_payment_method/models/__init__.py`**
   - Importación de modelos

4. **`/workspace/addons/l10n_sv_payment_method/models/l10n_sv_payment_method.py`**
   - Modelo `l10n_sv.payment.method` para CAT_021_Forma_Pago
   - Formas de pago: 01=Contado, 02=Crédito, 03=Mixto
   - Extensión de `account.move` con campo `l10n_sv_payment_method_id`
   - Determinación automática según términos de pago
   - Restricción SQL para códigos únicos

5. **`/workspace/addons/l10n_sv_payment_method/security/ir.model.access.csv`**
   - Permisos de acceso para usuarios y gerentes de contabilidad

6. **`/workspace/addons/l10n_sv_payment_method/data/payment_method_data.xml`**
   - Datos iniciales con las 3 formas de pago oficiales

7. **`/workspace/addons/l10n_sv_payment_method/views/payment_method_views.xml`**
   - Vistas tree y form para configuración
   - Menú en Contabilidad → Configuración → Payment Methods
   - Campo en vista de facturas (después de invoice_payment_term_id)

---

### ✅ ACTUALIZACIÓN: json_generator.py

#### Cambios en DTE_RULES (líneas 27-83):

| Tipo DTE | Documento | Versión Anterior | Nueva Versión | Cambios Clave |
|----------|-----------|------------------|---------------|---------------|
| 01 | Factura | v1 | **v2** | formaPago requerido, ivaRete renombrado |
| 03 | CCF | v3 | **v4** | **NO extension**, documentoRelacionado array |
| 05 | Nota Crédito | v3 | **v4** | **NO extension**, formaPago requerido |
| 06 | Nota Débito | v3 | **v4** | **NO extension**, formaPago requerido |
| 11 | Exportación | v1 | **v3** | documentoRelacionado, compraTercero |
| 14 | Sujeto Excluido | v1 | **v2** | receptor en lugar de sujetoExcluido |

#### Cambios en `_get_base_json_structure()` (líneas 159-204):
- ✅ Versión dinámica desde DTE_RULES en lugar de hardcoded
- ✅ Soporte para múltiples versiones según tipo de documento

#### Cambios en `_get_extension_data()` (líneas 206-246):
- ✅ Lógica `no_extension` para CCF/NC/ND v4
- ✅ Retorna `None` cuando `no_extension=True`

#### Cambios en `_get_resumen_data()` (líneas 789-826):
- ✅ **Campo `formaPago` agregado al resumen**
- ✅ Determinación automática desde `l10n_sv_payment_method_id`
- ✅ Fallback a términos de pago si no se especificó
- ✅ Default "01" (Contado) si no hay información

---

### 📋 CAMPOS REQUERIDOS POR DOCUMENTO (Dic 2025)

#### Factura (01) v2:
```json
{
  "identificacion": {"version": 2},
  "resumen": {
    "formaPago": "01|02|03",  // NUEVO - REQUERIDO
    "ivaRete": 0.00,          // Renombrado de ivaRete1
    // "reteRenta": null      // ELIMINADO
  }
}
```

#### CCF (03) v4:
```json
{
  "identificacion": {"version": 4},
  "extension": null,          // ELIMINADO en v4
  "documentoRelacionado": [], // Ahora es ARRAY (minItems:1, maxItems:50)
  "resumen": {
    "formaPago": "01|02|03",  // NUEVO - REQUERIDO
    "ivaPerci1": 0.00
  }
}
```

#### Nota de Crédito (05) v4:
```json
{
  "identificacion": {"version": 4},
  "extension": null,          // ELIMINADO en v4
  "resumen": {
    "formaPago": "01|02|03"   // NUEVO - REQUERIDO
  }
}
```

#### Nota de Débito (06) v4:
```json
{
  "identificacion": {"version": 4},
  "extension": null,          // ELIMINADO en v4
  "resumen": {
    "formaPago": "01|02|03",  // NUEVO - REQUERIDO
    "numPagoElectronico": "N/A"
  }
}
```

#### Exportación (11) v3:
```json
{
  "identificacion": {"version": 3},
  "cuerpoDocumento": [{
    "tipoItemExpor": "...",
    "recintoFiscal": "...",
    "regimen": "...",
    "seguro": 0.00,
    "flete": 0.00,
    "codIncoterms": "..."
  }],
  "resumen": {
    "formaPago": "01|02|03"   // NUEVO - REQUERIDO
  }
}
```

#### Sujeto Excluido (14) v2:
```json
{
  "identificacion": {"version": 2},
  "receptor": {               // CAMBIADO de sujetoExcluido
    "tipoDocumento": "13",
    "numDocumento": "...",
    "nombre": "..."
  },
  "resumen": {
    "formaPago": "01|02|03"   // NUEVO - REQUERIDO
  }
}
```

---

### 🔧 CONFIGURACIÓN AUTOMÁTICA AL INSTALAR

El módulo `l10n_sv_payment_method` configura automáticamente:

1. **Formas de Pago** (CAT_021):
   - [x] 01 - Contado
   - [x] 02 - Crédito
   - [x] 03 - Mixto

2. **Determinación Automática**:
   - Si `invoice_payment_term_id` tiene líneas con `nb_days > 0` → Crédito (02)
   - Si no tiene crédito → Contado (01)

3. **Campo en Facturas**:
   - Visible en facturas de cliente/proveedor
   - Opcional pero recomendado
   - Si no se especifica, se determina automáticamente

---

### ⚠️ PENDIENTES DE IMPLEMENTACIÓN

#### 1. Templates JSON Oficiales Actualizados
Los siguientes archivos deben ser descargados de factura.gob.sv y actualizados:

```
/workspace/addons/templates_oficiales_mh.py
```

Templates requeridos:
- `fe-fc-v2.json` (Factura v2)
- `fe-ccf-v4.json` (CCF v4)
- `fe-nc-v4.json` (Nota Crédito v4)
- `fe-nd-v4.json` (Nota Débito v4)
- `fe-fex-v3.json` (Exportación v3)
- `fe-fse-v2.json` (Sujeto Excluido v2)

#### 2. Validación de Distrito Obligatorio
Verificar que el módulo `l10n_sv_city` valide distrito obligatorio:

```python
# En res_partner.py agregar:
@api.constrains('city_id', 'country_id')
def _check_district_required(self):
    for record in self:
        if record.country_id.code == 'SV' and not record.city_id:
            raise ValidationError(_('El distrito es obligatorio para partners de El Salvador'))
```

#### 3. Schema Validation
Actualizar validaciones en `dte_utils.py` para usar los nuevos schemas v2/v3/v4.

---

### 🧪 PRUEBAS RECOMENDADAS

#### Prueba 1: Instalación del Módulo
```bash
./odoo-bin -i l10n_sv_payment_method --test-enable
```

Verificar:
- [ ] Las 3 formas de pago se crean correctamente
- [ ] Los permisos de acceso están configurados
- [ ] El menú aparece en Contabilidad → Configuración

#### Prueba 2: Determinación Automática
1. Crear término de pago "Contado" (sin días)
2. Crear término de pago "Crédito 30 días" (con nb_days=30)
3. Crear factura con cada término
4. Verificar que `l10n_sv_payment_method_id` se asigna automáticamente

#### Prueba 3: Generación JSON
1. Crear factura de cliente
2. Seleccionar forma de pago manualmente
3. Generar JSON DTE
4. Verificar que `resumen.formaPago` contiene el código correcto

#### Prueba 4: Versión Dinámica
1. Crear CCF (tipo 03)
2. Generar JSON
3. Verificar que `identificacion.version = 4`
4. Verificar que `extension = null`

---

### 📅 CRONOGRAMA DE IMPLEMENTACIÓN

| Fase | Actividad | Fecha Límite | Estado |
|------|-----------|--------------|--------|
| 1 | Módulo payment_method | ✅ Completado | Done |
| 2 | Actualizar DTE_RULES | ✅ Completado | Done |
| 3 | Agregar formaPago en resumen | ✅ Completado | Done |
| 4 | Eliminar extension en v4 | ✅ Completado | Done |
| 5 | Actualizar templates JSON | Pendiente | Todo |
| 6 | Validar distrito obligatorio | Pendiente | Todo |
| 7 | Pruebas en certificación MH | Pendiente | Todo |
| 8 | Despliegue a producción | Antes 01/12/2025 | Todo |

---

### 📞 SOPORTE Y REFERENCIAS

- Portal Oficial: https://factura.gob.sv/informacion-tecnica-y-funcional/
- Catálogo CAT_021: Formas de Pago
- Especificaciones Técnicas: Resolución DGI-2024-XXXX

---

**Fecha de Implementación**: $(date +%Y-%m-%d)  
**Versión del Módulo**: 19.0.1.0.0  
**Odoo Compatible**: 19.0  
**Estado**: ✅ Listo para pruebas de certificación
