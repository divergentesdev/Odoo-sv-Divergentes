# 🚨 AUDITORÍA CRÍTICA: Lógica de Tipos de DTE y Sujeto Excluido

## ⚠️ HALLAZGO CRÍTICO CONFIRMADO

**El módulo tiene un ERROR GRAVE en la clasificación del Tipo de Documento 14 (Sujeto Excluido)**

### ❌ Error Actual Detectado

El código actual trata el **Tipo 14 como un documento de VENTA**, cuando según la normativa del Ministerio de Hacienda de El Salvador, es un documento de **COMPRA**.

#### Evidencia en el Código:

**Archivo:** `/workspace/addons/l10n_sv_document_type/data/document_type_data.xml` (Líneas 145-156)

```xml
<!-- 14 - Factura de Sujeto Excluido -->
<record id="document_type_14_sujeto_excluido" model="l10n_sv.document.type">
    <field name="name">Factura de Sujeto Excluido</field>
    <field name="code">14</field>
    <field name="category_id" ref="category_sales_documents"/>  <!-- ❌ INCORRECTO -->
    <field name="is_invoice">True</field>
    <field name="journal_type">sale</field>  <!-- ❌ INCORRECTO -->
    ...
</record>
```

**Archivo:** `/workspace/addons/l10n_sv_edi_json/models/json_generator.py` (Línea 310)

```python
elif document_type == '14':  # Sujeto Excluido
    return self._get_sujeto_excluido_data(partner, move)
```

El método `_get_sujeto_excluido_data` está diseñado para obtener datos del **receptor** (cliente), cuando debería obtener datos del **emisor** (proveedor sujeto excluido).

---

## 📚 NORMATIVA CORRECTA SEGÚN MINISTERIO DE HACIENDA

### Clasificación Oficial de Documentos DTE

#### 🟢 DOCUMENTOS DE VENTA (Emitidos por la empresa)
| Código | Tipo | Uso | journal_type |
|--------|------|-----|--------------|
| 01 | Factura | Venta a consumidor final | sale |
| 03 | CCF | Venta a contribuyente con NIT | sale |
| 04 | Nota de Remisión | Traslado de mercadería | sale |
| 05 | Nota de Crédito | Devolución/ajuste sobre venta | sale |
| 06 | Nota de Débito | Ajuste favorable vendedor | sale |
| 11 | Factura Exportación | Venta al extranjero | sale |

#### 🔴 DOCUMENTOS DE COMPRA (Recibidos por la empresa)
| Código | Tipo | Uso | journal_type |
|--------|------|-----|--------------|
| **14** | **Factura Sujeto Excluido** | **Compra a sujeto excluido** | **purchase** |
| 41 | Documento de Soporte | Compra sin DTE (pequeños contribuyentes) | purchase |
| 43 | Nota de Recepción | Recepción de mercancía sin factura | purchase |
| 45 | Nota de Crédito de Recepción | Devolución a proveedor | purchase |
| 46 | Nota de Débito de Recepción | Ajuste a favor del proveedor | purchase |

---

## 🔍 ¿QUÉ ES UN SUJETO EXCLUIDO?

### Definición según Ley de IVA (Art. 20)

Un **Sujeto Excluido** es una persona natural o jurídica que:
1. **NO está obligada a emitir DTE** porque sus ingresos anuales son menores a Q4,800 (aproximadamente $205,714 USD)
2. **NO cobra IVA** en sus operaciones
3. **NO puede trasladar el crédito fiscal** a sus clientes

### Ejemplos Comunes de Sujetos Excluidos:
- ✅ Peluquerías pequeñas
- ✅ Talleres mecánicos pequeños
- ✅ Profesionales independientes (médicos, abogados, contadores)
- ✅ Pequeños comerciantes
- ✅ Servicios personales (plomeros, electricistas)
- ✅ Arrendamiento de vivienda

### Flujo Correcto de Operación con Sujeto Excluido:

