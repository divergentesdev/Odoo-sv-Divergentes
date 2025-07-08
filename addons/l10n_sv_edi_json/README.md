# El Salvador - Generador de JSON DTE

## Descripción

Módulo para generar documentos tributarios electrónicos (DTE) en formato JSON según las especificaciones técnicas del Ministerio de Hacienda de El Salvador.

## Funcionalidades Principales

### 1. Generación de JSON DTE
- **Generación automática**: Crea JSON DTE desde facturas de Odoo
- **Múltiples tipos de documento**: Soporta todos los tipos de DTE (01, 03, 05, 06, 07, 11, etc.)
- **Validación completa**: Valida estructura y contenido según especificaciones MH
- **Integración con catálogos**: Utiliza catálogos oficiales (UOM, Payment, Incoterms, etc.)

### 2. Utilidades y Herramientas
- **Conversión números a letras**: Formato específico MH ("CIENTO TRECE 00/100 DÓLARES")
- **Formateo de documentos**: NIT, DUI, fechas, montos según estándares
- **Validaciones específicas**: Por tipo de documento y campo
- **Cálculos automáticos**: Totales, impuestos, clasificación fiscal

### 3. Vista Previa y Validación
- **Vista previa HTML**: JSON formateado con colores para mejor lectura
- **Validación en tiempo real**: Errores y advertencias inmediatas
- **Descarga de archivos**: Exportar JSON como archivo .json
- **Regeneración**: Actualizar JSON cuando cambian datos de factura

## Modelos Principales

### L10nSvJsonGenerator
- **Propósito**: Configura generadores específicos por tipo de documento
- **Campos clave**: document_type_id, template, active
- **Métodos principales**: generate_json_dte(), validate_json()

### L10nSvDteUtils (AbstractModel)
- **Propósito**: Utilidades compartidas para generación DTE
- **Funciones**: number_to_words(), format_nit(), format_dui(), validaciones
- **Reutilizable**: Puede usarse desde otros módulos EDI

### Account Move (Heredado)
- **Campos agregados**: 
  - l10n_sv_json_dte: Contenido JSON generado
  - l10n_sv_json_generated: Boolean indicando si JSON existe
  - l10n_sv_json_validated: Boolean indicando si JSON es válido
- **Acciones**: Generar, validar, previsualizar, regenerar JSON

## Wizard de Vista Previa

### L10nSvJsonPreviewWizard
- **Vista HTML formateada**: JSON con colores y formato legible
- **Estadísticas**: Tamaño en bytes, número de líneas
- **Validación**: Estado de validación y lista de errores
- **Acciones**: Descargar, regenerar, copiar al portapapeles

## Estructura JSON Generada

El JSON sigue exactamente las especificaciones del MH:

```json
{
  "identificacion": {
    "version": 1,
    "ambiente": "00|01",
    "tipoDte": "01|03|05|...",
    "numeroControl": "DTE-##-####-###############",
    "codigoGeneracion": "UUID",
    "tipoModelo": 1,
    "tipoOperacion": 1,
    "fecEmi": "YYYY-MM-DD",
    "horEmi": "HH:MM:SS",
    "tipoMoneda": "USD"
  },
  "emisor": { ... },
  "receptor": { ... },
  "cuerpoDocumento": [ ... ],
  "resumen": { ... }
}
```

## Integración con Catálogos

### Catálogos Utilizados
- **CAT_002**: Tipos de documento (l10n_sv_document_type)
- **CAT_014**: Unidades de medida (l10n_sv_uom)
- **CAT_018**: Formas de pago (l10n_sv_payment)
- **CAT_024**: Incoterms (l10n_sv_incoterms)
- **Impuestos**: Códigos DGII para tributos

### Mapeo Automático
El sistema mapea automáticamente:
- Productos → códigos de unidad de medida
- Impuestos → códigos de tributo MH
- Términos de pago → códigos de plazo
- Partners → tipos de documento de identificación

