# Extensión de Incoterms para El Salvador
## Descripción General
Este módulo extiende el modelo account.incoterms añadiendo el campo code_dgii para la clasificación según la Dirección General de Impuestos Internos de El Salvador.

## Características Principales
- Añade el campo code_dgii al modelo account.incoterms
- Integra el campo en las vistas de formulario y lista
- Facilita la clasificación de Incoterms según normativa salvadoreña
## Requisitos Técnicos
- Odoo 18.0
- Módulo base de contabilidad (account)
## Instalación
Para instalación manual:

1. Copiar el módulo a la carpeta de addons
2. Actualizar la lista de aplicaciones
3. Buscar e instalar "El Salvador - Incoterms DGII"
## Datos Incluidos
El módulo actualiza los Incoterms estándar con los códigos DGII correspondientes:

- EXW (En fábrica): 01
- FCA (Libre transportista): 02
- FAS (Libre al costado del buque): 08
- FOB (Libre a bordo): 09
- CFR (Costo y flete): 10
- DDP (Entrega con impuestos pagados): 07
- Y otros códigos según normativa salvadoreña
## Licencia
Este módulo está licenciado bajo LGPL-3.

## Soporte
Para soporte técnico, contactar al autor o visitar el repositorio en GitHub: https://github.com/miliky/odoo18

## Autor
- Nombre : José Emilio Flores Meléndez
- Email : jefm@outlook.com
- GitHub : https://github.com/miliky/odoo18