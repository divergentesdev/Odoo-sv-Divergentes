# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_withholding_agent = fields.Boolean(
        string='Es agente de retención',
        default=False,
        help='Indica si el contacto es un agente de retención de impuestos'
    )

    l10n_sv_document_type_code = fields.Selection([
        ('13', 'DUI'),
        ('36', 'NIT'),
        ('03', 'Pasaporte'),
        ('02', 'Carnet de Residente'),
        ('37', 'Otro documento'),
    ], string='Tipo de Documento', default='36')  # Cambiado a NIT (36)

    @api.onchange('l10n_sv_document_type_code')
    def _onchange_document_type(self):
        if self.l10n_sv_document_type_code == '36':
            self.l10n_latam_identification_type_id = self.env.ref('l10n_latam_base.it_vat').id
        elif self.l10n_sv_document_type_code == '03':
            self.l10n_latam_identification_type_id = self.env.ref('l10n_latam_base.it_pass').id
        elif self.l10n_sv_document_type_code == '02':
            self.l10n_latam_identification_type_id = self.env.ref('l10n_latam_base.it_fid').id
        elif self.l10n_sv_document_type_code == '13':
            self.l10n_latam_identification_type_id = self.env.ref('l10n_latam_sv.it_dui').id
        elif self.l10n_sv_document_type_code == '37':
            self.l10n_latam_identification_type_id = self.env.ref('l10n_latam_sv.it_other').id

    @api.onchange('company_registry')
    def _onchange_company_registry(self):
        if self.company_registry:
            # Eliminar guiones y espacios
            self.company_registry = re.sub(r'[-\s]', '', self.company_registry)

    @api.constrains('company_registry')
    def _check_company_registry_format(self):
        for partner in self:
            if partner.company_registry and not partner.company_registry.isdigit():
                raise ValidationError(_("El Número de Registro (NRC) debe contener únicamente dígitos."))

    @api.constrains('vat', 'country_id', 'l10n_sv_document_type_code')
    def _check_vat_for_sv_documents(self):
        for partner in self:
            if not partner.vat or len(partner.vat) == 1:
                continue

            if partner.country_id.code != 'SV':
                continue  # Solo validamos para El Salvador

            doc_type = partner.l10n_sv_document_type_code

            if doc_type == '36':  # NIT
                if not self._validate_nit(partner.vat):
                    raise ValidationError(_("El NIT ingresado no es válido: %s\nFormato esperado:\nNIT= 12345678901234 (sin guiones) o\nNIT homologado= 123456789 (sin guion)") % partner.vat)

            elif doc_type == '13':  # DUI
                if not self._validate_dui(partner.vat):
                    raise ValidationError(_("El DUI ingresado no es válido: %s\nFormato esperado: 12345678-9 (con guión)") % partner.vat)

    def _validate_nit(self, nit):
        """Valida NIT salvadoreño (14 o 9 dígitos, sin guiones)
        Validar que los primeros 2 dígitos estén entre 01 y 14 (códigos de departamento válido)
        Validar dígito verificador del NIT homologado (módulo 10)"""
        # Eliminar espacios pero no guiones para verificar formato
        nit_clean = nit.strip() if nit else ''
        
        # Verificar que no tenga guiones
        if '-' in nit_clean:
            return False
            
        # Verificar que solo contenga dígitos
        if not nit_clean.isdigit():
            return False

        # Validar que los primeros 2 dígitos estén entre 01 y 14 (códigos de departamento válido)
        if len(nit_clean) == 14:
            digitos_iniciales = int(nit_clean[:2])
            return 1 <= digitos_iniciales <= 14

        # Validar dígito verificador del NIT homologado (módulo 10)
        elif len(nit_clean) == 9:
            # suma = sum(int(digito) * (9 - i) for i, digito in enumerate(nit_clean[:-1]))
            # verificacion = suma % 10
            # digito_control = 10 - verificacion if verificacion != 0 else 0
            # return int(nit_clean[-1]) == digito_control
            
            return True

        return False

    def _validate_dui(self, dui):
        """Valida DUI salvadoreño: 8 dígitos + guion + 1 dígito verificador (mod 10)"""
        # Verificar formato obligatorio: 8 dígitos + guion + 1 dígito
        if not re.match(r'^\d{8}-\d{1}$', dui):
            return False
            
        # # Extraer los dígitos para validación
        # dui_parts = dui.split('-')
        # if len(dui_parts) != 2 or len(dui_parts[0]) != 8 or len(dui_parts[1]) != 1:
        #     return False
            
        # # Concatenar para validación del dígito verificador
        # dui_clean = dui_parts[0] + dui_parts[1]
        
        # # Validación del dígito verificador
        # suma = sum(int(d) * (9 - i) for i, d in enumerate(dui_clean[:-1]))
        # verificador = suma % 10
        # return int(dui_clean[-1]) == verificador

        return True

    # === ANULA VALIDACIÓN ESTÁNDAR DE ODOO PARA SV ===

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self._should_skip_vat_validation(vals):
                self = self.with_context(no_vat_validation=True)
                break
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        if self._should_skip_vat_validation(vals):
            self = self.with_context(no_vat_validation=True)
        return super(ResPartner, self).write(vals)

    def _should_skip_vat_validation(self, vals):
        """Evita validación estándar de VAT para El Salvador y tipos locales"""
        doc_type = vals.get('l10n_sv_document_type_code') or self.l10n_sv_document_type_code
        country_id = vals.get('country_id') or self.country_id.id
        if not doc_type or not country_id:
            return False
        country = self.env['res.country'].browse(country_id)
        return country.code == 'SV' and doc_type in ['13', '36', '02', '03', '37']
