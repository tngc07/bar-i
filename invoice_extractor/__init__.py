"""Invoice extraction toolkit.

This package provides utilities to convert scanned invoices into text via OCR
and match the extracted text against configurable templates to obtain
structured data.
"""

from .pipeline import InvoiceExtractor, ExtractionResult
from .templates import TemplateRepository, RegexInvoiceTemplate

__all__ = [
    "InvoiceExtractor",
    "ExtractionResult",
    "TemplateRepository",
    "RegexInvoiceTemplate",
]
