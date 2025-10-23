from invoice_extractor.pipeline import InvoiceExtractor
from invoice_extractor.templates import TemplateRepository


def test_default_repository_loads_templates():
    repository = TemplateRepository.from_default()
    assert len(list(repository)) >= 2


def test_invoice_extractor_matches_sample_text():
    text = """
    Northwind Traders
    Invoice Number: INV-1001
    Invoice Date: January 5, 2023
    Due Date: February 5, 2023
    Total Due: $1,234.56
    """
    extractor = InvoiceExtractor()
    result = extractor.extract_from_text(text, source_path=None)
    assert result.template_name == "Northwind Traders Simple Invoice"
    assert result.fields["invoice_number"] == "INV-1001"
    assert result.fields["total"] == "1234.56"
