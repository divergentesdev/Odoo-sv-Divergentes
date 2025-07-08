Trae

Used 1 context

README.md 1-1

Necesito ver el archivo index.html del módulo l10n_sv_city para actualizar el README.md con la información más reciente.

l10n_sv_city\static\description\index.html :( 1 - 200 )

# Distritos y Municipios de El Salvador
## Versión: 18.0.1.0.2
## Descripción
Este módulo para Odoo proporciona una localización para El Salvador, para distritos y municipios organizados para facilitar la gestión de direcciones.

## Características
### Localización Geográfica Completa
- Lista completa de distritos y municipios de El Salvador
- Interfaz adaptada a la terminología local (Distrito en lugar de Ciudad, Municipio en lugar de Estado)
- Oculta automáticamente el campo de código postal para direcciones de El Salvador
- Filtrado inteligente de distritos según el municipio seleccionado
- El Salvador configurado como país predeterminado para nuevos contactos
- Menú dedicado para administrar la lista de distritos
- Formato de dirección adaptado a normativa DGII (distrito antes de la dirección)
- Moneda USD configurada por defecto para El Salvador
### Mejoras de Usabilidad
- Selección automática de distrito : Al cambiar de municipio, el sistema selecciona automáticamente el primer distrito disponible, evitando valores incorrectos.
- Priorización de municipios : La lista desplegable de municipios muestra primero los de El Salvador, facilitando la búsqueda sin necesidad de seleccionar antes el país.
- Valores predeterminados : El Salvador se establece como país predeterminado para nuevos contactos, agilizando el proceso de creación.
- Interfaz intuitiva con etiquetas adaptadas al contexto salvadoreño
## Funcionamiento
Una vez instalado, el módulo:

- Cambia automáticamente las etiquetas de "Ciudad" a "Distrito" y "Estado" a "Municipio"
- Establece El Salvador como país predeterminado en los formularios de contacto
- Oculta el campo de código postal cuando se selecciona El Salvador como país
- Proporciona una lista filtrada de distritos basada en el municipio seleccionado
- Selecciona automáticamente el primer distrito disponible al cambiar de municipio
- Muestra primero los municipios de El Salvador en las listas desplegables para facilitar la selección
Puede acceder a la lista completa de distritos desde el menú Contactos > Configuración > Localización > Ciudades.

## Instalación
1. Descargue el módulo y colóquelo en la carpeta de addons de Odoo
2. Actualice la lista de módulos
3. Busque e instale el módulo "Municipalities / Districts for El Salvador"
## Información Técnica
### Dependencias
- base
- base_address_extended
- contacts
### Compatibilidad
- Odoo 18.0
### Licencia
- LGPL-3
## Autor
JOSE EMILIO FLORES MELENDEZ
Email: jefm@outlook.com Web: https://www.smart.dte.company/