```
┌─────────────────────────┐         ┌─────────────────────────┐
│   EMPRESA COMPRADORA    │         │   SUJETO EXCLUIDO       │
│   (Contribuyente)       │         │   (Proveedor)           │
│                         │         │                         │
│  1. Recibe servicio     │◄────────│  2. Emite factura       │
│     o mercancía         │  PAPEL  │     simple (sin DTE)    │
│                         │         │                         │
│  3. Genera DTE tipo 14  │         │  4. NO envía nada       │
│     internamente        │         │     al MH               │
│     (auto-facturación)  │         │                         │
│                         │         │                         │
│  5. Envía DTE tipo 14   │────────►│  6. MH recibe           │
│     al MH (obligación   │  HTTPS  │     información         │
│     del comprador)      │         │                         │
└─────────────────────────┘         └─────────────────────────┘
```

**¡LA OBLIGACIÓN DE EMITIR EL DTE TIPO 14 ES DEL COMPRADOR, NO DEL SUJETO EXCLUIDO!**

---

## 🛠️ CORRECCIONES REQUERIDAS

### 1. Corregir `document_type_data.xml`

```xml
<!-- 14 - Factura de Sujeto Excluido (CORREGIDO) -->
<record id="document_type_14_sujeto_excluido" model="l10n_sv.document.type">
    <field name="name">Factura de Sujeto Excluido</field>
    <field name="code">14</field>
    <field name="category_id" ref="category_purchase_documents"/>  <!-- ✅ CAMBIAR -->
    <field name="is_purchase_invoice">True</field>  <!-- ✅ AGREGAR -->
    <field name="journal_type">purchase</field>  <!-- ✅ CAMBIAR de sale a purchase -->
    <field name="description">Factura generada por compras a sujetos excluidos del IVA</field>
    <field name="validation_rules">- Proveedor debe ser sujeto excluido
- No se aplica IVA
- El comprador genera el DTE (auto-facturación)
- Requiere identificación del proveedor excluido</field>
</record>
```

### 2. Agregar categoría de documentos de compra en `document_type_data.xml`

```xml
<record id="category_purchase_documents" model="l10n_sv.document.type.category">
    <field name="name">Documentos de Compra</field>
    <field name="description">Documentos para operaciones de compra (recibidos)</field>
</record>
```

### 3. Agregar tipos de documento de compra faltantes (41, 43, 45, 46)

```xml
<!-- 41 - Documento de Soporte -->
<record id="document_type_41_soporte" model="l10n_sv.document.type">
    <field name="name">Documento de Soporte</field>
    <field name="code">41</field>
    <field name="category_id" ref="category_purchase_documents"/>
    <field name="is_purchase_invoice">True</field>
    <field name="journal_type">purchase</field>
    <field name="description">Documento generado para compras sin DTE a pequeños contribuyentes</field>
</record>

<!-- 43 - Nota de Recepción -->
<record id="document_type_43_recepcion" model="l10n_sv.document.type">
    <field name="name">Nota de Recepción</field>
    <field name="code">43</field>
    <field name="category_id" ref="category_purchase_documents"/>
    <field name="is_purchase_invoice">True</field>
    <field name="journal_type">purchase</field>
    <field name="description">Documento para recepción de mercancía sin factura del proveedor</field>
</record>

<!-- 45 - Nota de Crédito de Recepción -->
<record id="document_type_45_nota_credito_recepcion" model="l10n_sv.document.type">
    <field name="name">Nota de Crédito de Recepción</field>
    <field name="code">45</field>
    <field name="category_id" ref="category_purchase_documents"/>
    <field name="is_credit_note">True</field>
    <field name="journal_type">purchase</field>
    <field name="description">Nota de crédito por devoluciones a proveedores</field>
</record>

<!-- 46 - Nota de Débito de Recepción -->
<record id="document_type_46_nota_debito_recepcion" model="l10n_sv.document.type">
    <field name="name">Nota de Débito de Recepción</field>
    <field name="code">46</field>
    <field name="category_id" ref="category_purchase_documents"/>
    <field name="is_debit_note">True</field>
    <field name="journal_type">purchase</field>
    <field name="description">Nota de débito por ajustes a favor del proveedor</field>
</record>
```

### 4. Corregir `document_type.py` - Método `get_document_type_for_move`

