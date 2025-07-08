# -*- coding: utf-8 -*-
"""
Modelo temporal para debug de configuración de partner
"""
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class DebugPartner(models.TransientModel):
    _name = 'debug.partner'
    _description = 'Debug Partner Configuration'

    @api.model
    def check_partner_config(self, partner_id=8):
        """Verifica la configuración de un partner para CCF"""
        partner = self.env['res.partner'].browse(partner_id)
        
        if not partner.exists():
            return f"Partner con ID {partner_id} no existe"
        
        result = []
        result.append("="*60)
        result.append(f"CONFIGURACIÓN DEL PARTNER ID {partner_id}")
        result.append("="*60)
        
        # Datos básicos
        result.append("\nDatos básicos:")
        result.append(f"  Nombre: {partner.name}")
        result.append(f"  Es empresa: {partner.is_company}")
        result.append(f"  País: {partner.country_id.name if partner.country_id else 'N/A'}")
        
        # Identificación fiscal
        result.append("\nIdentificación fiscal:")
        result.append(f"  Tipo de documento: {partner.l10n_sv_document_type_code or 'N/A'}")
        result.append(f"  VAT/NIT: {partner.vat or 'N/A'}")
        result.append(f"  NRC: {partner.company_registry or 'N/A'}")
        
        # Campos específicos si existen
        if hasattr(partner, 'l10n_sv_nit'):
            result.append(f"  NIT (campo específico): {partner.l10n_sv_nit or 'N/A'}")
        if hasattr(partner, 'l10n_sv_nrc'):
            result.append(f"  NRC (campo específico): {partner.l10n_sv_nrc or 'N/A'}")
        
        # Tipo de identificación LATAM
        if partner.l10n_latam_identification_type_id:
            result.append(f"  Tipo identificación LATAM: {partner.l10n_latam_identification_type_id.name}")
        
        # Clasificación fiscal
        result.append("\nClasificación fiscal:")
        if hasattr(partner, 'l10n_sv_taxpayer_type'):
            result.append(f"  Tipo de contribuyente: {partner.l10n_sv_taxpayer_type or 'N/A'}")
        if hasattr(partner, 'l10n_sv_is_export_customer'):
            result.append(f"  Cliente exportación: {partner.l10n_sv_is_export_customer}")
        if hasattr(partner, 'l10n_sv_is_excluded_subject'):
            result.append(f"  Sujeto excluido: {partner.l10n_sv_is_excluded_subject}")
        if hasattr(partner, 'l10n_sv_is_withholding_agent'):
            result.append(f"  Agente retenedor: {partner.l10n_sv_is_withholding_agent}")
        
        if partner.property_account_position_id:
            result.append(f"  Posición fiscal: {partner.property_account_position_id.name}")
        else:
            result.append(f"  Posición fiscal: No asignada")
        
        # Verificar facturas recientes
        result.append("\nFacturas recientes del cliente:")
        invoices = self.env['account.move'].search([
            ('partner_id', '=', partner_id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '!=', 'cancel')
        ], limit=5, order='create_date desc')
        
        for inv in invoices:
            doc_type = inv.l10n_sv_document_type_id.name if inv.l10n_sv_document_type_id else 'N/A'
            result.append(f"  - {inv.name}: Tipo doc={doc_type}, Código EDI={inv.l10n_sv_edi_tipo_documento or 'N/A'}, Estado={inv.state}")
        
        # Análisis para CCF
        result.append("\n" + "="*60)
        result.append("ANÁLISIS PARA CCF:")
        result.append("="*60)
        
        issues = []
        
        # Verificar tipo de documento
        if partner.l10n_sv_document_type_code != '36':
            issues.append(f"❌ Tipo de documento no es NIT (actual: {partner.l10n_sv_document_type_code or 'N/A'})")
        else:
            result.append("✅ Tipo de documento es NIT (36)")
        
        # Verificar VAT
        if not partner.vat:
            issues.append("❌ No tiene VAT/NIT configurado")
        else:
            result.append(f"✅ Tiene VAT configurado: {partner.vat}")
        
        # Verificar tipo de contribuyente
        if hasattr(partner, 'l10n_sv_taxpayer_type'):
            if partner.l10n_sv_taxpayer_type != 'taxpayer':
                issues.append(f"❌ Tipo de contribuyente no es 'taxpayer' (actual: {partner.l10n_sv_taxpayer_type or 'N/A'})")
            else:
                result.append("✅ Tipo de contribuyente es 'taxpayer'")
        
        # Verificar país
        if partner.country_id and partner.country_id.code != 'SV':
            issues.append(f"⚠️ País no es El Salvador (actual: {partner.country_id.name})")
        
        if issues:
            result.append("\nProblemas encontrados:")
            for issue in issues:
                result.append(f"  {issue}")
            result.append("\nPara generar CCF, el cliente debe:")
            result.append("  1. Tener tipo de documento = NIT (código 36)")
            result.append("  2. Tener el NIT en el campo VAT")
            result.append("  3. El sistema calculará automáticamente tipo_contribuyente = 'taxpayer'")
        else:
            result.append("\n✅ La configuración del cliente parece correcta para CCF")
            result.append("   Si aún no genera CCF, verifica:")
            result.append("   - Regenerar el JSON de la factura")
            result.append("   - Reiniciar el servidor Odoo")
            result.append("   - Crear una nueva factura")
        
        # Log resultado
        full_result = "\n".join(result)
        _logger.info(full_result)
        
        return full_result