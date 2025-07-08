import json
import logging
import re
from datetime import datetime
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)

# Importar templates oficiales del MH
try:
    import sys
    if '/mnt/extra-addons' not in sys.path:
        sys.path.append('/mnt/extra-addons')
    from templates_oficiales_mh import TEMPLATES_OFICIALES
    _logger.info(f"Templates oficiales cargados correctamente: {list(TEMPLATES_OFICIALES.keys())}")
except ImportError as e:
    _logger.error(f"Error importando templates oficiales: {e}")
    TEMPLATES_OFICIALES = {}


class L10nSvJsonGenerator(models.Model):
    """Generador de JSON DTE para El Salvador - ADAPTADO CON LÓGICA VALIDADA"""
    _name = 'l10n_sv.json.generator'
    _description = 'Generador JSON DTE El Salvador'
    
    # Reglas diferenciadas por tipo de documento basadas en esquemas oficiales y lógica validada
    DTE_RULES = {
        '01': {  # Factura - LÓGICA VALIDADA 29/06/2025
            'version': 1,
            'receptor_required': 'conditional',  # >= $1095
            'receptor_types': ['36','13','02','03','37'],
            'tributos_items_allowed': ['C3','59','71','D1','C5','C6','C7','C8','D5','D4','19','28','31','32','33','34','35','36','37','38','39','42','43','44','50','51','52','53','54','55','58','77','78','79','85','86','91','92','A1','A5','A7','A9'],
            'required_fields': ['ivaItem', 'saldoFavor', 'numPagoElectronico'],
            'tributos_resumen': 'conditional',  # null para consumidor final
            'schema_file': 'fe-fc-v1.json'
        },
        '03': {  # CCF
            'version': 3,
            'receptor_required': True,
            'receptor_types': ['36'],  # Solo NIT
            'tributos_items_allowed': ['20','C3','59','71','D1','C5','C6','C7','C8','D5','D4','19','28','31','32','33','34','35','36','37','38','39','42','43','44','50','51','52','53','54','55','58','77','78','79','85','86','91','92','A1','A5','A7','A9'],
            'required_fields': ['ivaPerci1'],
            'schema_file': 'fe-ccf-v3.json'
        },
        '05': {  # Nota de Crédito
            'version': 3,
            'receptor_required': True,
            'related_docs_required': True,
            'related_doc_types': ['03','07'],
            'tributos_items_allowed': ['20','C3','59','71','D1','C8','D5','D4'],
            'no_payments': True,
            'schema_file': 'fe-nc-v3.json'
        },
        '06': {  # Nota de Débito
            'version': 3,
            'receptor_required': True,
            'related_docs_required': True,
            'related_doc_types': ['03','07'],
            'tributos_items_allowed': ['20','C3','59','71','D1','C8','D5','D4'],
            'required_fields': ['numPagoElectronico'],
            'schema_file': 'fe-nd-v3.json'
        },
        '11': {  # Factura de Exportación
            'version': 1,
            'receptor_required': 'conditional',  # >= $10000
            'receptor_structure': 'internacional',
            'tributos_items_allowed': ['C3'],
            'required_fields': ['tipoItemExpor', 'recintoFiscal', 'regimen', 'seguro', 'flete', 'codIncoterms'],
            'schema_file': 'fe-fex-v1.json'
        },
        '14': {  # Factura Sujeto Excluido
            'version': 1,
            'receptor_field': 'sujetoExcluido',
            'simplified_structure': True,
            'schema_file': 'fe-fse-v1.json'
        }
    }

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre del generador'
    )
    
    document_type_id = fields.Many2one(
        'l10n_sv.document.type',
        string='Tipo de Documento',
        required=True,
        help='Tipo de documento DTE que puede generar'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    template = fields.Text(
        string='Plantilla JSON',
        help='Plantilla base para generar JSON DTE'
    )

    def generate_json_dte(self, move_id):
        """Genera JSON DTE usando templates oficiales del MH"""
        self.ensure_one()
        move = self.env['account.move'].browse(move_id)
        
        if not move.exists():
            raise exceptions.UserError(_('Factura no encontrada'))
        
        # Validar que el tipo de documento coincida
        if move.l10n_sv_document_type_id != self.document_type_id:
            raise exceptions.UserError(_(
                'El tipo de documento de la factura no coincide con este generador'
            ))
        
        # Obtener template oficial del MH
        document_type_code = self.document_type_id.code
        
        # Log para depuración
        _logger.info(f"Generando JSON para tipo de documento: {document_type_code}")
        
        # Usar template oficial si está disponible, sino usar el configurado
        if TEMPLATES_OFICIALES and document_type_code in TEMPLATES_OFICIALES:
            _logger.info(f"Usando template oficial MH para tipo {document_type_code}")
            template = TEMPLATES_OFICIALES[document_type_code]
            json_data = self._populate_template(template, move)
        else:
            _logger.warning(f"Template oficial no disponible para tipo {document_type_code}, usando lógica existente")
            # Fallback a lógica existente
            if document_type_code == '01':
                json_data = self._generate_factura_json(move)
            elif document_type_code == '03':
                _logger.info("Usando _generate_ccf_json")
                json_data = self._generate_ccf_json(move)
            elif document_type_code == '04':
                _logger.info("Usando _generate_nota_remision_json")
                json_data = self._generate_nota_remision_json(move)
            elif document_type_code == '05':
                json_data = self._generate_nota_credito_json(move)
            elif document_type_code == '11':
                json_data = self._generate_exportacion_json(move)
            else:
                json_data = self._generate_generic_json(move)
        
        # Log final JSON values
        _logger.info(f"Final JSON version: {json_data['identificacion']['version']}")
        _logger.info(f"Final JSON tipoDte: {json_data['identificacion']['tipoDte']}")
        _logger.info(f"Final JSON numeroControl: {json_data['identificacion']['numeroControl']}")
        
        return json_data

    
    def _get_base_json_structure(self, move):
        """Estructura base común para todos los DTE"""
        # Validar que el tipo de documento esté definido
        if not move.l10n_sv_document_type_id:
            raise exceptions.UserError(_(
                'Debe seleccionar un tipo de documento DTE antes de generar el JSON'
            ))
        
        utils = self.env['l10n_sv.dte.utils']
        config = move.company_id.get_edi_configuration()
        
        # Obtener fecha y hora actuales
        now = utils.get_current_datetime_sv()
        # Usar fecha de factura para emisión
        fecha_emision = utils.format_date(move.invoice_date or now.date())
        hora_emision = utils.format_time(now.time())
        
        return {
            "identificacion": {
                "version": 1,  # Default version, will be overridden for CCF
                "ambiente": utils.get_ambiente_code(config.environment),
                "tipoDte": str(move.l10n_sv_document_type_id.code) if move.l10n_sv_document_type_id else "01",
                "numeroControl": move.l10n_sv_edi_numero_control,  # Usar el número de control ya generado
                "codigoGeneracion": move.l10n_sv_edi_codigo_generacion or utils.generate_codigo_generacion(),
                "tipoModelo": utils.get_tipo_modelo_code(),
                "tipoOperacion": utils.get_tipo_operacion_code(move.l10n_sv_operation_type),
                "tipoContingencia": None,
                "motivoContin": None,
                "fecEmi": fecha_emision,
                "horEmi": hora_emision,
                "tipoMoneda": utils.get_moneda_code(move.currency_id.name)
            },
            "documentoRelacionado": self._get_documento_relacionado(move),
            "emisor": self._get_emisor_data(move),
            "receptor": self._get_receptor_data(move),
            "otrosDocumentos": None,
            "ventaTercero": None,
            "cuerpoDocumento": self._get_cuerpo_documento(move),
            "resumen": self._get_resumen_data(move),
            "extension": self._get_extension_data(move),
            "apendice": None
        }

    def _get_extension_data(self, move):
        """Datos de extensión según tipo de documento"""
        document_type = move.l10n_sv_document_type_id.code if move.l10n_sv_document_type_id else "01"
        
        
        if document_type == "01":  # Factura - extension debe ser null según JSON válido
            return None  # OBLIGATORIO: extension = null para Factura tipo 01
        elif document_type == "03":  # CCF
            # Para CCF, generar datos válidos para llenar template
            receptor_name = move.partner_id.name if move.partner_id else "Cliente"
            receptor_vat = move.partner_id.vat if move.partner_id and move.partner_id.vat else "00000000"
            
            return {
                "nombEntrega": "Sistema Facturación",
                "docuEntrega": "12345678",
                "nombRecibe": receptor_name,
                "docuRecibe": receptor_vat,
                "placaVehiculo": "N/A",
                "observaciones": "Sin observaciones"
            }
        else:
            # Para otros tipos, usar valores null por defecto
            return {
                "nombEntrega": None,
                "docuEntrega": None,
                "nombRecibe": None,
                "docuRecibe": None,
                "placaVehiculo": None,
                "observaciones": None
            }

    def _get_emisor_data(self, move):
        """Datos del emisor"""
        utils = self.env['l10n_sv.dte.utils']
        company = move.company_id
        
        # Validar que el movimiento tenga establecimiento y punto de venta
        if not move.l10n_sv_establishment_id:
            raise exceptions.UserError(_(
                'La factura no tiene establecimiento asignado. '
                'Por favor seleccione un establecimiento antes de generar el DTE.'
            ))
        
        if not move.l10n_sv_point_of_sale_id:
            raise exceptions.UserError(_(
                'La factura no tiene punto de venta asignado. '
                'Por favor seleccione un punto de venta antes de generar el DTE.'
            ))
        
        # Determinar actividad económica
        codigo_actividad = company.l10n_sv_codigo_actividad or "01111"
        desc_actividad = company.l10n_sv_desc_actividad or "Actividad económica general"
        
        # Dirección del establecimiento
        establishment = move.l10n_sv_establishment_id
        departamento = establishment.departamento_code or "06"
        municipio = establishment.municipio_code or "14"
        
        return {
            "nit": utils.format_nit(company.l10n_sv_nit or company.vat),
            "nrc": company.partner_id.company_registry or "",
            "nombre": utils.clean_text_for_json(company.name, 200),
            "codActividad": codigo_actividad,
            "descActividad": utils.clean_text_for_json(desc_actividad, 150),
            "nombreComercial": utils.clean_text_for_json(company.name, 150),
            "tipoEstablecimiento": "01",  # Sucursal
            "direccion": {
                "departamento": departamento,
                "municipio": municipio,
                "complemento": utils.clean_text_for_json(
                    establishment.street or company.street or "", 200
                )
            },
            "telefono": company.phone or "25919000",  # Teléfono por defecto del emisor
            "correo": utils.clean_text_for_json(company.email or "", 100),
            "codEstableMH": establishment.code.zfill(4),  # Asegurar 4 dígitos
            "codEstable": establishment.code.zfill(4),
            "codPuntoVentaMH": move.l10n_sv_point_of_sale_id.code.zfill(4),  # Asegurar 4 dígitos según especificación
            "codPuntoVenta": move.l10n_sv_point_of_sale_id.code.zfill(4)
        }

    def _get_receptor_data(self, move):
        """Datos del receptor según tipo de documento y posición fiscal - LÓGICA VALIDADA"""
        document_type = move.l10n_sv_document_type_id.code if move.l10n_sv_document_type_id else "01"
        partner = move.partner_id
        fiscal_position = move.fiscal_position_id
        
        # Aplicar lógica según tipo de documento
        if document_type == '03':  # CCF
            # CCF SIEMPRE requiere datos completos del receptor, NUNCA consumidor final
            return self._get_receptor_ccf(partner, move)
        elif document_type == '11':  # Exportación
            return self._get_receptor_exportacion(partner, move)
        elif document_type == '14':  # Sujeto Excluido
            return self._get_sujeto_excluido_data(partner, move)
        elif document_type == '01':  # Factura
            # Solo Factura puede ser consumidor final
            if self._is_final_consumer(partner, fiscal_position):
                return self._get_receptor_consumidor_final(partner, move)
            else:
                return self._get_receptor_contribuyente(partner, move)
        else:
            return self._get_receptor_contribuyente(partner, move)
    
    def _is_final_consumer(self, partner, fiscal_position):
        """Determina si es consumidor final por múltiples criterios"""
        # Criterio 1: Posición fiscal marcada como consumidor final
        if fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
            return True
        
        # Criterio 2: No tiene NIT/VAT válido
        if not partner.vat:
            return True
            
        # Criterio 3: NIT inválido (no 14 dígitos)
        vat_clean = ''.join(filter(str.isdigit, partner.vat or ''))
        if len(vat_clean) != 14:
            return True
            
        # Criterio 4: Nombre específico
        if partner.name and 'consumidor final' in partner.name.lower():
            return True
            
        # Criterio 5: Campo específico del partner
        if hasattr(partner, 'l10n_sv_is_final_consumer') and partner.l10n_sv_is_final_consumer:
            return True
        
        # Por defecto, si no hay posición fiscal, asumir consumidor final
        return fiscal_position is None
    
    def _get_receptor_consumidor_final(self, partner, move):
        """Receptor para consumidor final - CORREGIDO según esquema MH"""
        utils = self.env['l10n_sv.dte.utils']
        
        # Según esquema oficial MH: nombre debe ser el real del partner
        return {
            "tipoDocumento": None,
            "numDocumento": None,
            "nrc": None,
            "nombre": utils.clean_text_for_json(partner.name, 250),  # Nombre real del cliente
            "codActividad": None,
            "descActividad": None,
            "direccion": None,
            "telefono": None,
            "correo": partner.email  # Solo email real del partner
        }
    
    
    def _get_receptor_ccf(self, partner, move):
        """Receptor para CCF - SIEMPRE requiere datos completos, NUNCA consumidor final"""
        utils = self.env['l10n_sv.dte.utils']
        
        # CCF NUNCA puede ser consumidor final según especificaciones MH
        if not partner.vat:
            raise exceptions.UserError(_(
                'CCF requiere un cliente con NIT válido. '
                'No se puede emitir CCF a consumidor final.'
            ))
        utils = self.env['l10n_sv.dte.utils']
        
        # Dirección del receptor
        departamento = "06"  # Por defecto San Salvador
        municipio = "14"     # Por defecto San Salvador
        
        if partner.city_id and hasattr(partner.city_id, 'district_code'):
            if partner.city_id.district_code and len(partner.city_id.district_code) == 4:
                departamento = partner.city_id.district_code[:2]
                municipio = partner.city_id.district_code[2:]
        
        # Determinar tipo de documento de identificación
        doc_type = partner.l10n_sv_document_type_code or "36"
        if doc_type == "36":  # NIT
            num_documento = utils.format_nit(partner.vat)
        elif doc_type == "13":  # DUI
            num_documento = utils.format_dui(partner.vat) if hasattr(utils, 'format_dui') else partner.vat
        else:
            num_documento = partner.vat or ""
        
        # CCF estructura según esquema oficial MH v3
        # IMPORTANTE: CCF requiere nit y nombreComercial, NO incluye tipoDocumento ni numDocumento
        receptor_data = {
            "nit": utils.format_nit(partner.vat),
            "nrc": partner.company_registry if partner.company_registry else "0000000",
            "nombre": utils.clean_text_for_json(partner.name, 200),
            "codActividad": partner.industry_id.code if partner.industry_id and partner.industry_id.code else "47739",
            "descActividad": utils.clean_text_for_json(
                partner.industry_id.name if partner.industry_id else "Actividad general", 150
            ),
            "nombreComercial": utils.clean_text_for_json(partner.commercial_name or partner.name, 150),
            "direccion": {
                "departamento": departamento,
                "municipio": municipio,
                "complemento": utils.clean_text_for_json(
                    partner.street or "Ciudad", 200
                )
            },
            "telefono": partner.phone or "0000-0000",
            "correo": utils.clean_text_for_json(partner.email or "cliente@empresa.com", 100)
        }
        
        return receptor_data
    
    def _get_receptor_contribuyente(self, partner, move):
        """Receptor para contribuyentes con NIT"""
        utils = self.env['l10n_sv.dte.utils']
        partner = move.partner_id
        
        # Determinar tipo de documento de identificación
        doc_type = partner.l10n_sv_document_type_code or "36"
        if doc_type == "36":  # NIT
            num_documento = utils.format_nit(partner.vat)
        elif doc_type == "13":  # DUI
            num_documento = utils.format_dui(partner.vat)
        else:
            num_documento = partner.vat or ""
        
        # Dirección del receptor
        departamento = "06"  # Por defecto San Salvador
        municipio = "14"     # Por defecto San Salvador
        
        if partner.city_id and hasattr(partner.city_id, 'district_code'):
            if partner.city_id.district_code and len(partner.city_id.district_code) == 4:
                departamento = partner.city_id.district_code[:2]
                municipio = partner.city_id.district_code[2:]
        
        # Para clientes extranjeros
        if partner.country_id and partner.country_id.code != 'SV':
            departamento = "00"
            municipio = "00"
        
        receptor_data = {
            "tipoDocumento": doc_type,
            "numDocumento": num_documento,
            "nrc": partner.company_registry if partner.company_registry else None,
            "nombre": utils.clean_text_for_json(partner.name, 200),
            "codActividad": partner.industry_id.code if partner.industry_id else None,
            "descActividad": utils.clean_text_for_json(
                partner.industry_id.name if partner.industry_id else "Actividad general", 150
            ),
            "direccion": {
                "departamento": departamento,
                "municipio": municipio,
                "complemento": utils.clean_text_for_json(
                    partner.street or "Ciudad", 200
                )
            },
            "telefono": partner.phone or "0000-0000",
            "correo": utils.clean_text_for_json(partner.email or "cliente@empresa.com", 100)
        }
        
        # Solo agregar nombreComercial si es diferente del nombre
        if partner.commercial_company_name and partner.commercial_company_name != partner.name:
            receptor_data["nombreComercial"] = utils.clean_text_for_json(partner.commercial_company_name, 150)
        
        return receptor_data

    def _get_cuerpo_documento(self, move):
        """Líneas del documento"""
        utils = self.env['l10n_sv.dte.utils']
        cuerpo = []
        
        # Obtener tipo de documento para lógica específica
        document_type = move.l10n_sv_document_type_id.code if move.l10n_sv_document_type_id else "01"
        
        item_num = 1
        for line in move.invoice_line_ids:
            if line.display_type in ('line_section', 'line_note'):
                continue
            
            # Obtener código de unidad de medida
            uom_code = 99  # Por defecto "No aplica"
            if line.product_uom_id and hasattr(line.product_uom_id, 'code'):
                uom_code = line.product_uom_id.code or 99
            
            # Determinar tipo de item (debe ser valor válido del catálogo MH)
            tipo_item = int(line.l10n_sv_item_type) if hasattr(line, 'l10n_sv_item_type') and line.l10n_sv_item_type else 1
            
            # Calcular montos por línea
            # Según ejemplo de N1CO, el precio unitario se muestra tal cual (con IVA si lo incluye)
            precio_unitario = utils.format_currency_amount(line.price_unit)
            cantidad = utils.format_currency_amount(line.quantity)
            
            # Calcular descuento
            if line.discount:
                monto_descu = utils.format_currency_amount(line.price_unit * line.quantity * line.discount / 100)
            else:
                monto_descu = 0.00
            
            # Clasificar venta según impuestos
            venta_no_suj = 0.00
            venta_exenta = 0.00
            venta_gravada = 0.00
            
            # Obtener tributos aplicados según lógica validada
            tributos = self._get_tributos_item(line, move)
            
            # Clasificar venta según lógica validada
            # Para consumidor final: tributos = null pero venta gravada con IVA
            fiscal_position = move.fiscal_position_id
            
            # IMPORTANTE: Diferencia entre CCF y Factura
            if document_type == '03':  # CCF
                # Para CCF: ventaGravada es SIN IVA (base imponible)
                if tributos and '20' in tributos:
                    venta_gravada = utils.format_currency_amount(line.price_subtotal)
                elif tributos and 'C3' in tributos:
                    venta_exenta = utils.format_currency_amount(line.price_subtotal)
                elif not tributos:
                    # Si no hay tributos pero es CCF, asumir que es gravado con IVA
                    venta_gravada = utils.format_currency_amount(line.price_subtotal)
                    tributos = ['20']  # Asignar IVA por defecto
                else:
                    venta_no_suj = utils.format_currency_amount(line.price_subtotal)
            else:  # Factura (01) u otros
                # Para consumidor final: precio es sin IVA, usar directamente
                if fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
                    # Para FCF: price_subtotal es la base gravable (sin IVA)
                    venta_gravada = utils.format_currency_amount(line.price_subtotal)
                    _logger.info(f"FCF - Línea {line.name}: price_unit={line.price_unit}, price_subtotal={line.price_subtotal}, venta_gravada={venta_gravada}")
                elif tributos and '20' in tributos:
                    venta_gravada = utils.format_currency_amount(line.price_subtotal)
                elif tributos and 'C3' in tributos:
                    venta_exenta = utils.format_currency_amount(line.price_subtotal)
                else:
                    # Para Factura 01: si hay venta gravada pero no hay tributos específicos, 
                    # verificar si la línea tiene impuestos IVA
                    has_iva = False
                    for tax in line.tax_ids:
                        if tax.amount == 13:  # IVA 13%
                            has_iva = True
                            break
                    
                    if has_iva:
                        venta_gravada = utils.format_currency_amount(line.price_subtotal)
                        tributos = ['20']  # Asignar IVA
                    else:
                        venta_no_suj = utils.format_currency_amount(line.price_subtotal)
            
            # =====================================================================
            # LÓGICA ESTRICTA DE TRIBUTOS POR TIPO DE DOCUMENTO
            # =====================================================================
            # REGLA CRÍTICA: NUNCA MEZCLAR LÓGICAS ENTRE TIPOS DE DOCUMENTO
            # - CCF (document_type '03'): Tiene sus propias reglas específicas
            # - FCF (document_type '01' + fiscal_position.l10n_sv_is_final_consumer): Reglas específicas
            # - Factura Normal (document_type '01' + NO es final consumer): Reglas específicas
            # =====================================================================
            
            if document_type == '03':
                # ===== CRÉDITO FISCAL CCF =====
                # Reglas específicas para CCF según esquema MH
                cod_tributo = None  # CCF: codTributo siempre null
                if venta_gravada > 0:
                    tributos = ["20"]  # CCF con IVA: tributos = ["20"]
                    # CCF: calcular IVA usando formato específico para ivaItem
                    iva_item = utils.format_iva_item_amount(utils.calculate_iva_amount_precise(venta_gravada))
                else:
                    tributos = None  # CCF sin IVA: tributos = null
                    iva_item = 0.00
                    
            elif document_type == '01':
                # ===== FACTURAS (FCF Y NORMAL) =====
                if self._is_final_consumer(move.partner_id, fiscal_position):
                    # ===== FACTURA CONSUMIDOR FINAL =====
                    # Reglas específicas para FCF según error MH
                    cod_tributo = None  # FCF: codTributo siempre null
                    if venta_gravada > 0:
                        tributos = ["20"]  # FCF con IVA: tributos = ["20"] (SEGÚN ERROR MH)
                        # FCF: extraer IVA del total (precio incluye IVA para consumidor final)
                        iva_item = utils.format_iva_item_amount(venta_gravada * 13 / 113)
                    else:
                        tributos = None  # FCF sin IVA: tributos = null
                        iva_item = 0.00
                else:
                    # ===== FACTURA NORMAL (CONTRIBUYENTE) =====
                    # Reglas para factura a contribuyente
                    cod_tributo = None  # Factura: codTributo siempre null
                    if venta_gravada > 0:
                        tributos = ["20"]  # Factura con IVA: tributos = ["20"]
                        # Factura: calcular IVA usando formato específico para ivaItem
                        iva_item = utils.format_iva_item_amount(utils.calculate_iva_amount_precise(venta_gravada))
                    else:
                        tributos = None  # Factura sin IVA: tributos = null
                        iva_item = 0.00
            else:
                # ===== OTROS TIPOS DE DOCUMENTO =====
                # Para tipos no implementados
                cod_tributo = None
                tributos = None
                iva_item = 0.00
            
            item = {
                "numItem": item_num,
                "tipoItem": tipo_item,
                "numeroDocumento": None,
                "cantidad": cantidad,
                "codigo": utils.clean_text_for_json(line.product_id.default_code or f"PROD-{item_num:03d}", 25),
                "codTributo": cod_tributo,  # Usar la variable calculada, no siempre None
                "uniMedida": uom_code,
                "descripcion": utils.clean_text_for_json(line.name or line.product_id.name or "Producto", 1000),
                "precioUni": utils.format_body_amount(precio_unitario),
                "montoDescu": utils.format_body_amount(monto_descu),
                "ventaNoSuj": utils.format_body_amount(venta_no_suj),
                "ventaExenta": utils.format_body_amount(venta_exenta),
                "ventaGravada": utils.format_body_amount(venta_gravada),
                "psv": 0.00,
                "noGravado": 0.00
            }
            
            # Log para verificar
            if document_type == '03':
                _logger.info(f"Item {item_num} antes de agregar ivaItem - codTributo: {cod_tributo}")
            
            # Agregar ivaItem según tipo de documento
            if document_type == '01':  # Factura - según error MH, es requerido
                item["ivaItem"] = utils.format_body_amount(iva_item)
                _logger.info(f"Agregando ivaItem={utils.format_body_amount(iva_item)} a item {item_num} para Factura 01")
            # CCF NO debe tener ivaItem según esquema oficial MH
            elif document_type == '03':  # CCF - ivaItem no permitido
                _logger.info(f"CCF no requiere ivaItem - Item {item_num} sin ivaItem")
                _logger.info(f"Item completo para CCF: {item}")
            
            # Siempre incluir tributos (puede ser null para consumidor final)
            item["tributos"] = tributos
            
            # DEBUGGING: Log completo del item generado
            _logger.info(f"=== ITEM {item_num} GENERADO ===")
            _logger.info(f"Tipo documento: {document_type}")
            _logger.info(f"Es FCF: {fiscal_position.l10n_sv_is_final_consumer if fiscal_position else False}")
            _logger.info(f"ventaGravada: {item['ventaGravada']}")
            _logger.info(f"ivaItem: {item.get('ivaItem', 'NO INCLUIDO')}")
            _logger.info(f"tributos: {item['tributos']}")
            _logger.info(f"codTributo: {item['codTributo']}")
            _logger.info(f"Cálculo IVA: {item['ventaGravada']} * 0.13 = {float(item['ventaGravada']) * 0.13}")
            
            cuerpo.append(item)
            item_num += 1
        
        return cuerpo

    def _get_resumen_data(self, move):
        """Resumen del documento"""
        utils = self.env['l10n_sv.dte.utils']
        
        # Obtener tipo de documento para lógica específica
        document_type = move.l10n_sv_document_type_id.code if move.l10n_sv_document_type_id else "01"
        
        # Recalcular totales desde las líneas para asegurar consistencia
        total_no_suj = 0.00
        total_exenta = 0.00
        total_gravada = 0.00
        total_iva = 0.00
        
        fiscal_position = move.fiscal_position_id
        
        # Sumar desde las líneas del documento
        for line in move.invoice_line_ids:
            if line.display_type in ('line_section', 'line_note'):
                continue
            
            # Determinar tipo de venta según impuestos
            tributos = self._get_tributos_item(line, move)
            
            # Calcular montos según tipo de venta
            if self._is_final_consumer(move.partner_id, fiscal_position):
                # Para consumidor final: CONSISTENTE con cálculo del cuerpo
                # FCF: precio INCLUYE IVA, extraer IVA con fórmula oficial
                base_gravada = line.price_subtotal  # Base sin IVA
                iva_linea = base_gravada * 13 / 113  # IVA extraído (mismo cálculo que cuerpo)
                
                total_gravada += base_gravada  # Base sin IVA
                total_iva += iva_linea  # IVA calculado
            elif tributos and '20' in tributos:
                # Contribuyente con IVA
                total_gravada += line.price_subtotal
                # Para FCF siempre usar formula sin IVA incluido
                if self._is_final_consumer(move.partner_id, fiscal_position):
                    # FCF: precio INCLUYE IVA, usar fórmula consistente
                    total_iva += (line.price_subtotal * 13 / 113)
                elif line.tax_ids and any(tax.price_include for tax in line.tax_ids):
                    # IVA incluido: extraer del total
                    total_iva += (line.price_subtotal * 13 / 113)
                else:
                    # IVA no incluido: calcular sobre la base usando función estándar
                    total_iva += utils.calculate_iva_amount(line.price_subtotal)
            elif tributos and 'C3' in tributos:
                # Exportación
                total_exenta += line.price_subtotal
            else:
                # Sin tributos
                total_no_suj += line.price_subtotal
        
        # Formatear a 2 decimales
        total_no_suj = utils.format_currency_amount(total_no_suj)
        total_exenta = utils.format_currency_amount(total_exenta)
        total_gravada = utils.format_currency_amount(total_gravada)
        total_iva = utils.format_currency_amount(total_iva)
        
        sub_total_ventas = total_no_suj + total_exenta + total_gravada
        
        # Cálculo correcto según especificaciones MH:
        # FCF (01): IVA incluido en precios, montoTotalOperacion = totalPagar = sub_total_ventas
        # CCF (03): IVA desglosado, montoTotalOperacion = totalPagar = sub_total_ventas + total_iva
        
        if fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
            # FCF: montoTotalOperacion = base + IVA (precio final que paga el cliente)
            monto_total_operacion = sub_total_ventas + total_iva
            total_a_pagar = sub_total_ventas + total_iva  # Ambos iguales
        else:
            # CCF: IVA se suma explícitamente al subtotal
            monto_total_operacion = sub_total_ventas + total_iva
            total_a_pagar = sub_total_ventas + total_iva  # Ambos iguales
        
        # Condición de operación
        condicion_operacion = 1  # Contado por defecto
        if move.invoice_payment_term_id and move.invoice_payment_term_id.line_ids:
            if any(line.nb_days > 0 for line in move.invoice_payment_term_id.line_ids):
                condicion_operacion = 2  # Crédito
        
        # Formas de pago según catálogo CAT-017 del MH
        # Para CCF debe ser null según JSON exitoso
        if document_type == '03':  # CCF
            pagos = None
        else:
            # Determinar código de pago según el journal
            # CAT-017: 01=Billetes y monedas, 02=Tarjeta Débito, 03=Tarjeta Crédito, 
            # 04=Cheque, 05=Transferencia-Depósito Bancario, 08=Dinero electrónico, etc.
            codigo_pago = "01"  # Billetes y monedas por defecto
            
            if move.journal_id:
                # Mapeo de tipos de journal a códigos CAT-017
                journal_type_mapping = {
                    'bank': "05",     # Transferencia-Depósito Bancario
                    'cash': "01",     # Billetes y monedas
                    'general': "99",  # Otros
                }
                
                # Si el journal es de tipo banco, usar transferencia
                if move.journal_id.type in journal_type_mapping:
                    codigo_pago = journal_type_mapping[move.journal_id.type]
                
                # Si tiene configurado un método de pago específico
                if hasattr(move.journal_id, 'l10n_sv_payment_code'):
                    codigo_pago = move.journal_id.l10n_sv_payment_code
            
            # Construir estructura de pagos
            pagos = [{
                "codigo": codigo_pago,
                "montoPago": utils.format_currency_amount(total_a_pagar),
                "referencia": None,
                "plazo": move.l10n_sv_payment_term_code if move.l10n_sv_payment_term_code else "01",
                "periodo": move.l10n_sv_payment_term_period if move.l10n_sv_payment_term_period else None
            }]
        
        # Aplicar lógica validada para tributos en resumen según LOGICA_VALIDADA.md
        if self._is_final_consumer(move.partner_id, fiscal_position):
            # Para consumidor final: tributos = null (estrictamente según LOGICA_VALIDADA.md)
            tributos = None
        else:
            # Para contribuyentes: calcular tributos normalmente
            tributos = []
            if total_iva > 0:
                if document_type == '03':  # CCF
                    # CCF usa descripción diferente
                    tributos = [{
                        "codigo": "20",
                        "descripcion": "IVA 13% Ventas",
                        "valor": utils.format_currency_amount(total_iva)
                    }]
                else:
                    tributos = [{
                        "codigo": "20",
                        "descripcion": "IVA 13% Ventas",
                        "valor": utils.format_currency_amount(total_iva)
                    }]

        # Determinar numPagoElectronico según tipo de documento
        num_pago_electronico = None if document_type == '03' else "N/A"
        
        # Construir objeto base de resumen
        resumen = {
            "totalNoSuj": utils.format_summary_amount(total_no_suj),
            "totalExenta": utils.format_summary_amount(total_exenta),
            "totalGravada": utils.format_summary_amount(total_gravada),
            "subTotalVentas": utils.format_summary_amount(sub_total_ventas),
            "descuNoSuj": 0.00,
            "descuExenta": 0.00,
            "descuGravada": 0.00,
            "porcentajeDescuento": 0.00,
            "totalDescu": 0.00,
            "tributos": tributos,  # null para consumidor final, requerido para contribuyentes
            "subTotal": utils.format_summary_amount(sub_total_ventas),
            "ivaRete1": utils.format_summary_amount(move.l10n_sv_retention_amount) if move.l10n_sv_retention_amount else 0.00,
            "reteRenta": 0.00,
            "montoTotalOperacion": utils.format_summary_amount(monto_total_operacion),
            "totalNoGravado": 0.00,
            "totalPagar": utils.format_summary_amount(total_a_pagar),
            "totalLetras": utils.number_to_words(total_a_pagar, move.currency_id.name),
            "saldoFavor": 0.00,
            "condicionOperacion": condicion_operacion,
            "pagos": pagos,
            "numPagoElectronico": num_pago_electronico  # null para CCF, "N/A" para otros
        }
        
        # Campos específicos según tipo de documento
        if document_type == '03':  # CCF
            resumen["ivaPerci1"] = 0.00  # IVA Percibido requerido para CCF
        else:
            resumen["totalIva"] = utils.format_summary_amount(total_iva)  # Para otros tipos de documento
            
        return resumen

    def _get_documento_relacionado(self, move):
        """Documento relacionado (para notas de crédito/débito)"""
        if move.l10n_sv_document_type_id and move.l10n_sv_document_type_id.code in ['05', '06']:  # Notas de crédito/débito
            if move.reversed_entry_id:
                related_move = move.reversed_entry_id
                return [{
                    "tipoDocumento": related_move.l10n_sv_document_type_id.code if related_move.l10n_sv_document_type_id else "01",
                    "tipoGeneracion": 1,
                    "numeroDocumento": related_move.l10n_sv_edi_numero_control,
                    "fechaEmision": self.env['l10n_sv.dte.utils'].format_date(related_move.invoice_date)
                }]
        return None

    def _populate_template(self, template, move):
        """Popula template oficial con datos de la factura"""
        utils = self.env['l10n_sv.dte.utils']
        
        # Crear copia profunda del template
        json_data = json.loads(json.dumps(template))
        
        # Poblar campos básicos de identificación
        json_data = self._populate_identificacion(json_data, move, utils)
        
        # Poblar emisor
        json_data = self._populate_emisor(json_data, move, utils)
        
        # Poblar receptor según tipo de documento
        json_data = self._populate_receptor(json_data, move, utils)
        
        # Poblar cuerpo del documento
        json_data = self._populate_cuerpo_documento(json_data, move, utils)
        
        # Poblar resumen
        json_data = self._populate_resumen(json_data, move, utils)
        
        # Poblar documentos relacionados si aplica
        json_data = self._populate_documento_relacionado(json_data, move, utils)
        
        # Poblar extension si aplica
        json_data = self._populate_extension(json_data, move, utils)
        
        return json_data
    
    def _populate_extension(self, json_data, move, utils):
        """Poblar extension si aplica"""
        if 'extension' in json_data and json_data['extension']:
            # Procesar placeholders en extension
            extension_data = json_data['extension']
            if isinstance(extension_data, dict):
                # Procesar cada campo de extension
                for key, value in extension_data.items():
                    if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                        # Para CCF, asignar valores por defecto según el campo
                        if key == 'nombEntrega':
                            extension_data[key] = move.user_id.name if move.user_id else "VENDEDOR"
                        elif key == 'docuEntrega':
                            # Usar DUI por defecto si no hay dato específico
                            extension_data[key] = "00000000-0"
                        elif key == 'nombRecibe':
                            extension_data[key] = move.partner_id.name if move.partner_id else "CLIENTE"
                        elif key == 'docuRecibe':
                            # Usar el NIT del receptor si existe
                            if move.partner_id and move.partner_id.vat:
                                extension_data[key] = move.partner_id.vat
                            else:
                                extension_data[key] = "00000000-0"
                        elif key == 'placaVehiculo':
                            # Placa por defecto si no se especifica
                            extension_data[key] = "P000000"
                        elif key == 'observaciones':
                            # Observaciones por defecto
                            extension_data[key] = move.narration or "Entrega en punto de venta"
                        else:
                            extension_data[key] = "N/A"
        return json_data
    
    def _process_placeholders(self, text, move, utils):
        """Procesar placeholders en texto"""
        if not text or not isinstance(text, str):
            return text
        
        # Procesar placeholders comunes
        if '{NUMERO_CONTROL}' in text:
            text = text.replace('{NUMERO_CONTROL}', move.name or '')
        if '{FECHA_EMISION}' in text:
            text = text.replace('{FECHA_EMISION}', move.invoice_date.strftime('%Y-%m-%d') if move.invoice_date else '')
        if '{PARTNER_NAME}' in text:
            text = text.replace('{PARTNER_NAME}', move.partner_id.name or '')
        
        return text
    
    def _populate_identificacion(self, json_data, move, utils):
        """Popula sección de identificación"""
        config = move.company_id.get_edi_configuration()
        now = utils.get_current_datetime_sv()
        
        identificacion = json_data.get('identificacion', {})
        
        # Reemplazar placeholders
        identificacion['ambiente'] = utils.get_ambiente_code(config.environment)
        identificacion['numeroControl'] = move.l10n_sv_edi_numero_control
        identificacion['codigoGeneracion'] = move.l10n_sv_edi_codigo_generacion or utils.generate_codigo_generacion()
        # Usar fecha de factura, o fecha actual si no está definida
        fecha_factura = move.invoice_date or now.date()
        identificacion['fecEmi'] = utils.format_date(fecha_factura)
        identificacion['horEmi'] = utils.format_time(now.time())
        
        json_data['identificacion'] = identificacion
        return json_data
    
    def _populate_emisor(self, json_data, move, utils):
        """Popula sección de emisor usando template"""
        company = move.company_id
        establishment = move.l10n_sv_establishment_id
        
        if not establishment:
            raise exceptions.UserError(_('La factura no tiene establecimiento asignado'))
        if not move.l10n_sv_point_of_sale_id:
            raise exceptions.UserError(_('La factura no tiene punto de venta asignado'))
        
        emisor = json_data.get('emisor', {})
        
        # Poblar datos del emisor
        emisor['nit'] = utils.format_nit(company.l10n_sv_nit or company.vat)
        emisor['nrc'] = company.partner_id.company_registry or ""
        emisor['nombre'] = utils.clean_text_for_json(company.name, 200)
        emisor['codActividad'] = company.l10n_sv_codigo_actividad or "01111"
        emisor['descActividad'] = utils.clean_text_for_json(company.l10n_sv_desc_actividad or "Actividad económica general", 150)
        emisor['nombreComercial'] = utils.clean_text_for_json(company.name, 150)
        
        # Dirección
        if 'direccion' in emisor:
            direccion = emisor['direccion']
            direccion['departamento'] = establishment.departamento_code or "06"
            direccion['municipio'] = establishment.municipio_code or "14"
            direccion['complemento'] = utils.clean_text_for_json(establishment.street or company.street or "", 200)
        
        emisor['telefono'] = company.phone or "25919000"
        emisor['correo'] = utils.clean_text_for_json(company.email or "", 100)
        emisor['codEstableMH'] = establishment.code.zfill(4)
        emisor['codEstable'] = establishment.code.zfill(4)
        emisor['codPuntoVentaMH'] = move.l10n_sv_point_of_sale_id.code.zfill(4)
        emisor['codPuntoVenta'] = move.l10n_sv_point_of_sale_id.code.zfill(4)
        
        json_data['emisor'] = emisor
        return json_data
    
    def _populate_receptor(self, json_data, move, utils):
        """Popula sección de receptor según tipo y template"""
        document_type = move.l10n_sv_document_type_id.code
        partner = move.partner_id
        fiscal_position = move.fiscal_position_id
        
        if document_type == '01':  # Factura
            if fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
                # Consumidor final con nombre real del partner
                json_data['receptor'] = {
                    "tipoDocumento": None,
                    "numDocumento": None,
                    "nrc": None,
                    "nombre": utils.clean_text_for_json(partner.name, 250),  # Nombre real
                    "codActividad": None,
                    "descActividad": None,
                    "direccion": None,
                    "telefono": None,
                    "correo": partner.email  # Solo email real del partner
                }
            else:
                json_data['receptor'] = self._get_receptor_contribuyente_data(partner, utils)
        elif document_type == '03':  # CCF
            json_data['receptor'] = self._get_receptor_ccf_data(partner, utils)
        elif document_type == '05':  # Nota de Crédito
            if fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
                json_data['receptor'] = {
                    "tipoDocumento": None,
                    "numDocumento": None,
                    "nrc": None,
                    "nombre": utils.clean_text_for_json(partner.name, 250),
                    "codActividad": None,
                    "descActividad": None,
                    "direccion": None,
                    "telefono": None,
                    "correo": partner.email
                }
            else:
                json_data['receptor'] = self._get_receptor_contribuyente_data(partner, utils)
        elif document_type == '06':  # Nota de Débito
            if fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
                json_data['receptor'] = {
                    "tipoDocumento": None,
                    "numDocumento": None,
                    "nrc": None,
                    "nombre": utils.clean_text_for_json(partner.name, 250),
                    "codActividad": None,
                    "descActividad": None,
                    "direccion": None,
                    "telefono": None,
                    "correo": partner.email
                }
            else:
                json_data['receptor'] = self._get_receptor_contribuyente_data(partner, utils)
        elif document_type == '11':  # Factura de Exportación
            json_data['receptor'] = self._get_receptor_exportacion_data(partner, move, utils)
        elif document_type == '14':  # Sujeto Excluido
            json_data['sujetoExcluido'] = self._get_sujeto_excluido_data(partner, utils)
        
        return json_data
    
    def _get_receptor_exportacion_data(self, partner, move, utils):
        """Datos del receptor para exportación (11) - datos reales del partner"""
        # Verificar si es obligatorio según monto >= $10,000
        monto_total = move.amount_total
        if monto_total < 10000.00:
            return None  # Receptor opcional para exportaciones < $10,000
        
        # Para exportaciones >= $10,000, receptor obligatorio con datos reales
        return {
            "tipoPersona": 1,  # Persona Natural/Jurídica
            "codPais": partner.country_id.code if partner.country_id else None,
            "nombrePais": partner.country_id.name if partner.country_id else None,
            "complemento": utils.clean_text_for_json(partner.street, 200) if partner.street else None,
            "telefono": partner.phone,
            "correo": partner.email
        }
    
    def _get_sujeto_excluido_data(self, partner, utils):
        """Datos para sujeto excluido (14) - datos reales del partner"""
        departamento = "06"  # Por defecto San Salvador
        municipio = "14"     # Por defecto San Salvador
        if partner.city_id and hasattr(partner.city_id, 'district_code'):
            if partner.city_id.district_code and len(partner.city_id.district_code) == 4:
                departamento = partner.city_id.district_code[:2]
                municipio = partner.city_id.district_code[2:]
        
        return {
            "tipoDocumento": partner.l10n_sv_document_type_code,
            "numDocumento": partner.vat,
            "nombre": utils.clean_text_for_json(partner.name, 250),
            "codActividad": partner.industry_id.code if partner.industry_id else None,
            "descActividad": utils.clean_text_for_json(
                partner.industry_id.name, 150
            ) if partner.industry_id else None,
            "direccion": {
                "departamento": departamento,
                "municipio": municipio,
                "complemento": utils.clean_text_for_json(partner.street, 200) if partner.street else None
            },
            "telefono": partner.phone,
            "correo": partner.email
        }
    
    def _get_receptor_contribuyente_data(self, partner, utils):
        """Datos completos del receptor contribuyente"""
        doc_type = partner.l10n_sv_document_type_code or "36"
        if doc_type == "36":
            num_documento = utils.format_nit(partner.vat)
        elif doc_type == "13":
            num_documento = utils.format_dui(partner.vat)
        else:
            num_documento = partner.vat or ""
        
        departamento = "06"
        municipio = "14"
        if partner.city_id and hasattr(partner.city_id, 'district_code'):
            if partner.city_id.district_code and len(partner.city_id.district_code) == 4:
                departamento = partner.city_id.district_code[:2]
                municipio = partner.city_id.district_code[2:]
        
        return {
            "tipoDocumento": doc_type,
            "numDocumento": num_documento,
            "nrc": partner.company_registry if partner.company_registry else None,
            "nombre": utils.clean_text_for_json(partner.name, 250),
            "codActividad": partner.industry_id.code if partner.industry_id else None,
            "descActividad": utils.clean_text_for_json(
                partner.industry_id.name if partner.industry_id else "Actividad general", 150
            ),
            "direccion": {
                "departamento": departamento,
                "municipio": municipio,
                "complemento": utils.clean_text_for_json(partner.street or "Ciudad", 200)
            },
            "telefono": partner.phone,
            "correo": partner.email
        }
    
    def _get_receptor_ccf_data(self, partner, utils):
        """Datos específicos para receptor CCF"""
        if not partner.vat:
            raise exceptions.UserError(_(
                'CCF requiere un cliente con NIT válido. '
                'No se puede emitir CCF a consumidor final.'
            ))
        
        departamento = "06"
        municipio = "14"
        if partner.city_id and hasattr(partner.city_id, 'district_code'):
            if partner.city_id.district_code and len(partner.city_id.district_code) == 4:
                departamento = partner.city_id.district_code[:2]
                municipio = partner.city_id.district_code[2:]
        
        return {
            "nit": utils.format_nit(partner.vat),  # REQUERIDO para CCF v3
            "nrc": partner.company_registry if partner.company_registry else "0000000",
            "nombre": utils.clean_text_for_json(partner.name, 250),
            "codActividad": partner.industry_id.code if partner.industry_id else "47739",
            "descActividad": utils.clean_text_for_json(
                partner.industry_id.name if partner.industry_id else "Actividad general", 150
            ),
            "nombreComercial": utils.clean_text_for_json(  # REQUERIDO para CCF v3
                partner.commercial_name if hasattr(partner, 'commercial_name') and partner.commercial_name else partner.name, 
                150
            ),
            "direccion": {
                "departamento": departamento,
                "municipio": municipio,
                "complemento": utils.clean_text_for_json(partner.street or "Ciudad", 200)
            },
            "telefono": partner.phone or "0000-0000",
            "correo": partner.email or "cliente@empresa.com"
            # REMOVIDOS tipoDocumento y numDocumento - PROHIBIDOS en CCF v3
        }
    
    def _get_sujeto_excluido_data(self, partner, utils):
        """Datos para sujeto excluido"""
        departamento = "06"
        municipio = "14"
        if partner.city_id and hasattr(partner.city_id, 'district_code'):
            if partner.city_id.district_code and len(partner.city_id.district_code) == 4:
                departamento = partner.city_id.district_code[:2]
                municipio = partner.city_id.district_code[2:]
        
        return {
            "tipoDocumento": partner.l10n_sv_document_type_code,
            "numDocumento": partner.vat,
            "nombre": utils.clean_text_for_json(partner.name, 250),
            "codActividad": partner.industry_id.code if partner.industry_id else None,
            "descActividad": utils.clean_text_for_json(
                partner.industry_id.name, 150
            ) if partner.industry_id else None,
            "direccion": {
                "departamento": departamento,
                "municipio": municipio,
                "complemento": utils.clean_text_for_json(partner.street, 200) if partner.street else None
            },
            "telefono": partner.phone,
            "correo": partner.email
        }
    
    def _populate_cuerpo_documento(self, json_data, move, utils):
        """Popula líneas del documento usando template"""
        document_type = move.l10n_sv_document_type_id.code
        fiscal_position = move.fiscal_position_id
        cuerpo = []
        
        item_num = 1
        for line in move.invoice_line_ids:
            if line.display_type in ('line_section', 'line_note'):
                continue
            
            # Validar que la línea tenga cantidad válida
            if not line.quantity or line.quantity <= 0:
                _logger.warning(f"Línea con cantidad inválida: {line.quantity}, saltando...")
                continue
            
            # Datos básicos del item
            uom_code = 99
            if line.product_uom_id and hasattr(line.product_uom_id, 'code'):
                uom_code = line.product_uom_id.code or 99
            
            tipo_item = int(line.l10n_sv_item_type) if hasattr(line, 'l10n_sv_item_type') and line.l10n_sv_item_type else 1
            precio_unitario = utils.format_currency_amount(line.price_unit) if line.price_unit else 0.00
            cantidad = utils.format_currency_amount(line.quantity) if line.quantity else 1.00
            
            # Calcular descuento
            monto_descu = 0.00
            if line.discount:
                monto_descu = utils.format_currency_amount(line.price_unit * line.quantity * line.discount / 100)
            
            # Clasificar venta y calcular IVA según tipo de documento
            venta_no_suj = 0.00
            venta_exenta = 0.00
            venta_gravada = 0.00
            
            tributos = self._get_tributos_item(line, move)
            
            # Lógica específica por tipo de documento
            if document_type == '03':  # CCF
                if tributos and '20' in tributos:
                    venta_gravada = utils.format_currency_amount(line.price_subtotal)
                    tributos = ["20"]  # CCF: tributos debe ser lista con código IVA
                    iva_item = utils.format_currency_amount(venta_gravada * 13 / 113)
                elif tributos and 'C3' in tributos:
                    venta_exenta = utils.format_currency_amount(line.price_subtotal)
                    iva_item = 0.00
                    tributos = ["20"]  # CCF: tributos debe ser lista con código IVA
                else:
                    # Para CCF sin tributos específicos, asumir gravado con IVA
                    venta_gravada = utils.format_currency_amount(line.price_subtotal)
                    tributos = ["20"]  # CCF: tributos debe ser lista con código IVA
                    iva_item = utils.format_currency_amount(venta_gravada * 13 / 113)
                cod_tributo = None
            elif document_type == '11':  # Exportación
                # Para exportación, generalmente exenta de IVA
                venta_exenta = utils.format_currency_amount(line.price_subtotal)
                tributos = ["C3"] if tributos and 'C3' in tributos else None
                cod_tributo = "C3"
                iva_item = 0.00
            elif document_type == '14':  # Sujeto Excluido
                # Estructura simplificada para sujeto excluido
                venta_gravada = utils.format_currency_amount(line.price_subtotal)
                tributos = None
                cod_tributo = None
                iva_item = 0.00
            elif fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
                # Consumidor final
                venta_gravada = utils.format_currency_amount(line.price_subtotal)
                # Calcular IVA con precisión: por unidad y luego multiplicar
                iva_por_unidad = utils.format_currency_amount(line.price_unit * 0.13, 8)
                iva_item = utils.format_currency_amount(iva_por_unidad * line.quantity, 8)
                cod_tributo = None
                tributos = None
            else:
                # Contribuyente normal (01, 05, 06)
                if tributos and '20' in tributos:
                    venta_gravada = utils.format_currency_amount(line.price_subtotal)
                    iva_item = utils.format_currency_amount(venta_gravada * 13 / 113)
                    cod_tributo = "20"
                elif tributos and 'C3' in tributos:
                    venta_exenta = utils.format_currency_amount(line.price_subtotal)
                    iva_item = 0.00
                    cod_tributo = "C3"
                else:
                    # Para Factura 01: verificar si hay venta gravada
                    if document_type == '01' and line.price_subtotal > 0:
                        # Verificar si la línea tiene impuestos IVA
                        has_iva = False
                        for tax in line.tax_ids:
                            if tax.amount == 13:  # IVA 13%
                                has_iva = True
                                break
                        
                        if has_iva:
                            venta_gravada = utils.format_currency_amount(line.price_subtotal)
                            tributos = ['20']  # Asignar IVA
                            iva_item = utils.format_currency_amount(venta_gravada * 0.13)
                            cod_tributo = None  # codTributo siempre null para Factura
                        else:
                            venta_no_suj = utils.format_currency_amount(line.price_subtotal)
                            iva_item = 0.00
                            cod_tributo = None
                    else:
                        venta_no_suj = utils.format_currency_amount(line.price_subtotal)
                        iva_item = 0.00
                        cod_tributo = None
            
            # Construir item según tipo de documento
            if document_type == '14':  # Sujeto Excluido - estructura simplificada
                item = {
                    "numItem": item_num,
                    "tipoItem": tipo_item,
                    "cantidad": cantidad,
                    "codigo": utils.clean_text_for_json(line.product_id.default_code or f"PROD-{item_num:03d}", 25),
                    "uniMedida": uom_code,
                    "descripcion": utils.clean_text_for_json(line.name or line.product_id.name or "Producto", 1000),
                    "precioUni": precio_unitario,
                    "montoDescu": monto_descu,
                    "compra": utils.format_currency_amount(line.price_subtotal)
                }
            else:  # Otros tipos de documento
                item = {
                    "numItem": item_num,
                    "tipoItem": tipo_item,
                    "numeroDocumento": None,
                    "cantidad": cantidad,
                    "codigo": utils.clean_text_for_json(line.product_id.default_code or f"PROD-{item_num:03d}", 25),
                    "codTributo": cod_tributo,
                    "uniMedida": uom_code,
                    "descripcion": utils.clean_text_for_json(line.name or line.product_id.name or "Producto", 1000),
                    "precioUni": precio_unitario,
                    "montoDescu": monto_descu,
                    "ventaNoSuj": venta_no_suj,
                    "ventaExenta": venta_exenta,
                    "ventaGravada": venta_gravada,
                    "tributos": tributos,
                    "psv": 0.00,
                    "noGravado": 0.00
                }
                
                # Agregar campos específicos por tipo
                if document_type in ['01', '05', '06']:  # Requieren ivaItem (NO CCF)
                    item["ivaItem"] = iva_item
                elif document_type == '11':  # Exportación
                    item["tipoItemExpor"] = 1  # Tipo de item de exportación
            
            cuerpo.append(item)
            item_num += 1
        
        json_data['cuerpoDocumento'] = cuerpo
        return json_data
    
    def _populate_resumen(self, json_data, move, utils):
        """Popula sección de resumen usando template"""
        document_type = move.l10n_sv_document_type_id.code
        fiscal_position = move.fiscal_position_id
        
        # Calcular totales desde las líneas
        total_no_suj = 0.00
        total_exenta = 0.00
        total_gravada = 0.00
        total_iva = 0.00
        
        for line in move.invoice_line_ids:
            if line.display_type in ('line_section', 'line_note'):
                continue
            
            tributos = self._get_tributos_item(line, move)
            
            # Lógica específica por tipo de documento para totales
            if document_type == '11':  # Exportación
                total_exenta += line.price_subtotal  # Exportaciones generalmente exentas
            elif document_type == '14':  # Sujeto Excluido
                total_gravada += line.price_subtotal  # Se maneja como compra total
            elif fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
                # Para consumidor final: precio SIN IVA, hay que calcular IVA
                base_gravada = line.price_subtotal  # Base sin IVA
                iva_linea = base_gravada * 0.13     # IVA = base × 13%
                
                total_gravada += base_gravada  # Base sin IVA
                total_iva += iva_linea  # IVA calculado
            elif tributos and '20' in tributos:
                total_gravada += line.price_subtotal
                total_iva += (line.price_subtotal * 0.13)
            elif tributos and 'C3' in tributos:
                total_exenta += line.price_subtotal
            else:
                # Para Factura 01: verificar si hay IVA aunque no tenga tributos específicos
                if document_type == '01':
                    has_iva = False
                    for tax in line.tax_ids:
                        if tax.amount == 13:  # IVA 13%
                            has_iva = True
                            break
                    
                    if has_iva:
                        total_gravada += line.price_subtotal
                        total_iva += (line.price_subtotal * 0.13)
                    else:
                        total_no_suj += line.price_subtotal
                else:
                    total_no_suj += line.price_subtotal
        
        # Formatear valores
        total_no_suj = utils.format_currency_amount(total_no_suj)
        total_exenta = utils.format_currency_amount(total_exenta)
        total_gravada = utils.format_currency_amount(total_gravada)
        total_iva = utils.format_currency_amount(total_iva)
        
        sub_total_ventas = total_no_suj + total_exenta + total_gravada
        
        # Condición de operación
        condicion_operacion = 1  # Contado
        if move.invoice_payment_term_id and move.invoice_payment_term_id.line_ids:
            if any(line.nb_days > 0 for line in move.invoice_payment_term_id.line_ids):
                condicion_operacion = 2  # Crédito
        
        # Tributos en resumen
        tributos = None
        if document_type == '03':  # CCF siempre debe tener tributos si hay IVA
            if total_iva > 0:
                tributos = [{
                    "codigo": "20",
                    "descripcion": "IVA 13% Ventas",
                    "valor": total_iva
                }]
        elif fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
            tributos = None
        elif total_iva > 0:
            tributos = [{
                "codigo": "20",
                "descripcion": "IVA 13% Ventas",
                "valor": total_iva
            }]
        
        # Pagos
        pagos = None
        if document_type != '03':  # No para CCF
            codigo_pago = "01"  # Billetes y monedas por defecto
            if move.journal_id and move.journal_id.type == 'bank':
                codigo_pago = "05"  # Transferencia bancaria
            
            pagos = [{
                "codigo": codigo_pago,
                "montoPago": utils.format_currency_amount(sub_total_ventas + total_iva),
                "referencia": None,
                "plazo": "01",
                "periodo": None
            }]
        
        # Poblar resumen
        resumen = json_data.get('resumen', {})
        resumen.update({
            "totalNoSuj": total_no_suj,
            "totalExenta": total_exenta,
            "totalGravada": total_gravada,
            "subTotalVentas": utils.format_currency_amount(sub_total_ventas),
            "tributos": tributos,
            "subTotal": utils.format_currency_amount(sub_total_ventas),
            "ivaRete1": 0.00,
            "montoTotalOperacion": utils.format_currency_amount(sub_total_ventas + total_iva),
            "totalPagar": utils.format_currency_amount(sub_total_ventas + total_iva),
            "totalLetras": utils.number_to_words(sub_total_ventas + total_iva, move.currency_id.name),
            "condicionOperacion": condicion_operacion,
            "pagos": pagos,
            "numPagoElectronico": "N/A" if document_type != '03' else None
        })
        
        # Lógica específica por tipo de documento
        if document_type == '03':  # CCF
            # CCF según esquema oficial MH v3
            # Agregar ivaPerci1 (requerido) y remover totalIva (prohibido)
            resumen["ivaPerci1"] = 0.00
            resumen.pop("totalIva", None)  # Remover totalIva si existe
            
            # Si es contado, debe incluir al menos un pago
            if condicion_operacion == 1:  # Contado
                resumen["pagos"] = [{
                    "codigo": "01",  # 01 = Efectivo
                    "montoPago": utils.format_currency_amount(sub_total_ventas + total_iva),
                    "referencia": "PAGO CONTADO",
                    "plazo": None,
                    "periodo": None
                }]
            else:
                resumen["pagos"] = []  # Crédito puede ir vacío
            resumen["numPagoElectronico"] = None
        else:
            # Para otros tipos de documento (no CCF), agregar totalIva
            resumen["totalIva"] = total_iva
            
        if document_type in ['05', '06']:  # Notas de Crédito/Débito
            if document_type == '05':  # Nota de Crédito
                resumen["pagos"] = None
                resumen["numPagoElectronico"] = None
            else:  # Nota de Débito (06)
                resumen["numPagoElectronico"] = "N/A"
        elif document_type == '11':  # Exportación
            # Campos específicos de exportación
            resumen.update({
                "seguro": 0.00,  # Valor del seguro
                "flete": 0.00,   # Valor del flete
                "codIncoterms": move.l10n_sv_incoterm_code if hasattr(move, 'l10n_sv_incoterm_code') else None,
                "descIncoterms": move.invoice_incoterm_id.name if move.invoice_incoterm_id else None,
                "observaciones": None
            })
            # Remover campos no aplicables para exportación
            campos_no_aplicables = ['tributos', 'ivaRete1', 'pagos', 'numPagoElectronico', 'condicionOperacion']
            for campo in campos_no_aplicables:
                resumen.pop(campo, None)
        elif document_type == '14':  # Sujeto Excluido
            # Estructura simplificada para sujeto excluido
            resumen = {
                "totalCompra": utils.format_currency_amount(sub_total_ventas + total_iva),
                "descu": 0.00,
                "totalDescu": 0.00,
                "totalPagar": utils.format_currency_amount(sub_total_ventas + total_iva),
                "totalLetras": utils.number_to_words(sub_total_ventas + total_iva, move.currency_id.name),
                "condicionOperacion": condicion_operacion
            }
        
        json_data['resumen'] = resumen
        return json_data
    
    def _populate_documento_relacionado(self, json_data, move, utils):
        """Popula documentos relacionados para notas"""
        document_type = move.l10n_sv_document_type_id.code
        
        if document_type in ['05', '06']:  # Notas de Crédito/Débito
            if move.reversed_entry_id:
                related_move = move.reversed_entry_id
                json_data['documentoRelacionado'] = [{
                    "tipoDocumento": related_move.l10n_sv_document_type_id.code if related_move.l10n_sv_document_type_id else "01",
                    "tipoGeneracion": 1,
                    "numeroDocumento": related_move.l10n_sv_edi_numero_control,
                    "fechaEmision": utils.format_date(related_move.invoice_date)
                }]
            else:
                # Si no hay documento relacionado, es requerido para notas
                raise exceptions.UserError(_(
                    f"{'Nota de Crédito' if document_type == '05' else 'Nota de Débito'} requiere un documento relacionado"
                ))
        else:
            # Para otros tipos, documentoRelacionado es null
            json_data['documentoRelacionado'] = None
        
        return json_data
    
    def _format_nit_receptor(self, nit_string):
        """Formatea NIT para receptor según especificaciones MH - 14 dígitos sin guiones"""
        if not nit_string:
            return ""
        # Remover caracteres no numéricos
        digits = re.sub(r'\D', '', nit_string)
        # NIT debe ser 14 dígitos sin guiones
        if len(digits) >= 14:
            return digits[:14]  # Tomar exactamente 14 dígitos
        elif len(digits) >= 9:
            return digits.zfill(14)  # Rellenar con ceros hasta 14
        return digits.zfill(14)
    
    def _generate_factura_json(self, move):
        """Genera JSON específico para Factura (01) - FALLBACK"""
        return self._get_base_json_structure(move)

    def _generate_ccf_json(self, move):
        """Genera JSON específico para CCF (03)"""
        json_data = self._get_base_json_structure(move)
        
        # CCF requiere version 3 según esquema oficial
        json_data["identificacion"]["version"] = 3
        
        # Log para depuración
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"CCF JSON version: {json_data['identificacion']['version']}")
        _logger.info(f"CCF JSON tipoDte: {json_data['identificacion']['tipoDte']}")
        _logger.info(f"CCF JSON numeroControl: {json_data['identificacion']['numeroControl']}")
        
        # CCF no debe incluir ivaPerci1 según esquema oficial MH
        if "resumen" in json_data:
            # No agregar ivaPerci1 para CCF según validación del esquema
            pass
        
        # La extensión ya viene correctamente formateada desde _get_base_json_structure
        # No es necesario volver a asignarla
        
        return json_data

    def _generate_nota_credito_json(self, move):
        """Genera JSON específico para Nota de Crédito (05)"""
        json_data = self._get_base_json_structure(move)
        # Agregar lógica específica para notas de crédito
        return json_data

    def _generate_exportacion_json(self, move):
        """Genera JSON específico para Factura de Exportación (11)"""
        json_data = self._get_base_json_structure(move)
        
        # Agregar información específica de exportación
        if move.invoice_incoterm_id:
            json_data["receptor"]["complemento"] = {
                "incoterms": move.l10n_sv_incoterm_code,
                "descIncoterms": move.invoice_incoterm_id.name
            }
        
        return json_data

    def _generate_nota_remision_json(self, move):
        """Genera JSON específico para Nota de Remisión (04)"""
        json_data = self._get_base_json_structure(move)
        
        # Nota de Remisión requiere version 3 según esquema oficial
        json_data["identificacion"]["version"] = 3
        
        # Log para depuración
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"Nota de Remisión JSON version: {json_data['identificacion']['version']}")
        _logger.info(f"Nota de Remisión JSON tipoDte: {json_data['identificacion']['tipoDte']}")
        _logger.info(f"Nota de Remisión JSON numeroControl: {json_data['identificacion']['numeroControl']}")
        
        # AJUSTES ESPECÍFICOS PARA NOTA DE REMISIÓN
        
        # 1. Eliminar campos prohibidos en raíz
        if "otrosDocumentos" in json_data:
            del json_data["otrosDocumentos"]
        
        # 2. Agregar campos requeridos al receptor
        if "receptor" in json_data:
            # Agregar nombreComercial si no existe
            if "nombreComercial" not in json_data["receptor"] or not json_data["receptor"]["nombreComercial"]:
                json_data["receptor"]["nombreComercial"] = json_data["receptor"].get("nombre", "Receptor")
            
            # Agregar bienTitulo (REQUERIDO para Nota de Remisión)
            json_data["receptor"]["bienTitulo"] = "01"  # Código para "Venta"
            
            # Asegurar numDocumento válido
            if "numDocumento" in json_data["receptor"] and not json_data["receptor"]["numDocumento"]:
                json_data["receptor"]["numDocumento"] = "000000000"
        
        # 3. Limpiar resumen - quitar campos prohibidos
        if "resumen" in json_data:
            prohibited_resumen_fields = [
                "totalIva", "ivaRete1", "reteRenta", "pagos", "numPagoElectronico",
                "totalNoGravado", "saldoFavor", "totalPagar", "condicionOperacion"
            ]
            for field in prohibited_resumen_fields:
                if field in json_data["resumen"]:
                    del json_data["resumen"][field]
        
        # 4. Limpiar cuerpoDocumento - quitar campos prohibidos
        if "cuerpoDocumento" in json_data:
            for item in json_data["cuerpoDocumento"]:
                prohibited_item_fields = ["noGravado", "psv"]
                for field in prohibited_item_fields:
                    if field in item:
                        del item[field]
        
        # 5. Limpiar extension - quitar campos prohibidos
        if "extension" in json_data:
            if "placaVehiculo" in json_data["extension"]:
                del json_data["extension"]["placaVehiculo"]
            
            # Solo mantener campos permitidos en extension para NR
            allowed_extension_fields = ["nombEntrega", "docuEntrega", "nombRecibe", "docuRecibe", "observaciones"]
            extension_copy = {}
            for field in allowed_extension_fields:
                if field in json_data["extension"]:
                    extension_copy[field] = json_data["extension"][field]
            json_data["extension"] = extension_copy
        
        return json_data

    def _generate_generic_json(self, move):
        """Genera JSON genérico para otros tipos de documentos"""
        return self._get_base_json_structure(move)

    def validate_json(self, json_data, move):
        """Valida el JSON generado"""
        utils = self.env['l10n_sv.dte.utils']
        document_type_code = move.l10n_sv_document_type_id.code if move.l10n_sv_document_type_id else "01"
        errors = utils.validate_json_structure(json_data, document_type_code)
        
        if errors:
            raise exceptions.ValidationError('\n'.join(errors))
        
        return True

    def _remove_null_values(self, obj, parent_key="", document_type="01"):
        """Remueve recursivamente campos con valor null del diccionario, excepto campos requeridos"""
        # Asegurar que document_type tenga un valor válido, preservando el tipo original
        if not document_type or document_type is None:
            document_type = "01"  # Valor por defecto solo si no se proporciona
            
        # Campos base que DEBEN mantenerse aunque sean null
        required_null_fields_base = {
            "documentoRelacionado", "apendice", "otrosDocumentos", 
            "ventaTercero", "tipoContingencia", "motivoContin", "referencia", 
            "plazo", "periodo", "nrc", "numeroDocumento"
        }
        
        # Campos específicos por tipo de documento que deben mantenerse null
        required_null_fields = required_null_fields_base.copy()
        
        if document_type == "01":  # Factura
            required_null_fields.update({"codTributo", "extension"})
        elif document_type == "03":  # CCF
            required_null_fields.update({"tipoDocumento", "numDocumento", "codTributo"})
        
        # Si es un diccionario
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if value is None and key not in required_null_fields:
                    continue  # Omitir campos null no requeridos
                elif isinstance(value, (dict, list)):
                    cleaned_value = self._remove_null_values(value, key, document_type)
                    if cleaned_value is not None or key in required_null_fields:
                        result[key] = cleaned_value
                else:
                    result[key] = value
            return result
        
        # Si es una lista
        elif isinstance(obj, list):
            return [self._remove_null_values(item, parent_key, document_type) for item in obj if item is not None]
        
        # Para otros tipos, retornar el valor tal cual
        return obj

    def _get_tributos_item(self, line, move):
        """Determinar tributos a nivel de línea según producto y posición fiscal"""
        fiscal_position = move.fiscal_position_id
        
        # Para consumidor final, siempre retornar null
        if fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
            return None
        
        # Verificar si la línea tiene impuestos
        if not line.tax_ids:
            return None
        
        # Buscar IVA en los impuestos de la línea
        for tax in line.tax_ids:
            if hasattr(tax, 'code_dgii') and tax.code_dgii == '20':
                return ['20']  # IVA
            elif hasattr(tax, 'code_dgii') and tax.code_dgii in ['C3', 'E0']:
                return [tax.code_dgii]
            # Fallback: verificar por porcentaje de IVA
            elif tax.amount == 13:  # IVA 13%
                return ['20']
        
        return None

    def format_json_output(self, json_data, document_type_code):
        """Formatear JSON para salida - convierte a string JSON"""
        # Por ahora, simplemente retornar el JSON como string
        # El document_type_code puede usarse para limpieza específica por tipo
        # Tipos: 01=Factura, 03=CCF, 05=NC, 06=ND, 11=Exportación, 14=Sujeto Excluido
        import json
        return json.dumps(json_data, ensure_ascii=False, indent=2)

    def _get_tributos_resumen(self, move):
        """Determinar tributos del resumen según posición fiscal - LÓGICA VALIDADA"""
        fiscal_position = move.fiscal_position_id
        utils = self.env['l10n_sv.dte.utils']
        
        # Calcular IVA primero
        iva_amount = 0.00
        for tax_line in move.line_ids.filtered(lambda l: l.tax_line_id):
            if hasattr(tax_line.tax_line_id, 'code_dgii') and tax_line.tax_line_id.code_dgii == '20':
                iva_amount += abs(tax_line.balance)
        
        # Para consumidor final, siempre retornar null según LOGICA_VALIDADA.md
        if fiscal_position and fiscal_position.l10n_sv_is_final_consumer:
            return None  # null para consumidor final validado exitosamente
        
        # Para contribuyentes, calcular tributos normalmente
        tributos = []
        if iva_amount > 0:
            tributos.append({
                "codigo": "20",
                "descripcion": "IVA 13% Ventas",
                "valor": utils.format_currency_amount(iva_amount)
            })
        
        return tributos

    def _get_receptor_exportacion(self, partner, move):
        """Receptor para operaciones de exportación"""
        utils = self.env['l10n_sv.dte.utils']
        
        # Verificar si es obligatorio según monto
        monto_total = move.amount_total
        if monto_total < 10000.00:  # USD según esquema fe-fex-v1.json
            return None  # Receptor opcional
        
        return {
            "tipoPersona": 1,  # Persona Natural/Jurídica
            "codPais": partner.country_id.code if partner.country_id else "US",
            "nombrePais": partner.country_id.name if partner.country_id else "Estados Unidos",
            "complemento": utils.clean_text_for_json(partner.street or "", 200),
            "telefono": partner.phone or "0000-0000",
            "correo": utils.clean_text_for_json(partner.email or "", 100)
        }

    def _get_sujeto_excluido_data(self, partner, move):
        """Datos del sujeto excluido para factura tipo 14"""
        utils = self.env['l10n_sv.dte.utils']
        
        return {
            "tipoDocumento": partner.l10n_sv_document_type_code or "13",
            "numDocumento": partner.vat or "",
            "nombre": utils.clean_text_for_json(partner.name, 200),
            "codActividad": partner.industry_id.code if partner.industry_id else None,
            "descActividad": utils.clean_text_for_json(
                partner.industry_id.name if partner.industry_id else "Actividad general", 150
            ),
            "telefono": partner.phone or "0000-0000",
            "correo": utils.clean_text_for_json(partner.email or "", 100)
        }

    # NOTA: Este método ya no se usa, el número de control se genera en account_move._generate_dte_identifiers()
    # def _generate_numero_control(self, move):
    #     """
    #     Generar número de control según especificación oficial MH El Salvador
    #     Estructura: DTE-XX-XXXXXXXX-XXXXXXXXXXXXXXX (31 caracteres total)
    #     """
    #     company = move.company_id
    #     sequence_number = getattr(move, 'l10n_sv_sequence_number', 1) or 1
    #     
    #     # 1. Primera sección: "DTE"
    #     prefix = "DTE"
    #     
    #     # 2. Segunda sección: Código de tipo de documento (2 dígitos)
    #     document_type = move.l10n_sv_document_type_id.code if move.l10n_sv_document_type_id else "01"
    #     document_type = document_type.zfill(2)  # Asegurar 2 dígitos
    #     
    #     # 3. Tercera sección: 8 dígitos (4 establecimiento + 4 punto de venta)
    #     # Código de establecimiento (4 dígitos)
    #     establishment_code = "0001"  # Por defecto
    #     if move.l10n_sv_establishment_id and move.l10n_sv_establishment_id.code:
    #         establishment_code = move.l10n_sv_establishment_id.code.zfill(4)
    #     
    #     # Código de punto de venta (4 dígitos)  
    #     point_of_sale_code = "0001"  # Por defecto
    #     if move.l10n_sv_point_of_sale_id and move.l10n_sv_point_of_sale_id.code:
    #         point_of_sale_code = move.l10n_sv_point_of_sale_id.code.zfill(4)
    #     
    #     # Combinar establecimiento + punto de venta (8 dígitos total)
    #     establishment_pos = f"{establishment_code}{point_of_sale_code}"
    #     
    #     # 4. Cuarta sección: Secuencial anual (15 dígitos)
    #     secuencial = f"{sequence_number:015d}"
    #     
    #     # Construir número de control completo
    #     numero_control = f"{prefix}-{document_type}-{establishment_pos}-{secuencial}"
    #     
    #     # Validar longitud exacta de 31 caracteres
    #     if len(numero_control) != 31:
    #         _logger.error(f"Número de control generado tiene {len(numero_control)} caracteres, esperados 31: {numero_control}")
    #         
    #     return numero_control

    def validate_json_against_schema(self, json_data, document_type):
        """Validar JSON contra esquema oficial correspondiente"""
        schema_file = self.DTE_RULES.get(document_type, {}).get('schema_file')
        if not schema_file:
            _logger.warning(f"No hay esquema definido para tipo de documento {document_type}")
            return True
        
        schema_path = f"/home/luis/Documentos/Dockers/Odoo18/svfe-json-schemas/svfe-json-schemas/{schema_file}"
        
        try:
            import jsonschema
            import os
            
            if not os.path.exists(schema_path):
                _logger.warning(f"Esquema no encontrado: {schema_path}")
                return True
                
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            jsonschema.validate(json_data, schema)
            _logger.info(f"JSON validado exitosamente contra esquema {schema_file}")
            return True
        except Exception as e:
            _logger.error(f"Validación de esquema falló para {document_type}: {e}")
            return False