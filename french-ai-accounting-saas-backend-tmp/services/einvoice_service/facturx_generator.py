"""Factur-X XML generator (Basic profile / EN16931)."""
import structlog
from decimal import Decimal
from datetime import date
from xml.etree.ElementTree import Element, SubElement, tostring

logger = structlog.get_logger()

def generate_facturx_xml(invoice_data: dict, lines: list[dict]) -> str:
    """Generate Factur-X Basic XML conforming to EN16931."""
    root = Element("rsm:CrossIndustryInvoice")
    root.set("xmlns:rsm", "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100")
    root.set("xmlns:ram", "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100")
    root.set("xmlns:udt", "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100")

    # Header
    context = SubElement(root, "rsm:ExchangedDocumentContext")
    guideline = SubElement(context, "ram:GuidelineSpecifiedDocumentContextParameter")
    SubElement(guideline, "ram:ID").text = "urn:factur-x.eu:1p0:basic"

    header = SubElement(root, "rsm:ExchangedDocument")
    SubElement(header, "ram:ID").text = invoice_data.get("invoice_number", "")
    SubElement(header, "ram:TypeCode").text = "380"  # Commercial invoice
    issue = SubElement(header, "ram:IssueDateTime")
    fmt = SubElement(issue, "udt:DateTimeString")
    fmt.set("format", "102")
    fmt.text = invoice_data.get("issue_date", "").replace("-", "")

    # Trade
    trade = SubElement(root, "rsm:SupplyChainTradeTransaction")

    # Seller
    agreement = SubElement(trade, "ram:ApplicableHeaderTradeAgreement")
    seller = SubElement(agreement, "ram:SellerTradeParty")
    SubElement(seller, "ram:Name").text = invoice_data.get("issuer_name", "")
    if invoice_data.get("issuer_vat_number"):
        tax_reg = SubElement(seller, "ram:SpecifiedTaxRegistration")
        tax_id = SubElement(tax_reg, "ram:ID")
        tax_id.set("schemeID", "VA")
        tax_id.text = invoice_data["issuer_vat_number"]

    # Buyer
    buyer = SubElement(agreement, "ram:BuyerTradeParty")
    SubElement(buyer, "ram:Name").text = invoice_data.get("recipient_name", "")
    if invoice_data.get("recipient_vat_number"):
        tax_reg = SubElement(buyer, "ram:SpecifiedTaxRegistration")
        tax_id = SubElement(tax_reg, "ram:ID")
        tax_id.set("schemeID", "VA")
        tax_id.text = invoice_data["recipient_vat_number"]

    # Settlement
    settlement = SubElement(trade, "ram:ApplicableHeaderTradeSettlement")
    SubElement(settlement, "ram:InvoiceCurrencyCode").text = invoice_data.get("currency", "EUR")

    # Tax summary
    total_ht = Decimal(str(invoice_data.get("total_ht", 0)))
    total_vat = Decimal(str(invoice_data.get("total_vat", 0)))
    total_ttc = Decimal(str(invoice_data.get("total_ttc", 0)))

    tax = SubElement(settlement, "ram:ApplicableTradeTax")
    SubElement(tax, "ram:CalculatedAmount").text = str(total_vat)
    SubElement(tax, "ram:TypeCode").text = "VAT"
    SubElement(tax, "ram:BasisAmount").text = str(total_ht)
    SubElement(tax, "ram:CategoryCode").text = "S"
    SubElement(tax, "ram:RateApplicablePercent").text = "20.00"

    # Monetary summary
    monetary = SubElement(settlement, "ram:SpecifiedTradeSettlementHeaderMonetarySummation")
    SubElement(monetary, "ram:LineTotalAmount").text = str(total_ht)
    SubElement(monetary, "ram:TaxBasisTotalAmount").text = str(total_ht)
    SubElement(monetary, "ram:TaxTotalAmount").text = str(total_vat)
    SubElement(monetary, "ram:GrandTotalAmount").text = str(total_ttc)
    SubElement(monetary, "ram:DuePayableAmount").text = str(total_ttc)

    xml_str = tostring(root, encoding="unicode", xml_declaration=True)
    logger.info("facturx_xml_generated", invoice=invoice_data.get("invoice_number"))
    return xml_str
