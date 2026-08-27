# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Generador de FacturaE 3.2.2 (XML)
Formato estándar español para facturación electrónica.
Compatible con: SII (AEAT), FACe, TicketBAI
Referencia: https://www.facturae.gob.es/formato/Versiones/Esquema_castellano_v3_2_2.pdf
"""
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
import hashlib
import base64
from typing import Optional, Dict, List


class FacturaeGenerator:
    """Genera documentos XML en formato FacturaE 3.2.2"""

    NAMESPACE = "http://www.facturae.gob.es/formato/Versiones/Facturaev3_2_2.xml"
    SCHEMA_VERSION = "3.2.2"

    # Tipos de factura
    INVOICE_TYPES = {
        "factura": "FC",           # Factura completa
        "rectificativa": "RC",     # Factura rectificativa
        "proforma": "OC",          # Factura proforma (no fiscal)
    }

    # Métodos de pago
    PAYMENT_METHODS = {
        "transferencia": "04",
        "domiciliacion": "02",
        "efectivo": "01",
        "tarjeta": "19",
        "pagare": "06",
        "cheque": "07",
    }

    # Tipos de IVA
    TAX_TYPES = {
        "IVA": "01",
        "IGIC": "02",
        "IRPF": "04",
    }

    def __init__(self, company_settings: dict):
        """
        Args:
            company_settings: Configuración de la empresa emisora
                - companyName, companyTaxId, companyAddress, companyCity,
                  companyPostalCode, companyProvince, companyCountry
        """
        self.company = company_settings

    def generate(self, invoice: dict, invoice_type: str = "factura") -> str:
        """
        Genera el XML de FacturaE 3.2.2

        Args:
            invoice: Datos de la factura (del modelo MongoDB)
            invoice_type: "factura", "rectificativa", "proforma"

        Returns:
            String XML formateado
        """
        root = Element("fe:Facturae")
        root.set("xmlns:fe", self.NAMESPACE)
        root.set("xmlns:ds", "http://www.w3.org/2000/09/xmldsig#")

        # 1. Cabecera del fichero
        self._add_file_header(root, invoice_type)

        # 2. Partes (emisor y receptor)
        self._add_parties(root, invoice)

        # 3. Facturas (puede haber varias, aquí solo una)
        invoices_elem = SubElement(root, "fe:Invoices")
        self._add_invoice(invoices_elem, invoice, invoice_type)

        # Formatear XML
        xml_str = tostring(root, encoding="unicode", xml_declaration=False)
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        pretty = parseString(xml_str).toprettyxml(indent="  ", encoding=None)
        # Quitar la declaración duplicada de minidom
        lines = pretty.split("\n")
        if lines[0].startswith("<?xml"):
            lines = lines[1:]
        return xml_declaration + "\n".join(lines)

    def _add_file_header(self, root: Element, invoice_type: str):
        """Añade FileHeader"""
        header = SubElement(root, "fe:FileHeader")
        SubElement(header, "fe:SchemaVersion").text = self.SCHEMA_VERSION
        SubElement(header, "fe:Modality").text = "I"  # Individual
        SubElement(header, "fe:InvoiceIssuerType").text = "EM"  # Emisor = proveedor

        # Batch (lote de 1 factura)
        batch = SubElement(header, "fe:Batch")
        SubElement(batch, "fe:BatchIdentifier").text = self.company.get("companyTaxId", "")
        SubElement(batch, "fe:InvoicesCount").text = "1"

        total_outstand = SubElement(batch, "fe:TotalInvoicesAmount")
        SubElement(total_outstand, "fe:TotalAmount").text = "0.00"  # Se actualiza después

        total_exec = SubElement(batch, "fe:TotalOutstandingAmount")
        SubElement(total_exec, "fe:TotalAmount").text = "0.00"

        SubElement(batch, "fe:InvoiceCurrencyCode").text = "EUR"

    def _add_parties(self, root: Element, invoice: dict):
        """Añade SellerParty y BuyerParty"""
        parties = SubElement(root, "fe:Parties")

        # ── Emisor (Seller) ──
        seller = SubElement(parties, "fe:SellerParty")
        seller_tax = SubElement(seller, "fe:TaxIdentification")
        SubElement(seller_tax, "fe:PersonTypeCode").text = "J"  # Jurídica
        SubElement(seller_tax, "fe:ResidenceTypeCode").text = "R"  # Residente
        SubElement(seller_tax, "fe:TaxIdentificationNumber").text = self.company.get("companyTaxId", "")

        # Datos legales del emisor
        legal_entity = SubElement(seller, "fe:LegalEntity")
        SubElement(legal_entity, "fe:CorporateName").text = self.company.get("companyName", "")

        address = SubElement(legal_entity, "fe:AddressInSpain")
        SubElement(address, "fe:Address").text = self.company.get("companyAddress", "")
        SubElement(address, "fe:PostCode").text = self.company.get("companyPostalCode", "00000")
        SubElement(address, "fe:Town").text = self.company.get("companyCity", "")
        SubElement(address, "fe:Province").text = self.company.get("companyProvince", "")
        SubElement(address, "fe:CountryCode").text = "ESP"

        # ── Receptor (Buyer) ──
        buyer = SubElement(parties, "fe:BuyerParty")
        buyer_tax = SubElement(buyer, "fe:TaxIdentification")

        # Determinar si es persona física o jurídica por el NIF/CIF
        tax_id = invoice.get("clientTaxId", "")
        is_company = tax_id and tax_id[0].isalpha() and tax_id[0] not in "XYZ"
        SubElement(buyer_tax, "fe:PersonTypeCode").text = "J" if is_company else "F"
        SubElement(buyer_tax, "fe:ResidenceTypeCode").text = "R"
        SubElement(buyer_tax, "fe:TaxIdentificationNumber").text = tax_id

        if is_company:
            legal = SubElement(buyer, "fe:LegalEntity")
            SubElement(legal, "fe:CorporateName").text = invoice.get("clientName", "")
            addr = SubElement(legal, "fe:AddressInSpain")
        else:
            individual = SubElement(buyer, "fe:Individual")
            # Intentar separar nombre y apellidos
            parts = invoice.get("clientName", "").split(" ", 1)
            SubElement(individual, "fe:Name").text = parts[0]
            SubElement(individual, "fe:FirstSurname").text = parts[1] if len(parts) > 1 else ""
            addr = SubElement(individual, "fe:AddressInSpain")

        SubElement(addr, "fe:Address").text = invoice.get("clientAddress", "")
        SubElement(addr, "fe:PostCode").text = invoice.get("clientPostalCode", "00000")
        SubElement(addr, "fe:Town").text = invoice.get("clientCity", "")
        SubElement(addr, "fe:Province").text = invoice.get("clientProvince", "")
        SubElement(addr, "fe:CountryCode").text = "ESP"

    def _add_invoice(self, invoices_elem: Element, invoice: dict, invoice_type: str):
        """Añade los datos de la factura"""
        inv = SubElement(invoices_elem, "fe:Invoice")

        # Cabecera de la factura
        inv_header = SubElement(inv, "fe:InvoiceHeader")
        SubElement(inv_header, "fe:InvoiceNumber").text = invoice.get("invoiceNumber", "")
        SubElement(inv_header, "fe:InvoiceSeriesCode").text = self._get_series(invoice_type)
        SubElement(inv_header, "fe:InvoiceDocumentType").text = self.INVOICE_TYPES.get(invoice_type, "FC")
        SubElement(inv_header, "fe:InvoiceClass").text = "OO"  # Original

        # Datos de emisión
        inv_data = SubElement(inv, "fe:InvoiceIssueData")
        SubElement(inv_data, "fe:IssueDate").text = invoice.get("issueDate", "")[:10]
        SubElement(inv_data, "fe:InvoiceCurrencyCode").text = "EUR"
        SubElement(inv_data, "fe:TaxCurrencyCode").text = "EUR"
        SubElement(inv_data, "fe:LanguageName").text = "es"

        # Impuestos
        taxes = SubElement(inv, "fe:TaxesOutputs")
        self._add_taxes(taxes, invoice)

        # Totales
        totals = SubElement(inv, "fe:InvoiceTotals")
        tax_base = invoice.get("taxBase", 0)
        total_vat = invoice.get("totalVat", 0)
        total = invoice.get("total", 0)

        SubElement(totals, "fe:TotalGrossAmount").text = f"{invoice.get('subtotal', 0):.2f}"
        
        # Descuentos generales
        if invoice.get("totalDiscount", 0) > 0:
            discounts = SubElement(totals, "fe:GeneralDiscounts")
            disc = SubElement(discounts, "fe:Discount")
            SubElement(disc, "fe:DiscountReason").text = "Descuento comercial"
            SubElement(disc, "fe:DiscountAmount").text = f"{invoice.get('totalDiscount', 0):.2f}"

        SubElement(totals, "fe:TotalGrossAmountBeforeTaxes").text = f"{tax_base:.2f}"
        SubElement(totals, "fe:TotalTaxOutputs").text = f"{total_vat:.2f}"
        SubElement(totals, "fe:TotalTaxesWithheld").text = "0.00"
        SubElement(totals, "fe:InvoiceTotal").text = f"{total:.2f}"
        SubElement(totals, "fe:TotalOutstandingAmount").text = f"{total:.2f}"
        SubElement(totals, "fe:TotalExecutableAmount").text = f"{total:.2f}"

        # Líneas de detalle
        items = SubElement(inv, "fe:Items")
        for i, line in enumerate(invoice.get("lines", []), 1):
            self._add_invoice_line(items, line, i)

        # Información de pago
        payment_details = SubElement(inv, "fe:PaymentDetails")
        installment = SubElement(payment_details, "fe:Installment")
        SubElement(installment, "fe:InstallmentDueDate").text = invoice.get("dueDate", "")[:10]
        SubElement(installment, "fe:InstallmentAmount").text = f"{total:.2f}"
        SubElement(installment, "fe:PaymentMeans").text = self.PAYMENT_METHODS.get(
            invoice.get("paymentMethod", "transferencia"), "04"
        )

        # IBAN si está configurado
        if self.company.get("companyIban"):
            account = SubElement(installment, "fe:AccountToBeCredited")
            SubElement(account, "fe:IBAN").text = self.company.get("companyIban", "")

        # Notas adicionales
        if invoice.get("notes"):
            additional = SubElement(inv, "fe:AdditionalData")
            SubElement(additional, "fe:InvoiceAdditionalInformation").text = invoice.get("notes", "")

    def _add_taxes(self, taxes_elem: Element, invoice: dict):
        """Añade el desglose de impuestos"""
        # Agrupar por tipo de IVA
        vat_groups = {}
        for line in invoice.get("lines", []):
            rate = line.get("vatRate", 21)
            qty = line.get("quantity", 1)
            price = line.get("unitPrice", 0)
            disc = line.get("discount", 0)
            gross = qty * price
            net = gross * (1 - disc / 100)
            if rate not in vat_groups:
                vat_groups[rate] = 0
            vat_groups[rate] += net

        for rate, base in vat_groups.items():
            tax = SubElement(taxes_elem, "fe:Tax")
            SubElement(tax, "fe:TaxTypeCode").text = "01"  # IVA
            SubElement(tax, "fe:TaxRate").text = f"{rate:.2f}"
            SubElement(tax, "fe:TaxableBase")
            tb = SubElement(tax, "fe:TaxableBase")
            SubElement(tb, "fe:TotalAmount").text = f"{base:.2f}"
            tax_amount = SubElement(tax, "fe:TaxAmount")
            SubElement(tax_amount, "fe:TotalAmount").text = f"{base * rate / 100:.2f}"

    def _add_invoice_line(self, items_elem: Element, line: dict, line_number: int):
        """Añade una línea de factura"""
        item = SubElement(items_elem, "fe:InvoiceLine")
        SubElement(item, "fe:ItemDescription").text = line.get("description", "")
        SubElement(item, "fe:Quantity").text = f"{line.get('quantity', 1):.2f}"

        unit_price = line.get("unitPrice", 0)
        SubElement(item, "fe:UnitPriceWithoutTax").text = f"{unit_price:.6f}"
        
        gross = line.get("quantity", 1) * unit_price
        SubElement(item, "fe:TotalCost").text = f"{gross:.2f}"

        # Descuento de línea
        discount_pct = line.get("discount", 0)
        if discount_pct > 0:
            discounts = SubElement(item, "fe:DiscountsAndRebates")
            disc = SubElement(discounts, "fe:Discount")
            SubElement(disc, "fe:DiscountReason").text = "Descuento"
            SubElement(disc, "fe:DiscountRate").text = f"{discount_pct:.4f}"
            SubElement(disc, "fe:DiscountAmount").text = f"{gross * discount_pct / 100:.2f}"

        net = gross * (1 - discount_pct / 100)
        SubElement(item, "fe:GrossAmount").text = f"{net:.2f}"

        # Impuesto de la línea
        taxes_output = SubElement(item, "fe:TaxesOutputs")
        tax = SubElement(taxes_output, "fe:Tax")
        SubElement(tax, "fe:TaxTypeCode").text = "01"
        vat_rate = line.get("vatRate", 21)
        SubElement(tax, "fe:TaxRate").text = f"{vat_rate:.2f}"
        tb = SubElement(tax, "fe:TaxableBase")
        SubElement(tb, "fe:TotalAmount").text = f"{net:.2f}"
        ta = SubElement(tax, "fe:TaxAmount")
        SubElement(ta, "fe:TotalAmount").text = f"{net * vat_rate / 100:.2f}"

    def _get_series(self, invoice_type: str) -> str:
        """Devuelve el código de serie según el tipo"""
        series_map = {
            "factura": "A",
            "rectificativa": "R",
            "proforma": "P",
        }
        return series_map.get(invoice_type, "A")

    def validate_tax_id(self, tax_id: str) -> bool:
        """Valida un NIF/CIF español (básico)"""
        if not tax_id or len(tax_id) < 9:
            return False
        tax_id = tax_id.upper().replace("-", "").replace(" ", "")
        # CIF: empieza por A-H, J, N, P, Q, R, S, U, V, W
        # NIF: empieza por número o X, Y, Z (NIE)
        return len(tax_id) == 9
