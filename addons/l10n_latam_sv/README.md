# Módulo de Localización para El Salvador (l10n_latam_sv)
## Versión: 18.0.1.0.6
## Descripción
Este módulo extiende la funcionalidad de l10n_latam_base para agregar tipos de documentos específicos para El Salvador, cumpliendo con los requisitos de identificación locales según el catálogo "CAT_022_Tipo_de_documento_de_identificación_del_Receptor". Además, implementa el catálogo "CAT_019_Código_de_Actividad_Económica" para la gestión de giros comerciales.

## Características
### Tipos de Documentos Soportados
- DUI (Documento Único de Identidad) - Código 13
- NIT (Número de Identificación Tributaria) - Código 36
- Pasaporte - Código 03
- Carnet de Residente - Código 02
- Otro documento - Código 37
### Giros Comerciales (Actividades Económicas)
- Implementación del catálogo "CAT_019_Código_de_Actividad_Económica" de la DGII
- Campo de código para identificar cada actividad económica
- Posibilidad de importar actividades económicas desde Excel
- Ejemplos de actividades: Comerciante (10006), Estudiante (10003), entre otros
- Acceso directo desde el menú de Contactos > Configuración > Sectores
### Funcionalidades
- Integración con el módulo base de localización latinoamericana
- Selección de tipo de documento mediante botones de radio en la interfaz
- Sincronización automática entre el tipo de documento seleccionado y el campo de identificación estándar
- Etiquetado dinámico del campo de número según el tipo de documento seleccionado
- Valor predeterminado configurado como NIT para mayor compatibilidad con el sistema
- Gestión de giros comerciales según normativa de la DGII
### Interfaz de Usuario
- Interfaz mejorada para la selección de documentos en el formulario de contactos
- Visualización horizontal de opciones de documentos para mejor experiencia de usuario
- Campo de número etiquetado apropiadamente según el contexto
- Menú específico para gestionar los giros comerciales (actividades económicas)
## Validación Avanzada de Documentos
### Validación de NIT
- Formato completo (14 dígitos): Verifica que los primeros 2 dígitos estén entre 01 y 14 (códigos de departamento válidos)
- Formato homologado (9 dígitos): Valida el dígito verificador mediante algoritmo de módulo 10
- Validación en tiempo real con mensajes de error personalizados
### Validación de DUI
- Verifica la validez del Documento Único de Identidad mediante algoritmo de dígito verificador (módulo 10)
- Validación en tiempo real con mensajes de error personalizados
- Formato obligatorio: 8 dígitos + guion + 1 dígito verificador
## Mejoras Técnicas
### Mejoras en la Gestión de Contactos
- Anulación inteligente de la validación estándar de VAT de Odoo para documentos salvadoreños
- Manejo automático de tipos de documentos según estándares locales
- Mensajes de error personalizados para validaciones fallidas
### Optimizaciones Técnicas
- Implementación de restricciones (@api.constrains) para validación en tiempo real
- Sobrecarga de métodos create() y write() para manejo adecuado de documentos salvadoreños
- Función auxiliar _should_skip_vat_validation() para determinar cuándo omitir la validación estándar
## Instalación
1. Asegúrese de tener instalado el módulo l10n_latam_base
2. Instale este módulo desde la interfaz de Odoo (Aplicaciones > Buscar "El Salvador")
3. No requiere configuración adicional después de la instalación
## Migración de Datos de Giros Comerciales
Para migrar los datos de giros comerciales según la normativa de la DGII:

1. Acceda al menú Contactos > Sectores
2. Archive todos los registros existentes (seleccione todos y use la opción "Archivar")
3. Prepare un archivo Excel con las columnas: code, name, full_name
4. Importe el archivo Excel utilizando la función de importación de Odoo
## Dependencias
- l10n_latam_base
## Licencia
LGPL-3

## Compatibilidad
- Odoo 18.0
## Autor
JOSE EMILIO FLORES MELENDEZ Email: jefm@outlook.com Web: https://www.smart.dte.company/