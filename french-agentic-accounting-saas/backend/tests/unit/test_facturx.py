# -----------------------------------------------------------------------------
# File: test_facturx.py
# Description: Unit tests for Factur-X XML generator
# -----------------------------------------------------------------------------

"""Unit tests for Factur-X XML generator."""
import pytest
import xml.etree.ElementTree as ET

from services.einvoice_service.facturx_generator import generate_facturx_xml


class TestGenerateFacturXML:
    def test_generates_valid_xml(self):
        data = {
            "invoice_number": "FAC-000001",
            "issue_date": "2025-03-15",
            "issuer_name": "Ma Societe",
            "issuer_vat_number": "FR12345678901",
            "recipient_name": "Client SARL",
            "recipient_vat_number": "FR98765432101",
            "currency": "EUR",
            "total_ht": "1000.00",
            "total_vat": "200.00",
            "total_ttc": "1200.00",
        }
        xml = generate_facturx_xml(data, [])
        assert xml is not None
        assert "CrossIndustryInvoice" in xml

    def test_contains_invoice_number(self):
        data = {"invoice_number": "TEST-001", "issue_date": "2025-01-01",
                "issuer_name": "", "recipient_name": "", "currency": "EUR",
                "total_ht": "100", "total_vat": "20", "total_ttc": "120"}
        xml = generate_facturx_xml(data, [])
        assert "TEST-001" in xml

    def test_contains_amounts(self):
        data = {"invoice_number": "X", "issue_date": "2025-01-01",
                "issuer_name": "", "recipient_name": "", "currency": "EUR",
                "total_ht": "500.00", "total_vat": "100.00", "total_ttc": "600.00"}
        xml = generate_facturx_xml(data, [])
        assert "500.00" in xml
        assert "100.00" in xml
        assert "600.00" in xml
