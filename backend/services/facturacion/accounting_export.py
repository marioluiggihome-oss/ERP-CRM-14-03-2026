# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Exportador Contable - LuiggiAI Engine
Genera ficheros CSV/TXT compatibles con:
- a3innuva / a3 ERP (Wolters Kluwer)
- Sage 200 / ContaPlus
- Formato estándar PGCE (Plan General de Contabilidad Español)
"""
import csv
import io
from datetime import datetime
from typing import List, Dict, Optional


class AccountingExporter:
    """Exporta facturas a formatos contables estándar"""

    # Cuentas contables por defecto (PGCE)
    ACCOUNTS = {
        "ventas": "7000000",          # Ventas de mercaderías
        "ventas_servicios": "7050000", # Prestaciones de servicios
        "iva_repercutido_21": "4770000",  # IVA repercutido 21%
        "iva_repercutido_10": "4770001",  # IVA repercutido 10%
        "iva_repercutido_4": "4770002",   # IVA repercutido 4%
        "clientes": "4300000",        # Clientes
        "clientes_efectos": "4310000", # Efectos comerciales a cobrar
        "irpf": "4730000",            # Retenciones IRPF
    }

    def __init__(self, custom_accounts: Optional[Dict] = None):
        if custom_accounts:
            self.ACCOUNTS.update(custom_accounts)

    def export_csv_standard(self, invoices: List[dict]) -> str:
        """
        Exporta facturas en formato CSV estándar contable.
        Compatible con importación en la mayoría de programas contables.
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        # Cabecera
        writer.writerow([
            "Fecha", "Asiento", "Cuenta", "Concepto",
            "Debe", "Haber", "NIF_Cliente", "Factura",
            "Serie", "Base_Imponible", "Tipo_IVA", "Cuota_IVA"
        ])

        for i, inv in enumerate(invoices, 1):
            asiento = f"{i:06d}"
            fecha = inv.get("issueDate", "")[:10]
            concepto = f"Fra. {inv.get('invoiceNumber', '')} - {inv.get('clientName', '')}"
            nif = inv.get("clientTaxId", "")
            factura = inv.get("invoiceNumber", "")
            serie = factura.split("-")[0] if "-" in factura else "A"

            total = inv.get("total", 0)
            base = inv.get("taxBase", 0)
            iva_total = inv.get("totalVat", 0)
            vat_rate = inv.get("vatRate", 21)

            # Asiento: Cliente al Debe
            writer.writerow([
                fecha, asiento,
                self._get_client_account(nif),
                concepto,
                f"{total:.2f}", "0.00",
                nif, factura, serie,
                f"{base:.2f}", f"{vat_rate:.2f}", f"{iva_total:.2f}"
            ])

            # Asiento: Ventas al Haber
            writer.writerow([
                fecha, asiento,
                self.ACCOUNTS["ventas"],
                concepto,
                "0.00", f"{base:.2f}",
                nif, factura, serie,
                f"{base:.2f}", "", ""
            ])

            # Asiento: IVA repercutido al Haber
            if iva_total > 0:
                iva_account = self._get_iva_account(vat_rate)
                writer.writerow([
                    fecha, asiento,
                    iva_account,
                    f"IVA Rep. {vat_rate}% {factura}",
                    "0.00", f"{iva_total:.2f}",
                    nif, factura, serie,
                    f"{base:.2f}", f"{vat_rate:.2f}", f"{iva_total:.2f}"
                ])

        return output.getvalue()

    def export_a3_format(self, invoices: List[dict]) -> str:
        """
        Exporta en formato específico a3innuva/a3 ERP.
        Formato de longitud fija compatible con importación a3.
        """
        output = io.StringIO()

        for inv in invoices:
            fecha = inv.get("issueDate", "")[:10].replace("-", "")
            factura = inv.get("invoiceNumber", "")
            nif = inv.get("clientTaxId", "").ljust(15)
            nombre = inv.get("clientName", "")[:40].ljust(40)
            base = inv.get("taxBase", 0)
            iva = inv.get("totalVat", 0)
            total = inv.get("total", 0)
            tipo_iva = inv.get("vatRate", 21)

            # Registro tipo 1: Cabecera factura
            line = (
                f"1"                          # Tipo registro
                f"{fecha}"                    # Fecha YYYYMMDD
                f"{factura:<20}"              # Número factura
                f"{nif}"                      # NIF cliente
                f"{nombre}"                   # Nombre cliente
                f"{base:>12.2f}"             # Base imponible
                f"{tipo_iva:>5.2f}"          # Tipo IVA
                f"{iva:>12.2f}"              # Cuota IVA
                f"{total:>12.2f}"            # Total factura
                f"{'E'}"                      # Tipo operación (E=emitida)
            )
            output.write(line + "\n")

            # Registro tipo 2: Líneas de detalle
            for j, line_item in enumerate(inv.get("lines", []), 1):
                qty = line_item.get("quantity", 1)
                price = line_item.get("unitPrice", 0)
                desc = line_item.get("description", "")[:50].ljust(50)
                line_total = qty * price

                detail = (
                    f"2"
                    f"{fecha}"
                    f"{factura:<20}"
                    f"{j:>4}"
                    f"{desc}"
                    f"{qty:>8.2f}"
                    f"{price:>12.2f}"
                    f"{line_total:>12.2f}"
                )
                output.write(detail + "\n")

        return output.getvalue()

    def export_sage_format(self, invoices: List[dict]) -> str:
        """
        Exporta en formato Sage 200 / ContaPlus.
        Formato CSV con campos específicos de Sage.
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")

        # Cabecera Sage
        writer.writerow([
            "EMPRESA", "EJERCICIO", "ASESSION", "FECHA",
            "SUBCUENTA", "CONTRAPARTIDA", "CONCEPTO",
            "DEBE", "HABER", "FACTURA", "BASEIVA",
            "PORCENTAJEIVA", "CUOTAIVA", "DOCUMENTO"
        ])

        year = datetime.now().year
        empresa = "001"

        for i, inv in enumerate(invoices, 1):
            fecha = inv.get("issueDate", "")[:10]
            factura = inv.get("invoiceNumber", "")
            concepto = f"{inv.get('clientName', '')} - {factura}"[:50]
            nif = inv.get("clientTaxId", "")
            base = inv.get("taxBase", 0)
            iva = inv.get("totalVat", 0)
            total = inv.get("total", 0)
            vat_rate = inv.get("vatRate", 21)

            # Línea cliente (Debe)
            writer.writerow([
                empresa, year, f"{i:06d}", fecha,
                self._get_client_account(nif),
                self.ACCOUNTS["ventas"],
                concepto,
                f"{total:.2f}", "0.00",
                factura, f"{base:.2f}",
                f"{vat_rate:.2f}", f"{iva:.2f}", nif
            ])

            # Línea ventas (Haber)
            writer.writerow([
                empresa, year, f"{i:06d}", fecha,
                self.ACCOUNTS["ventas"],
                self._get_client_account(nif),
                concepto,
                "0.00", f"{base:.2f}",
                factura, f"{base:.2f}",
                "", "", nif
            ])

            # Línea IVA (Haber)
            if iva > 0:
                writer.writerow([
                    empresa, year, f"{i:06d}", fecha,
                    self._get_iva_account(vat_rate),
                    self._get_client_account(nif),
                    f"IVA {vat_rate}% {factura}",
                    "0.00", f"{iva:.2f}",
                    factura, f"{base:.2f}",
                    f"{vat_rate:.2f}", f"{iva:.2f}", nif
                ])

        return output.getvalue()

    def export_sii_json(self, invoices: List[dict], company: dict) -> dict:
        """
        Genera el JSON para el Suministro Inmediato de Información (SII) de la AEAT.
        Formato para envío a la API REST del SII.
        """
        registros = []

        for inv in invoices:
            fecha_parts = inv.get("issueDate", "2025-01-01")[:10].split("-")
            ejercicio = fecha_parts[0]
            periodo = fecha_parts[1]

            registro = {
                "IDFactura": {
                    "IDEmisorFactura": {
                        "NIF": company.get("companyTaxId", "")
                    },
                    "NumSerieFacturaEmisor": inv.get("invoiceNumber", ""),
                    "FechaExpedicionFacturaEmisor": f"{fecha_parts[2]}-{fecha_parts[1]}-{fecha_parts[0]}"
                },
                "PeriodoLiquidacion": {
                    "Ejercicio": ejercicio,
                    "Periodo": periodo
                },
                "FacturaExpedida": {
                    "TipoFactura": "F1",  # Factura normal
                    "ClaveRegimenEspecialOTrascendencia": "01",
                    "DescripcionOperacion": f"Factura {inv.get('invoiceNumber', '')}",
                    "Contraparte": {
                        "NombreRazon": inv.get("clientName", ""),
                        "NIF": inv.get("clientTaxId", "")
                    },
                    "TipoDesglose": {
                        "DesgloseFactura": {
                            "Sujeta": {
                                "NoExenta": {
                                    "TipoNoExenta": "S1",
                                    "DesgloseIVA": {
                                        "DetalleIVA": [{
                                            "TipoImpositivo": inv.get("vatRate", 21),
                                            "BaseImponible": inv.get("taxBase", 0),
                                            "CuotaRepercutida": inv.get("totalVat", 0)
                                        }]
                                    }
                                }
                            }
                        }
                    },
                    "ImporteTotal": inv.get("total", 0)
                }
            }
            registros.append(registro)

        return {
            "Cabecera": {
                "IDVersionSii": "1.1",
                "Titular": {
                    "NombreRazon": company.get("companyName", ""),
                    "NIF": company.get("companyTaxId", "")
                },
                "TipoComunicacion": "A0"  # Alta
            },
            "RegistroLRFacturasEmitidas": registros
        }

    def _get_client_account(self, nif: str) -> str:
        """Genera cuenta contable del cliente basada en su NIF"""
        if not nif:
            return self.ACCOUNTS["clientes"]
        # Subcuenta: 430 + últimos 5 dígitos del NIF
        digits = "".join(c for c in nif if c.isdigit())
        suffix = digits[-5:].zfill(5) if digits else "00001"
        return f"430{suffix}"

    def _get_iva_account(self, rate: float) -> str:
        """Devuelve la cuenta de IVA repercutido según el tipo"""
        if rate >= 20:
            return self.ACCOUNTS["iva_repercutido_21"]
        elif rate >= 9:
            return self.ACCOUNTS["iva_repercutido_10"]
        else:
            return self.ACCOUNTS["iva_repercutido_4"]