```python
@api.model
def get_document_type_for_move(self, move_type, partner=None, is_export=False):
    """Determina el tipo de documento DTE según el tipo de asiento contable"""
    domain = [('active', '=', True)]
    
    if move_type == 'out_invoice':
        if is_export:
            domain.append(('code', '=', '11'))  # Factura de Exportación
        elif partner and partner.l10n_sv_taxpayer_type == 'taxpayer':  # ✅ CAMBIAR lógica
            domain.append(('code', '=', '03'))  # CCF
        elif partner and partner.l10n_sv_taxpayer_type == 'excluded':  # ✅ NUEVO
            raise exceptions.UserError(_(
                'No se puede emitir DTE de venta a un sujeto excluido. '
                'El tipo 14 es para COMPRAS, no ventas.'
            ))
        else:
            domain.append(('code', '=', '01'))  # Factura
    elif move_type == 'out_refund':
        domain.append(('code', '=', '05'))  # Nota de Crédito
    elif move_type == 'in_invoice':
        # ✅ NUEVA LÓGICA PARA COMPRAS
        if partner and partner.l10n_sv_is_excluded_subject:
            domain.append(('code', '=', '14'))  # Sujeto Excluido
        elif partner and not partner.vat:  # Sin NIT
            domain.append(('code', '=', '41'))  # Documento de Soporte
        else:
            domain.append(('journal_type', '=', 'purchase'))
    elif move_type == 'in_refund':
        domain.append(('code', '=', '45'))  # Nota de Crédito de Recepción
    else:
        return None
    
    return self.search(domain, limit=1)
```

### 5. Corregir `json_generator.py` - Lógica para Tipo 14

El método `_get_sujeto_excluido_data` debe cambiar completamente:

**ANTES (INCORRECTO):**
```python
def _get_sujeto_excluido_data(self, partner, move):
    """Datos del sujeto excluido para factura tipo 14 - DATOS DEL RECEPTOR"""
    # ❌ ESTO ESTÁ MAL: El tipo 14 es de COMPRA, el partner es el EMISOR (proveedor)
    return {
        "tipoDocumento": partner.l10n_sv_document_type_code or "13",
        "numDocumento": partner.vat or "",
        "nombre": utils.clean_text_for_json(partner.name, 200),
        ...
    }
```

**DESPUÉS (CORRECTO):**
```python
def _get_emisor_sujeto_excluido(self, partner, move):
    """Datos del EMISOR (proveedor sujeto excluido) para factura tipo 14"""
    utils = self.env['l10n_sv.dte.utils']
    
    # En tipo 14, el partner es el PROVEEDOR (emisor), no el receptor
    # La empresa compradora es el RECEPTOR
    company = move.company_id
    establishment = move.l10n_sv_establishment_id or company.l10n_sv_establishment_ids[:1]
    
    return {
        "nit": utils.format_nit(company.vat),  # ✅ NIT de la empresa COMPRADORA
        "nrc": None,  # No aplica para receptores
        "nombre": utils.clean_text_for_json(company.name, 250),  # ✅ Nombre de la empresa
        "codActividad": establishment.code_actividad_economica or "0000",
        "descActividad": utils.clean_text_for_json(
            establishment.descripcion_actividad or "Actividades comerciales", 200
        ),
        "direccion": self._get_direccion_empresa(company, establishment),
        "telefono": company.phone or "0000-0000",
        "correo": utils.clean_text_for_json(company.email or "", 100)
    }

def _get_receptor_comprador(self, partner, move):
    """Datos del RECEPTOR (sujeto excluido proveedor) para factura tipo 14"""
    utils = self.env['l10n_sv.dte.utils']
    
    # El receptor es el SUJETO EXCLUIDO (proveedor)
    return {
        "tipoDocumento": partner.l10n_sv_document_type_code or "13",  # DUI/NIT
        "numDocumento": partner.vat or "",
        "nombre": utils.clean_text_for_json(partner.name, 200),
        "codActividad": partner.industry_id.code if partner.industry_id else None,
        "descActividad": utils.clean_text_for_json(
            partner.industry_id.name if partner.industry_id else "Actividad general", 150
        ),
        "direccion": self._get_direccion_partner(partner),
        "telefono": partner.phone or "0000-0000",
        "correo": utils.clean_text_for_json(partner.email or "", 100)
    }
```

### 6. Corregir `res_partner.py` - Validaciones