## Flujo de Trabajo

1. **Configuración inicial**:
   - Instalar módulo y dependencias
   - Configurar generadores JSON por tipo de documento
   - Configurar catálogos si es necesario

2. **Generación JSON**:
   - Crear factura en Odoo
   - Asignar tipo de documento DTE
   - Generar número de control EDI
   - Ejecutar "Generar JSON DTE"

3. **Validación y envío**:
   - Revisar JSON en vista previa
   - Validar estructura y contenido
   - Descargar JSON para envío al MH
   - (Envío automático disponible en módulo l10n_sv_api_client)

## Configuración

### Dependencias Requeridas
```python
'depends': [
    'l10n_sv_edi_base',        # Infraestructura EDI base
    'l10n_sv_document_type',   # Tipos de documentos
    'l10n_sv_cta',             # Plan de cuentas e impuestos
    'l10n_latam_sv',           # Tipos de identificación
    'l10n_sv_city',            # Municipios y departamentos
    'l10n_sv_uom',             # Unidades de medida
    'l10n_sv_payment',         # Términos de pago
    'l10n_sv_incoterms',       # Incoterms para exportación
]
```

### Permisos de Acceso
- **account.group_account_user**: Leer generadores, crear JSON
- **account.group_account_invoice**: Crear/modificar generadores
- **account.group_account_manager**: Acceso completo

## Menús y Navegación

- **Contabilidad > Localización SV > EDI > JSON DTE > Generadores JSON**
- **Facturas > Página "JSON DTE"** (en vista de formulario)
- **Vista previa**: Botón "Vista Previa" en facturas con JSON generado

## Tarea Programada

### Generación Automática
- **Función**: `cron_generate_pending_json_dte()`
- **Propósito**: Generar JSON DTE para facturas pendientes
- **Filtros**: Facturas validadas con tipo DTE pero sin JSON generado
- **Logs**: Registra éxitos y errores en log del sistema

## Casos de Uso Específicos

### Factura de Exportación (11)
- Incluye información de Incoterms
- Mapea datos de comercio exterior
- Valida datos requeridos para exportación

### Notas de Crédito/Débito (05/06)
- Referencia documento original
- Incluye sección "documentoRelacionado"
- Valida existencia de documento relacionado

### Comprobante de Retención (07)
- Cálculos específicos de retenciones
- Mapea tipos de retención
- Valida montos y porcentajes

## Validaciones Implementadas

### Estructura JSON
- Campos requeridos por tipo de documento
- Tipos de datos correctos
- Longitudes máximas de texto
- Formatos de fecha/hora

### Contenido de Negocio
- Correlatividad de número de control
- Validez de códigos de catálogo
- Consistencia de totales
- Lógica específica por tipo de documento

## Extensibilidad

### Agregar Nuevo Tipo de Documento
1. Crear registro en l10n_sv.json.generator
2. Implementar método `_generate_[tipo]_json()` en JsonGenerator
3. Agregar validaciones específicas en `validate_json_structure()`
4. Actualizar plantilla JSON en data/

### Personalizar Generación
- Override métodos `_get_*_data()` para campos específicos
- Extender DteUtils para nuevas utilidades
- Agregar validaciones personalizadas

## Troubleshooting

### Errores Comunes
1. **"No se encontró generador"**: Verificar que existe generador activo para tipo de documento
2. **"JSON inválido"**: Revisar estructura, campos requeridos y formatos
3. **"Error de catálogo"**: Verificar que productos/impuestos tienen códigos MH asignados

### Logs y Debugging
- Logs en `/var/log/odoo/odoo.log`
- Nivel DEBUG para información detallada
- Campo `l10n_sv_json_errors` en facturas para errores específicos

## Versión y Compatibilidad

- **Versión**: 18.0.1.0.0
- **Odoo**: 18.0+
- **País**: El Salvador
- **Licencia**: LGPL-3