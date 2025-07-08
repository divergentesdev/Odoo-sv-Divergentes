# El Salvador - Cliente API MH

## Descripción

Módulo para comunicación directa con la API del Ministerio de Hacienda de El Salvador para el envío y recepción de documentos tributarios electrónicos (DTE).

## Funcionalidades Principales

### 1. Comunicación con API del MH
- **Autenticación con certificados .cert**: Utiliza certificados digitales del MH
- **Envío de DTE**: Transmite documentos JSON al MH con validación completa
- **Consulta de estado**: Verifica el estado de procesamiento de DTE enviados
- **Manejo de contingencias**: Soporte para eventos de contingencia
- **Reintentos automáticos**: Sistema robusto de reintentos con backoff

### 2. Gestión de Certificados Digitales
- **Certificados .cert del MH**: Soporte completo para formato específico del MH
- **Autenticación SSL**: Configuración automática de contexto SSL
- **Manejo de contraseñas**: Almacenamiento seguro de credenciales
- **Validación de certificados**: Verificación de validez y expiración

### 3. Logging y Monitoreo
- **Logs detallados**: Registro completo de todas las comunicaciones
- **Análisis de respuestas**: Parseo inteligente de respuestas del MH
- **Estadísticas de uso**: Métricas de éxito/error por cliente
- **Troubleshooting**: Herramientas para diagnóstico de problemas

## Modelos Principales

### L10nSvApiClient
- **Propósito**: Configura clientes para comunicación con MH
- **Características**:
  - Manejo de ambientes (certificación/producción)
  - Configuración de timeouts y reintentos
  - Autenticación automática con tokens JWT
  - Estadísticas de uso en tiempo real

### L10nSvApiLog
- **Propósito**: Registra todas las comunicaciones con el MH
- **Información capturada**:
  - Peticiones y respuestas completas
  - Tiempos de procesamiento
  - Códigos de estado y errores
  - Datos de debugging

### L10nSvApiEndpoint
- **Propósito**: Configura endpoints específicos del MH
- **Flexibilidad**:
  - URLs configurables por ambiente
  - Headers personalizables
  - Validación de códigos de respuesta
  - Métricas de rendimiento

## Arquitectura de Comunicación

### Flujo de Autenticación
1. **Carga de certificado .cert**: Decodifica y valida certificado
2. **Preparación SSL**: Configura contexto SSL con certificado
3. **Solicitud de token**: Envía credenciales al endpoint de auth
4. **Almacenamiento de token**: Guarda JWT con fecha de expiración
5. **Renovación automática**: Renueva token antes de expiración

### Flujo de Envío DTE
1. **Validaciones previas**: Verifica JSON DTE válido y completo
2. **Preparación de datos**: Estructura payload según especificaciones MH
3. **Envío autenticado**: Transmite con token JWT en headers
4. **Procesamiento de respuesta**: Interpreta estado y mensajes del MH
5. **Actualización de factura**: Actualiza estado y datos recibidos

### Flujo de Consulta Estado
1. **Identificación del DTE**: Usa número de control y código de generación
2. **Consulta al MH**: Solicita estado actual del documento
3. **Interpretación de respuesta**: Mapea estados del MH a estados internos
4. **Actualización automática**: Refleja cambios en la factura

## Integración con Account Move

### Campos Agregados
- `l10n_sv_mh_status`: Estado de comunicación con MH
- `l10n_sv_mh_response`: Última respuesta del MH
- `l10n_sv_mh_send_date`: Fecha de envío
- `l10n_sv_mh_sello`: Sello digital recibido
- `l10n_sv_mh_observations`: Observaciones del MH

### Acciones Disponibles
- **Enviar al MH**: `action_send_to_mh()`
- **Consultar Estado**: `action_query_mh_status()`
- **Ver Logs**: `action_view_mh_logs()`
- **Reset Estado**: `action_reset_mh_status()`

## Estados de Comunicación

### Estados Principales
- **draft**: Borrador, no enviado
- **ready**: Listo para envío (JSON validado)
- **sent**: Enviado al MH, esperando confirmación
- **received**: Recibido por el MH
- **processed**: Procesado exitosamente por el MH
- **approved**: Aprobado por el MH
- **rejected**: Rechazado por el MH
- **error**: Error de comunicación

### Transiciones de Estado
```
draft → ready → sent → received → processed → approved
               ↓                            ↓
             error ←──────────────────── rejected
```

## Configuración

### Dependencias Requeridas
```python
'depends': [
    'l10n_sv_edi_base',        # Infraestructura EDI base
    'l10n_sv_edi_json',       # Generador JSON DTE
]

'external_dependencies': {
    'python': [
        'requests',           # Comunicación HTTP
        'cryptography',       # Manejo de certificados
        'OpenSSL',           # SSL/TLS avanzado
    ]
}
```

