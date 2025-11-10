"""Invoice extraction toolkit.

This package provides utilities to convert scanned invoices into text via OCR
and match the extracted text against configurable templates to obtain
structured data.
"""

from .pipeline import InvoiceExtractor, ExtractionResult
from .template_learning import learn_template_from_text
from .templates import TemplateRepository, RegexInvoiceTemplate

__all__ = [
    "InvoiceExtractor",
    "ExtractionResult",
    "TemplateRepository",
    "RegexInvoiceTemplate",
    "learn_template_from_text",
]
