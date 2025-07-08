# El Salvador - Firma Digital DTE

## Descripción

Módulo para firma digital de documentos tributarios electrónicos (DTE) según las especificaciones técnicas del Ministerio de Hacienda de El Salvador.

## Funcionalidades Principales

### 1. Firma Digital de Documentos DTE
- **Múltiples formatos de firma**: XML-DSig, JOSE/JWS, PKCS#7, Raw
- **Algoritmos seguros**: RSA-SHA256, RSA-SHA512, compatibles con estándares
- **Certificados .cert del MH**: Soporte completo para certificados específicos del MH
- **Integración transparente**: Firma automática integrada en flujo de facturación

### 2. Validación y Verificación
- **Verificación de firmas**: Validación criptográfica de firmas existentes
- **Validación de certificados**: Verificación de vigencia y cadena de confianza
- **Integridad de documentos**: Detección de modificaciones post-firma
- **Logs de auditoría**: Registro completo de operaciones de firma

### 3. Gestión de Algoritmos Criptográficos
- **Catálogo de algoritmos**: Configuración de algoritmos soportados
- **Niveles de seguridad**: Clasificación por fortaleza criptográfica
- **Compatibilidad estándares**: Soporte XML-DSig, JOSE, PKCS#7
- **Algoritmos deprecados**: Gestión de algoritmos obsoletos

## Arquitectura del Sistema

### Modelos Principales

#### L10nSvDigitalSignature
- **Propósito**: Servicio de firma digital configurable
- **Características**:
  - Configuración de algoritmos y formatos
  - Integración con certificados .cert
  - Estadísticas de uso y rendimiento
  - Validación de certificados

#### L10nSvSignatureAlgorithm
- **Propósito**: Catálogo de algoritmos criptográficos
- **Información**:
  - Especificaciones técnicas (OID, URI, JOSE)
  - Niveles de seguridad y recomendaciones
  - Compatibilidad con estándares
  - Estado de deprecación

#### L10nSvSignatureLog
- **Propósito**: Auditoría de operaciones de firma
- **Registro**:
  - Operaciones exitosas y fallidas
  - Tiempos de procesamiento
  - Información de certificados utilizados
  - Datos para troubleshooting

## Formatos de Firma Soportados

### 1. XML Digital Signature (XML-DSig)
```xml
<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
  <SignedInfo>
    <CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
    <SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
    <Reference URI="">
      <Transforms>
        <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
      </Transforms>
      <DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
      <DigestValue>...</DigestValue>
    </Reference>
  </SignedInfo>
  <SignatureValue>...</SignatureValue>
  <KeyInfo>
    <X509Data>
      <X509Certificate>...</X509Certificate>
    </X509Data>
  </KeyInfo>
</Signature>
```

