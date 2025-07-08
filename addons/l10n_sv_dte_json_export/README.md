# Invoice Attachment Export

Módulo para Odoo 18 que permite descargar masivamente todos los archivos adjuntos de facturas, incluyendo documentos electrónicos como JSON FSSE para El Salvador.

## Características

- Asistente para seleccionar facturas por rango de fechas o manualmente.
- Descarga todos los archivos adjuntos (PDF, XML, JSON, etc.) en un archivo `.zip`.
- Generación automática del archivo JSON FSSE para documentos tipo 14 (Factura Sujeto Excluido).
- Acceso directo al asistente desde el formulario de la factura.

## Instalación

1. Copia el módulo en la carpeta de addons personalizada.
2. Actualiza la lista de aplicaciones.
3. Busca e instala **Invoice Attachment Export**.

## Uso

- Abre cualquier factura validada.
- Haz clic en el botón **"Descargar adjuntos"** en la vista formulario.
- Selecciona el rango de fechas o las facturas deseadas.
- Presiona **"Descargar ZIP"** para obtener todos los adjuntos comprimidos.

## Dependencias

- `account` (Módulo base de contabilidad en Odoo)

## Capturas de pantalla

![Botón en factura](static/description/screenshot_button.png)
![Asistente de descarga](static/description/screenshot_wizard.png)

## Licencia

Este módulo está licenciado bajo la LGPL-3.0.

## Autor

**miliky**  
José Emilio Flores Meléndez  
📧 jefm@outlook.com  
🔗 [Repositorio en GitHub](https://github.com/miliky/odoo18)

---

¡Contribuciones y sugerencias son bienvenidas!
