# Módulo de Localización Contable para El Salvador (l10n_sv)
## Versión: 18.0.1.0.4
## Descripción General
Este módulo proporciona la localización contable para El Salvador en Odoo 18, incluyendo el plan de cuentas, impuestos y configuraciones específicas requeridas por la legislación salvadoreña.

## Características Principales
### Plan de Cuentas
- Implementación del catálogo de cuentas adaptado a los requerimientos fiscales de El Salvador
- Estructura de cuentas contables optimizada para empresas salvadoreñas
- Configuración predeterminada de cuentas para operaciones comunes
### Impuestos
- IVA 13% para ventas y compras
- IVA 13% incluido en precio para ventas y compras
- Impuestos exentos para operaciones nacionales
- Configuración para exportaciones (0%)
- FOVIAL ($0.20 por galón)
- COTRANS ($0.10 por galón)
- Turismo 5%
### Códigos DGII
- Integración de códigos de la Dirección General de Impuestos Internos
- Campo personalizado code_dgii para clasificación fiscal según normativa salvadoreña
- Mapeo automático de impuestos con sus códigos DGII correspondientes:
  - "20": Impuesto al Valor Agregado 13%
  - "C3": Impuesto al Valor Agregado (exportaciones) 0%
  - "59": Turismo: por alojamiento (5%)
  - "D1": FOVIAL ($0.20 Ctvs. por galón)
  - "C8": COTRANS ($0.10 Ctvs. por galón)
### Configuración de Compañía
- Configuración automática de parámetros fiscales para empresas salvadoreñas
- Prefijos de cuentas para efectivo, bancos y transferencias
- Cuentas predeterminadas para diferencias de cambio
- Cuentas para descuentos por pronto pago
## Requisitos Técnicos
- Odoo 18.0
- Módulo base de contabilidad (account)
## Instalación
El módulo se instala automáticamente cuando se selecciona El Salvador como país de la empresa durante la configuración inicial de Odoo.

Para instalación manual:

1. Copiar el módulo a la carpeta de addons
2. Actualizar la lista de aplicaciones
3. Buscar e instalar "El Salvador - Accounting"
## Uso
Después de la instalación, el sistema estará configurado con:

- Plan de cuentas salvadoreño
- Impuestos predefinidos con sus tasas correspondientes
- Grupos de impuestos clasificados según normativa local
## Mantenimiento
Este módulo es mantenido por José Emilio Flores Meléndez.

## Licencia
Este módulo está licenciado bajo LGPL-3.

## Contribuciones
Las contribuciones son bienvenidas a través de solicitudes de extracción en el repositorio GitHub.

## Soporte
Para soporte técnico, contactar al autor o visitar el repositorio en GitHub: https://github.com/miliky/