### 2. JSON Web Signature (JWS/JOSE)
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsIng1YyI6WyIuLi4iXX0.
eyJkdGUiOiJ7Li4ufSIsImlhdCI6MTY0MDk5NTIwMH0.
signature_base64_encoded
```

### 3. Firma Raw (Base64)
```
Base64EncodedSignatureData==
```

## Algoritmos Criptográficos

### Algoritmos Recomendados

#### RSA-SHA256 (Por Defecto)
- **Seguridad**: Alta
- **Tamaño mínimo clave**: 2048 bits
- **Estado**: Recomendado para uso general
- **Aprobación gubernamental**: Sí

#### RSA-SHA512 (Máxima Seguridad)
- **Seguridad**: Muy Alta
- **Tamaño mínimo clave**: 2048 bits
- **Estado**: Recomendado para documentos críticos
- **Aprobación gubernamental**: Sí

### Algoritmos Legacy

#### RSA-SHA1 (Deprecado)
- **Seguridad**: Media
- **Tamaño mínimo clave**: 1024 bits
- **Estado**: Deprecado desde 2020
- **Uso**: Solo compatibilidad legacy

## Integración con Account Move

### Campos Agregados
- `l10n_sv_signature_status`: Estado de firma digital
- `l10n_sv_signature_data`: Datos de la firma
- `l10n_sv_signature_algorithm`: Algoritmo utilizado
- `l10n_sv_signature_date`: Fecha de firma
- `l10n_sv_signature_verified`: Estado de verificación
- `l10n_sv_signed_json`: JSON DTE con firma integrada

### Estados de Firma
- **draft**: Sin firmar
- **signed**: Firmado digitalmente
- **verified**: Firma verificada
- **invalid**: Firma inválida
- **error**: Error en proceso de firma

### Flujo de Trabajo
1. **Generación JSON DTE**: Prerequisito para firma
2. **Validación JSON**: JSON debe estar validado
3. **Firma digital**: Proceso automático o manual
4. **Verificación**: Validación criptográfica opcional
5. **Integración**: JSON firmado listo para envío MH

## Configuración del Sistema

### Dependencias Requeridas
```python
'external_dependencies': {
    'python': [
        'cryptography',    # Operaciones criptográficas modernas
        'OpenSSL',        # Manejo de certificados X.509
        'xmlsec',         # XML Digital Signature
        'lxml',           # Procesamiento XML
    ]
}
```

### Instalación de Dependencias
```bash
pip install cryptography pyOpenSSL xmlsec lxml
```

### Configuración Inicial
1. **Crear servicio de firma**:
   - Ir a Contabilidad > Localización SV > EDI > Firma Digital > Servicios de Firma
   - Configurar certificado .cert y algoritmo
   - Seleccionar formato de firma (XML-DSig recomendado)

2. **Configurar algoritmos**:
   - Revisar algoritmos disponibles
   - Verificar algoritmos recomendados
   - Configurar algoritmos deprecados si es necesario

3. **Probar firma**:
   - Usar botón "Probar Firma" en servicio
   - Verificar logs de firma
   - Validar configuración de certificados

## Seguridad y Certificados

### Manejo de Certificados .cert
- **Formato PKCS#12**: Soporte completo para .cert del MH
- **Validación temporal**: Verificación de vigencia automática
- **Cadena de confianza**: Validación opcional de cadena completa
- **Almacenamiento seguro**: Certificados en base64 en BD

### Validaciones de Seguridad
- **Expiración de certificados**: Verificación automática
- **Tamaño de clave**: Validación según algoritmo
- **Algoritmos seguros**: Recomendaciones de seguridad
- **Compatibilidad**: Verificación algoritmo-certificado

## Automatización

### Tareas Programadas

#### Firma Automática de DTE
- **Frecuencia**: Cada 20 minutos
- **Función**: `cron_sign_pending_dte()`
- **Filtros**: JSON validado, estado posted, sin firma
- **Propósito**: Firma automática de documentos listos

#### Verificación Automática
- **Frecuencia**: Cada hora
- **Función**: `cron_verify_signatures()`
- **Filtros**: Documentos firmados sin verificar
- **Propósito**: Validación automática de firmas

#### Limpieza de Logs
- **Frecuencia**: Semanal
- **Función**: `cleanup_old_logs(days=180)`
- **Conservación**: 180 días por defecto
- **Propósito**: Mantener rendimiento del sistema

## Logging y Auditoría

### Información Registrada
- **Operaciones de firma**: Éxitos y errores
- **Tiempos de procesamiento**: Métricas de rendimiento
- **Certificados utilizados**: Trazabilidad de certificados
- **Algoritmos aplicados**: Auditoria de algoritmos
- **Hash de entrada**: Verificación de integridad

### Análisis de Logs
- **Filtros avanzados**: Por estado, tipo, fecha
- **Estadísticas**: Tasas de éxito, tiempos promedio
- **Troubleshooting**: Información detallada de errores
- **Auditoría**: Trazabilidad completa de operaciones

## JSON DTE Firmado

### Estructura del JSON Firmado
```json
{
  "identificacion": { ... },
  "emisor": { ... },
  "receptor": { ... },
  "cuerpoDocumento": [ ... ],
  "resumen": { ... },
  "firmaElectronica": {
    "fechaFirma": "2024-01-15T14:30:00",
    "algoritmo": "RSA-SHA256",
    "formato": "xmldsig",
    "certificado": {
      "sujeto": "CN=EMPRESA CERT, O=EMPRESA, C=SV",
      "emisor": "CN=MH ROOT CA, O=MINISTERIO DE HACIENDA, C=SV",
      "numeroSerie": "123456789",
      "validoDesde": "2023-01-01T00:00:00",
      "validoHasta": "2025-12-31T23:59:59"
    },
    "firma": "PD94bWwgdmVyc2lvbj0iMS4wIi..."
  }
}
```

## Casos de Uso Específicos

### Firma de Facturas de Exportación
- Algoritmos de alta seguridad recomendados
- Validación adicional de datos de exportación
- Integración con información de Incoterms

### Firma de Notas de Crédito
- Referencia a documento original
- Validación de consistencia con factura base
- Preservación de trazabilidad

### Firma Masiva
- Procesamiento por lotes automático
- Optimización de rendimiento
- Manejo de errores individuales

## Troubleshooting

### Errores Comunes

#### Error de Certificado
```
Error: Certificado expirado o inválido
Solución: Verificar vigencia y formato del certificado .cert
```

#### Error de Algoritmo
```
Error: Algoritmo no compatible con certificado
Solución: Verificar compatibilidad algoritmo-certificado
```

#### Error de Formato
```
Error: Formato de firma no soportado
Solución: Verificar configuración de formato en servicio
```

### Herramientas de Diagnóstico
- **Probar Firma**: Verificar configuración básica
- **Ver Logs**: Análisis detallado de errores
- **Verificar Firma**: Validación de firmas existentes
- **Reset Firma**: Limpiar estado corrupto

## APIs y Extensibilidad

### API de Firma
```python
# Firmar documento
signature_service = env['l10n_sv.digital.signature'].get_default_signature_service()
result = signature_service.sign_document(data, document_type='json')

