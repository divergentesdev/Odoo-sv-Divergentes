import re
import uuid
from datetime import datetime
from odoo import models, fields, api, exceptions, _


class DteUtils(models.AbstractModel):
    """Utilidades para generación de DTE"""
    _name = 'l10n_sv.dte.utils'
    _description = 'Utilidades DTE El Salvador'

    @api.model
    def number_to_words(self, amount, currency='USD'):
        """Convierte un número a palabras según formato del MH"""
        
        # Separar parte entera y decimal
        amount_str = f"{amount:.2f}"
        integer_part, decimal_part = amount_str.split('.')
        integer_part = int(integer_part)
        decimal_part = int(decimal_part)
        
        # Diccionarios para conversión
        units = ['', 'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
        teens = ['DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 
                'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE']
        tens = ['', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 
               'SETENTA', 'OCHENTA', 'NOVENTA']
        hundreds = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 
                   'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS']
        
        def convert_hundreds(n):
            """Convierte números de 0-999 a palabras"""
            if n == 0:
                return ''
            elif n == 100:
                return 'CIEN'
            elif n < 10:
                return units[n]
            elif n < 20:
                return teens[n - 10]
            elif n < 100:
                if n % 10 == 0:
                    return tens[n // 10]
                else:
                    return tens[n // 10] + ' Y ' + units[n % 10]
            else:
                hundred = n // 100
                remainder = n % 100
                result = hundreds[hundred]
                if remainder > 0:
                    if remainder < 10:
                        result += ' ' + units[remainder]
                    elif remainder < 20:
                        result += ' ' + teens[remainder - 10]
                    else:
                        if remainder % 10 == 0:
                            result += ' ' + tens[remainder // 10]
                        else:
                            result += ' ' + tens[remainder // 10] + ' Y ' + units[remainder % 10]
                return result
        
        def convert_thousands(n):
            """Convierte números con miles"""
            if n < 1000:
                return convert_hundreds(n)
            elif n < 1000000:
                thousands = n // 1000
                remainder = n % 1000
                
                if thousands == 1:
                    result = 'MIL'
                else:
                    result = convert_hundreds(thousands) + ' MIL'
                
                if remainder > 0:
                    result += ' ' + convert_hundreds(remainder)
                return result
            else:
                millions = n // 1000000
                remainder = n % 1000000
                
                if millions == 1:
                    result = 'UN MILLÓN'
                else:
                    result = convert_hundreds(millions) + ' MILLONES'
                
                if remainder > 0:
                    result += ' ' + convert_thousands(remainder)
                return result
        
        # Convertir parte entera
        if integer_part == 0:
            words = 'CERO'
        else:
            words = convert_thousands(integer_part)
        
        # Agregar decimales y moneda
        if currency == 'USD':
            if decimal_part == 0:
                return f"{words} 00/100 DÓLARES"
            else:
                return f"{words} {decimal_part:02d}/100 DÓLARES"
        else:
            return f"{words}.{decimal_part:02d}"

    @api.model
    def generate_uuid(self):
        """Genera UUID para código de generación"""
        return str(uuid.uuid4()).upper()

    @api.model
    def format_date(self, date_value):
        """Formatea fecha para DTE (YYYY-MM-DD)"""
        if isinstance(date_value, str):
            # Si ya es string, verificar formato
            if len(date_value) == 10 and date_value[4] == '-' and date_value[7] == '-':
                return date_value
            # Intentar parsear y reformatear
            try:
                from datetime import datetime
                dt = datetime.strptime(date_value, '%d/%m/%Y')
                return dt.strftime('%Y-%m-%d')
            except:
                return date_value
        return date_value.strftime('%Y-%m-%d') if date_value else None

    @api.model
    def format_time(self, datetime_value):
        """Formatea hora para DTE (HH:MM:SS)"""
        if isinstance(datetime_value, str):
            return datetime_value
        return datetime_value.strftime('%H:%M:%S') if datetime_value else None

    @api.model
    def format_nit(self, nit):
        """Formatea NIT según especificaciones MH - 14 dígitos sin guiones"""
        if not nit:
            return None
        
        # Remover caracteres no numéricos
        digits_only = re.sub(r'\D', '', nit)
        
        # NIT debe tener 14 dígitos sin guiones
        if len(digits_only) >= 14:
            # Tomar solo los primeros 14 dígitos
            return digits_only[:14]
        elif len(digits_only) >= 9:
            # Si tiene al menos 9 dígitos, rellenar con ceros al inicio
            return digits_only.zfill(14)
        
        # Si tiene menos de 9 dígitos, no es válido
        return digits_only.zfill(14)

    @api.model
    def format_dui(self, dui):
        """Formatea DUI según especificaciones MH - 8 dígitos sin guiones"""
        if not dui:
            return None
        
        # Remover caracteres no numéricos
        digits_only = re.sub(r'\D', '', dui)
        
        # DUI debe tener exactamente 8 dígitos sin guiones
        if len(digits_only) >= 8:
            # Tomar solo los primeros 8 dígitos
            return digits_only[:8]
        
        # Si tiene menos de 8 dígitos, rellenar con ceros
        return digits_only.zfill(8)

    @api.model
    def validate_correlativo_format(self, numero_control):
        """Valida formato de número de control DTE"""
        # Formato correcto: DTE-##-[A-Z0-9]{8}-###############
        pattern = r'^DTE-\d{2}-[A-Z0-9]{8}-\d{15}$'
        return bool(re.match(pattern, numero_control)) if numero_control else False

    @api.model
    def get_tributo_description(self, codigo_tributo):
        """Obtiene descripción de tributo según código"""
        tributos = {
            '20': 'Impuesto al Valor Agregado 13%',
            'C3': 'Exportación',
            'D1': 'FOVIAL',
            'C8': 'COTRANS',
            '59': 'Turismo 5%',
            '22': 'Retención IVA 1%',
            'C4': 'Retención IVA 13%',
            'C9': 'Otras retenciones',
        }
        return tributos.get(codigo_tributo, f'Tributo {codigo_tributo}')

    @api.model
    def calculate_iva_amount(self, base_amount, rate=13.0):
        """Calcula monto de IVA"""
        return round(base_amount * (rate / 100), 2)

    @api.model
    def validate_json_structure(self, json_data, document_type):
        """Valida estructura básica del JSON DTE"""
        required_fields = [
            'identificacion',
            'emisor',
            'receptor',
            'cuerpoDocumento',
            'resumen'
        ]
        
        errors = []
        for field in required_fields:
            if field not in json_data:
                errors.append(f'Campo requerido faltante: {field}')
        
        # Validaciones específicas por tipo de documento
        if document_type == '11':  # Factura de Exportación
            if 'documentoRelacionado' not in json_data.get('receptor', {}):
                errors.append('Factura de exportación requiere información de documento relacionado')
        
        if document_type == '05':  # Nota de Crédito
            if not json_data.get('documentoRelacionado'):
                errors.append('Nota de crédito debe referenciar documento original')
        
        return errors

    @api.model
    def get_ambiente_code(self, environment):
        """Obtiene código de ambiente para DTE"""
        # Según el estándar del MH de El Salvador:
        # 00 = Certificación/Pruebas
        # 01 = Producción
        return '00' if environment == 'test' else '01'

    @api.model
    def get_tipo_modelo_code(self):
        """Obtiene código de tipo de modelo (siempre 1 para facturación normal)"""
        return 1

    @api.model
    def get_tipo_operacion_code(self, operation_type='1'):
        """Obtiene código de tipo de operación"""
        operaciones = {
            '1': 1,  # Venta
            '2': 2,  # Operaciones a cuenta de terceros  
            '3': 3,  # Otros
        }
        return operaciones.get(operation_type, 1)

    @api.model
    def format_currency_amount(self, amount, decimals=2):
        """Formatea montos monetarios para DTE
        Args:
            amount: Monto a formatear
            decimals: Número de decimales (2 para resumen, 8 para cuerpo)
        """
        return round(float(amount), decimals) if amount else 0.0
    
    @api.model
    def format_body_amount(self, amount):
        """Formatea montos para el cuerpo del documento (8 decimales)"""
        return self.format_currency_amount(amount, 8)
    
    @api.model
    def format_summary_amount(self, amount):
        """Formatea montos para el resumen (2 decimales)"""
        return self.format_currency_amount(amount, 2)

    @api.model
    def get_moneda_code(self, currency_code='USD'):
        """Obtiene código de moneda para DTE"""
        return currency_code or 'USD'

    @api.model
    def clean_text_for_json(self, text, max_length=None):
        """Limpia texto para JSON DTE"""
        if not text:
            return ''
        
        # Remover caracteres especiales problemáticos pero mantener @ para emails
        text = re.sub(r'[^\w\s\-.,()@áéíóúüñÁÉÍÓÚÜÑ]', '', text)
        
        # Normalizar espacios
        text = ' '.join(text.split())
        
        # Truncar si es necesario
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        return text.upper()

    @api.model
    def generate_codigo_generacion(self):
        """Genera código de generación único"""
        return self.generate_uuid()

    @api.model
    def get_current_datetime_sv(self):
        """Obtiene fecha y hora actual de El Salvador"""
        # El Salvador está en GMT-6
        now = fields.Datetime.now()
        return now

    @api.model
    def validate_establishment_code(self, code):
        """Valida código de establecimiento (4 dígitos)"""
        return bool(re.match(r'^\d{4}$', code)) if code else False

    @api.model
    def validate_pos_code(self, code):
        """Valida código de punto de venta (3 dígitos)"""
        return bool(re.match(r'^\d{3}$', code)) if code else False
    
    @api.model
    def validate_numero_control_format(self, numero_control):
        """Valida formato de número de control según MH"""
        pattern = r"^DTE-\d{2}-\d{8}-\d{15}$"
        return bool(re.match(pattern, numero_control))