### Instalación de Dependencias Python
```bash
pip install requests cryptography pyOpenSSL
```

### Configuración Inicial
1. **Crear cliente API**:
   - Ir a Contabilidad > Localización SV > EDI > API MH > Clientes API
   - Crear nuevo cliente con certificado .cert
   - Configurar ambiente (certificación/producción)

2. **Configurar endpoints**:
   - Los endpoints se crean automáticamente
   - Verificar URLs según ambiente del MH
   - Probar conectividad

3. **Probar comunicación**:
   - Usar botón "Probar Conexión" en cliente API
   - Verificar autenticación exitosa
   - Revisar logs de comunicación

## Automatización

### Tareas Programadas (Cron Jobs)

#### Envío Automático de DTE
- **Frecuencia**: Cada 15 minutos
- **Función**: `cron_send_pending_dte()`
- **Propósito**: Envía automáticamente DTE listos al MH
- **Filtros**: JSON validado, no enviado, máximo 3 intentos

#### Consulta Automática de Estado
- **Frecuencia**: Cada 30 minutos
- **Función**: `cron_query_sent_dte_status()`
- **Propósito**: Consulta estado de DTE enviados
- **Filtros**: Enviados/recibidos, últimos 7 días, máximo 10 consultas

#### Limpieza de Logs
- **Frecuencia**: Semanal
- **Función**: `cleanup_old_logs(days=90)`
- **Propósito**: Elimina logs antiguos para mantener rendimiento
- **Configuración**: Conserva últimos 90 días por defecto

## Seguridad y Permisos

### Grupos de Acceso
- **account.group_account_user**: Lectura de clientes y logs
- **account.group_account_invoice**: Crear/modificar, acceso a logs
- **account.group_account_manager**: Acceso completo

### Datos Sensibles
- **Certificados**: Almacenados en base64 en base de datos
- **Tokens JWT**: Almacenados temporalmente, renovación automática
- **Contraseñas**: Cifradas en modelo de certificados
- **Logs**: Excluyen información sensible en headers

## Endpoints del MH

### Certificación (Testing)
- **Auth**: `https://apitestauth.mh.gob.sv/seguridad/auth`
- **Envío**: `https://apitest.mh.gob.sv/v1/dte`
- **Consulta**: `https://apitest.mh.gob.sv/v1/dte/consulta`
- **Contingencia**: `https://apitest.mh.gob.sv/v1/dte/contingencia`

### Producción
- **Auth**: `https://apiauth.mh.gob.sv/seguridad/auth`
- **Envío**: `https://api.mh.gob.sv/v1/dte`
- **Consulta**: `https://api.mh.gob.sv/v1/dte/consulta`
- **Contingencia**: `https://api.mh.gob.sv/v1/dte/contingencia`

## Manejo de Errores

### Errores Comunes
1. **Error de certificado**: Verificar formato .cert y contraseña
2. **Token expirado**: Renovación automática, verificar conectividad
3. **Timeout**: Ajustar configuración de timeout en cliente
4. **Validación MH**: Revisar JSON DTE generado
5. **Conectividad**: Verificar firewall y DNS

### Estrategias de Recuperación
- **Reintentos automáticos**: Con backoff exponencial
- **Logging detallado**: Para análisis post-mortem
- **Notificaciones**: Alertas en caso de errores críticos
- **Fallback**: Modo contingencia para casos extremos

## Monitoreo y Métricas

### KPIs Disponibles
- **Tasa de éxito**: Porcentaje de envíos exitosos
- **Tiempo de respuesta**: Latencia promedio del MH
- **Volumen de envíos**: Cantidad de DTE procesados
- **Errores por tipo**: Análisis de causas de fallo

### Dashboards
- Vista de logs con filtros avanzados
- Estadísticas por cliente API
- Métricas de rendimiento por endpoint
- Análisis de tendencias temporales

## Troubleshooting

### Logs Detallados
Cada comunicación genera un log con:
- Request/response completos
- Headers HTTP (sin datos sensibles)
- Tiempos de procesamiento
- Códigos de error específicos

### Herramientas de Diagnóstico
- **Probar Conexión**: Verificar conectividad básica
- **Probar Endpoint**: Validar endpoint específico
- **Ver Logs**: Análisis histórico de comunicaciones
- **Regenerar Token**: Forzar renovación de autenticación

## Versión y Compatibilidad

- **Versión**: 18.0.1.0.0
- **Odoo**: 18.0+
- **País**: El Salvador
- **Licencia**: LGPL-3
- **API MH**: Compatible con especificaciones v1.0