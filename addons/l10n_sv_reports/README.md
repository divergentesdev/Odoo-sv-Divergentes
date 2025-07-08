# Módulo l10n_sv_reports - Reportes DTE El Salvador

## Descripción

Módulo para generar reportes PDF personalizados de documentos tributarios electrónicos (DTE) según las especificaciones del Ministerio de Hacienda de El Salvador.

## Funcionalidades Principales

### 📄 Reportes PDF Oficiales
- Reportes con diseño oficial DTE El Salvador
- Plantillas personalizables por tipo de documento
- Información completa de emisor y receptor
- Formato compatible con especificaciones del MH

### 📱 Códigos QR
- Generación automática de códigos QR
- Información completa del DTE embebida
- Soporte para logos de empresa en QR
- Configuración personalizable de tamaño y calidad

### 🔒 Integración EDI
- Información de firma digital
- Estado del documento en MH
- Trazabilidad completa del proceso
- Sellos y validaciones oficiales

### 🎨 Personalización
- Colores personalizables por empresa
- Marcas de agua para estados de documento
- CSS personalizado para reportes
- Múltiples formatos de papel

## Modelos Principales

### l10n_sv.qr.code.generator
Configuración para generación de códigos QR:
- Versión y corrección de errores
- Colores y tamaños
- Contenido del QR (URL, firma, MH)
- Plantillas de datos personalizadas

### l10n_sv.report.template
Plantillas de reportes DTE:
- Configuración por tipo de documento
- Elementos visuales (header, footer, QR)
- Estilos y colores personalizados
- CSS y diseño personalizable

## Configuración

### 1. Generadores QR
1. Ir a **Reportes DTE > Configuración > Generadores QR**
2. Crear o configurar generador por defecto
3. Establecer parámetros de calidad y contenido

### 2. Plantillas de Reporte
1. Ir a **Reportes DTE > Configuración > Plantillas de Reporte**
2. Crear plantillas por tipo de documento
3. Configurar colores, logos y elementos
4. Personalizar CSS si es necesario

### 3. Configuración en Facturas
1. Abrir factura con tipo de documento DTE
2. Ir a pestaña **Reportes DTE**
3. Seleccionar plantilla personalizada (opcional)
4. Generar QR y configurar opciones

## Uso

### Generar Reporte DTE
1. Desde factura: Botón **"Imprimir DTE"**
2. Vista previa: Botón **"Vista Previa"**
3. Envío por correo: Botón **"Enviar por Correo"**

### Códigos QR
- Generación automática al imprimir
- Generación manual: Botón **"Generar QR"**
- Descarga de imagen: Botón **"Descargar QR"**

### Códigos de Barras
- Generación opcional de códigos de barras
- Formato Code128 por defecto
- Integración en reportes PDF

## Estructura de Archivos

```
l10n_sv_reports/
├── models/
│   ├── qr_code_generator.py      # Generador de códigos QR
│   ├── report_template.py        # Plantillas de reportes
│   └── account_move.py           # Extensión de facturas
├── reports/
│   ├── invoice_dte_report.py     # Lógica del reporte
│   └── invoice_dte_template.xml  # Plantilla XML del reporte
├── views/
│   ├── qr_code_generator_views.xml
│   ├── report_template_views.xml
│   ├── account_move_views.xml
│   └── menu_views.xml
├── data/
│   ├── report_template_data.xml  # Plantillas por defecto
│   └── email_template_data.xml   # Template de correo
├── security/
│   └── ir.model.access.csv       # Permisos de acceso
└── static/src/css/
    └── report_style.css          # Estilos CSS
```

## Dependencias

### Módulos Odoo
- `l10n_sv_edi_base`: Infraestructura EDI
- `l10n_sv_edi_json`: Generador JSON DTE
- `l10n_sv_api_client`: Comunicación MH
- `l10n_sv_digital_signature`: Firma digital
- `account`: Contabilidad

### Librerías Python
- `qrcode`: Generación de códigos QR
- `Pillow`: Procesamiento de imágenes
- `reportlab`: Generación PDF avanzada
- `python-barcode`: Códigos de barras

## Personalización

### CSS Personalizado
En plantillas de reporte, pestaña "CSS Personalizado":
```css
.dte-report-container {
    font-family: 'Arial', sans-serif;
}

.dte-title {
    color: #your-color;
    font-size: 24px;
}
```

### Datos QR Personalizados
En generadores QR, campo "Plantilla de Datos":
```python
{
    'documento': doc.name,
    'fecha': doc.invoice_date.isoformat(),
    'total': doc.amount_total,
    'empresa': doc.company_id.name
}
```

## Tareas Automatizadas

### Generación Automática de QR
- Tarea programada: **"Generar Códigos QR Faltantes"**
- Ejecuta cada hora
- Genera QR para documentos publicados sin QR

## Troubleshooting

### QR no se genera
1. Verificar que el documento tenga tipo DTE asignado
2. Revisar configuración del generador QR
3. Verificar permisos de usuario

### Errores de plantilla
1. Verificar sintaxis CSS personalizado
2. Revisar referencias a campos del modelo
3. Verificar dependencias de módulos

### Problemas de correo
1. Verificar configuración SMTP en Odoo
2. Revisar template de correo electrónico
3. Verificar email del cliente

## Soporte

Para soporte técnico o reportar errores:
1. Revisar logs de Odoo en modo debug
2. Verificar configuración de módulos EDI
3. Contactar administrador del sistema

---

**Versión:** 18.0.1.0.0  
**Autor:** Tu Empresa  
**Licencia:** LGPL-3