# Verificar firma
verification = signature_service.verify_signature(signature_data, original_data)
```

### Extensión de Algoritmos
```python
# Agregar nuevo algoritmo
env['l10n_sv.signature.algorithm'].create({
    'name': 'NUEVO-ALGORITMO',
    'code': 'NEW_ALG_CODE',
    'hash_algorithm': 'sha384',
    'key_type': 'rsa',
    'security_level': 'high'
})
```

## Cumplimiento Normativo

### Estándares Soportados
- **XML Digital Signature**: W3C XML-DSig estándar
- **JSON Web Signature**: RFC 7515 (JWS)
- **PKCS#7/CMS**: RFC 5652
- **X.509**: Certificados estándar

### Especificaciones MH
- **Certificados .cert**: Formato específico MH
- **Algoritmos aprobados**: RSA-SHA256, RSA-SHA512
- **Estructura JSON DTE**: Integración con JSON oficial
- **Validaciones requeridas**: Según normativa MH

## Versión y Compatibilidad

- **Versión**: 18.0.1.0.0
- **Odoo**: 18.0+
- **País**: El Salvador
- **Licencia**: LGPL-3
- **Dependencias**: cryptography, OpenSSL, xmlsec, lxml

## Métricas y KPIs

### Indicadores de Rendimiento
- **Tiempo promedio de firma**: < 2 segundos
- **Tasa de éxito**: > 99%
- **Certificados válidos**: 100%
- **Algoritmos seguros**: > 95%

### Monitoreo Continuo
- Alertas por errores de certificado
- Notificaciones de algoritmos deprecados
- Métricas de rendimiento en tiempo real
- Auditoría de cumplimiento normativo