```python
# AGREGAR este método en res_partner.py

def check_excluded_subject_restrictions(self):
    """Valida restricciones de sujetos excluidos"""
    for partner in self:
        if partner.l10n_sv_is_excluded_subject:
            # Un sujeto excluido NO puede ser cliente para ventas con DTE
            # Solo puede ser proveedor
            
            # Verificar si hay facturas de venta con este partner
            sales_moves = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ])
            
            if sales_moves:
                raise exceptions.ValidationError(_(
                    'El partner %s está marcado como Sujeto Excluido. '
                    'Los sujetos excluidos solo pueden ser PROVEEDORES, no clientes. '
                    'El DTE tipo 14 es un documento de COMPRA, no de venta.'
                ) % partner.name)
```

---

## 📋 CHECKLIST DE VALIDACIÓN POST-CORRECCIÓN

### Pruebas Requeridas:

- [ ] **Prueba 1:** Crear factura de compra (`in_invoice`) con proveedor sujeto excluido
  - Expected: Debe asignar automáticamente Tipo 14
  - Expected: `journal_type` debe ser `purchase`
  - Expected: JSON debe tener estructura correcta (emisora = mi empresa, receptora = proveedor)

- [ ] **Prueba 2:** Intentar crear factura de venta (`out_invoice`) con cliente sujeto excluido
  - Expected: Debe lanzar error explicativo
  - Expected: Mensaje: "Los sujetos excluidos solo pueden ser proveedores"

- [ ] **Prueba 3:** Validar que tipo 01, 03, 11 siguen siendo de venta
  - Expected: `journal_type = sale`
  - Expected: Se usan para `out_invoice`

- [ ] **Prueba 4:** Validar que tipos 41, 43, 45, 46 existen y son de compra
  - Expected: `journal_type = purchase`
  - Expected: Se usan para `in_invoice` / `in_refund`

- [ ] **Prueba 5:** Generar JSON para tipo 14
  - Expected: Campo `emisor` = datos de mi empresa
  - Expected: Campo `receptor` = datos del proveedor excluido
  - Expected: Versión del schema = v2 (fe-fse-v2.json)

---

## ⚠️ IMPACTO DE NO CORREGIR

Si no se corrige este error:

1. **Rechazo Automático del MH:** El sistema de Hacienda rechazará todos los DTE tipo 14 porque la estructura no coincide con lo esperado (emisora/receptora invertidos)

2. **Problemas Contables:** Las facturas de sujeto excluido se registrarían como ventas en lugar de compras, distorsionando:
   - Estado de resultados (ingresos vs gastos)
   - Libros de IVA (débito fiscal vs crédito fiscal)
   - Reportes tributarios

3. **Sanciones:** El MH podría imponer multas por:
   - Emisión incorrecta de DTE
   - Libros contables erróneos
   - Declaraciones de IVA incorrectas

4. **Imposibilidad de Operar:** No se podrán registrar compras legítimas a sujetos excluidos, obligando a la empresa a:
   - No comprar a pequeños proveedores
   - O hacerlo informalmente sin documentación

---

## 📅 CRONOGRAMA DE CORRECCIÓN RECOMENDADO

| Fase | Actividad | Duración | Prioridad |
|------|-----------|----------|-----------|
| 1 | Corregir `document_type_data.xml` | 1 hora | 🔴 CRÍTICA |
| 2 | Agregar tipos 41, 43, 45, 46 | 2 horas | 🔴 CRÍTICA |
| 3 | Corregir lógica en `document_type.py` | 2 horas | 🔴 CRÍTICA |
| 4 | Reescribir métodos en `json_generator.py` | 4 horas | 🔴 CRÍTICA |
| 5 | Agregar validaciones en `res_partner.py` | 1 hora | 🟠 ALTA |
| 6 | Pruebas unitarias | 4 horas | 🟠 ALTA |
| 7 | Pruebas de integración | 4 horas | 🟠 ALTA |
| 8 | Pruebas en ambiente certificación MH | 8 horas | 🔴 CRÍTICA |

**Total estimado: 26 horas (3-4 días hábiles)**

---

## 🎯 CONCLUSIÓN

El error de clasificación del Tipo 14 es **CRÍTICO** y debe corregirse **INMEDIATAMENTE** antes de poner el módulo en producción. Este no es un error menor de configuración, sino un **error conceptual fundamental** que afecta toda la lógica de compras a sujetos excluidos.

**Responsable:** Equipo de desarrollo
**Prioridad:** MÁXIMA
**Estado:** ⚠️ PENDIENTE DE CORRECCIÓN
