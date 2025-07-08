import logging
from odoo import models, api, _

_logger = logging.getLogger(__name__)


class InvoiceDteReport(models.AbstractModel):
    """Reporte DTE personalizado para facturas"""
    _name = 'report.l10n_sv_reports.invoice_dte_template'
    _description = 'Reporte DTE El Salvador'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepara valores para el reporte"""
        
        # Obtener documentos
        docs = self.env['account.move'].browse(docids)
        
        # Obtener datos del contexto
        template_id = data.get('template_id') if data else None
        include_qr = data.get('include_qr', True) if data else True
        include_signature_info = data.get('include_signature_info', True) if data else True
        include_mh_info = data.get('include_mh_info', True) if data else True
        preview_mode = data.get('preview_mode', False) if data else False
        
        # Procesar cada documento
        report_data = []
        for doc in docs:
            # Obtener plantilla
            if template_id:
                template = self.env['l10n_sv.report.template'].browse(template_id)
            else:
                template = self._get_template_for_document(doc)
            
            # Generar QR si es necesario y está habilitado
            if include_qr and not doc.l10n_sv_qr_generated and not preview_mode:
                try:
                    doc.action_generate_qr_code()
                except Exception as e:
                    _logger.warning(f'No se pudo generar QR para {doc.name}: {str(e)}')
            
            # Preparar datos del documento
            doc_data = {
                'doc': doc,
                'template': template,
                'qr_code': doc.l10n_sv_qr_code if include_qr else None,
                'barcode': doc.l10n_sv_barcode,
                'include_signature_info': include_signature_info,
                'include_mh_info': include_mh_info,
                'dte_summary': doc.get_dte_summary_data(),
                'status_badge': doc.get_dte_status_badge(),
                'watermark_text': template.get_watermark_text(doc) if template else '',
                'preview_mode': preview_mode
            }
            
            report_data.append(doc_data)
        
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'report_data': report_data,
            'company': docs[0].company_id if docs else self.env.company,
            'report_title': self._get_report_title(docs),
            'print_date': self._get_formatted_datetime(),
        }

    def _get_template_for_document(self, doc):
        """Obtiene plantilla para el documento"""
        if doc.l10n_sv_report_template_id:
            return doc.l10n_sv_report_template_id
        
        # Buscar por tipo de documento
        if doc.l10n_sv_document_type_id:
            template = self.env['l10n_sv.report.template'].get_template_for_document(
                doc.l10n_sv_document_type_id.id,
                doc.company_id.id
            )
            # Asignar plantilla al documento para futuras referencias
            doc.l10n_sv_report_template_id = template.id
            return template
        
        # Plantilla por defecto
        return self.env['l10n_sv.report.template'].get_template_for_document(
            False,
            doc.company_id.id
        )

    def _get_report_title(self, docs):
        """Obtiene título del reporte"""
        if len(docs) == 1:
            doc = docs[0]
            if doc.l10n_sv_document_type_id:
                return doc.l10n_sv_document_type_id.name
            else:
                return 'Factura Electrónica'
        else:
            return 'Documentos Tributarios Electrónicos'

    def _get_formatted_datetime(self):
        """Obtiene fecha y hora formateada"""
        from datetime import datetime
        now = datetime.now()
        return now.strftime('%d/%m/%Y %H:%M:%S')

    @api.model
    def _get_line_tax_summary(self, lines):
        """Obtiene resumen de impuestos por línea"""
        tax_summary = {}
        
        for line in lines:
            for tax in line.tax_ids:
                tax_key = f"{tax.name} ({tax.amount}%)"
                if tax_key not in tax_summary:
                    tax_summary[tax_key] = {
                        'tax': tax,
                        'base_amount': 0.0,
                        'tax_amount': 0.0
                    }
                
                tax_summary[tax_key]['base_amount'] += line.price_subtotal
                # Calcular impuesto
                tax_amount = line.price_subtotal * (tax.amount / 100)
                tax_summary[tax_key]['tax_amount'] += tax_amount
        
        return list(tax_summary.values())

    @api.model
    def _format_currency(self, amount, currency):
        """Formatea moneda para reporte"""
        return f"{currency.symbol} {amount:,.2f}"

    @api.model
    def _get_payment_terms_info(self, doc):
        """Obtiene información de términos de pago"""
        if not doc.invoice_payment_term_id:
            return "Contado"
        
        terms = []
        for line in doc.invoice_payment_term_id.line_ids:
            if line.days == 0:
                terms.append("Contado")
            else:
                terms.append(f"{line.value_amount:.0f}% a {line.days} días")
        
        return " + ".join(terms)

    @api.model
    def _get_company_address_formatted(self, company):
        """Obtiene dirección de empresa formateada"""
        address_parts = []
        
        if company.street:
            address_parts.append(company.street)
        if company.street2:
            address_parts.append(company.street2)
        if company.city:
            address_parts.append(company.city)
        if company.state_id:
            address_parts.append(company.state_id.name)
        if company.country_id:
            address_parts.append(company.country_id.name)
        
        return ", ".join(address_parts)

    @api.model
    def _get_partner_address_formatted(self, partner):
        """Obtiene dirección de cliente formateada"""
        address_parts = []
        
        if partner.street:
            address_parts.append(partner.street)
        if partner.street2:
            address_parts.append(partner.street2)
        if partner.city:
            address_parts.append(partner.city)
        if partner.state_id:
            address_parts.append(partner.state_id.name)
        if partner.country_id and partner.country_id.code != 'SV':
            address_parts.append(partner.country_id.name)
        
        return ", ".join(address_parts) if address_parts else "No especificada"

    @api.model
    def _should_show_taxes_detail(self, doc):
        """Determina si mostrar detalle de impuestos"""
        # Mostrar detalle si hay más de un tipo de impuesto
        tax_types = set()
        for line in doc.invoice_line_ids:
            for tax in line.tax_ids:
                tax_types.add(tax.id)
        
        return len(tax_types) > 1

    @api.model
    def _get_dte_validation_info(self, doc):
        """Obtiene información de validación DTE"""
        validations = []
        
        # Estado JSON
        if doc.l10n_sv_json_validated:
            validations.append({
                'label': 'JSON DTE Validado',
                'status': 'success',
                'icon': 'fa-check-circle'
            })
        
        # Estado firma
        if doc.l10n_sv_signature_status == 'verified':
            validations.append({
                'label': 'Firma Digital Verificada',
                'status': 'success',
                'icon': 'fa-shield'
            })
        elif doc.l10n_sv_signature_status == 'signed':
            validations.append({
                'label': 'Firmado Digitalmente',
                'status': 'info',
                'icon': 'fa-pencil-square-o'
            })
        
        # Estado MH
        if doc.l10n_sv_mh_status == 'approved':
            validations.append({
                'label': 'Aprobado por MH',
                'status': 'success',
                'icon': 'fa-check-circle'
            })
        elif doc.l10n_sv_mh_status == 'processed':
            validations.append({
                'label': 'Procesado por MH',
                'status': 'info',
                'icon': 'fa-cog'
            })
        
        return validations