from invoice_extractor.template_learning import learn_template_from_text
from invoice_extractor.templates import RegexInvoiceTemplate


def test_learn_template_generates_patterns_for_invoice():
    sample_text = """
    ACME Industrial Supplies
    Invoice #: 1013-1016-1
    Invoice Date: 10/16/2023
    Total Due: $1,234.00
    """

    template_dict = learn_template_from_text(
        sample_text,
        name="ACME Industrial Invoice",
        keywords=["ACME Industrial Supplies"],
        field_samples={
            "invoice_number": "1013-1016-1",
            "invoice_date": "10/16/2023",
            "total": "$1,234.00",
        },
    )

    template = RegexInvoiceTemplate.from_dict(template_dict)

    new_text = """
    ACME Industrial Supplies
    Invoice #: 1013-1017-9
    Invoice Date: 11/01/2023
    Total Due: $987.65
    """

    extracted = template.extract(new_text)

    assert extracted["invoice_number"] == "1013-1017-9"
    assert extracted["invoice_date"] == "11/01/2023"
    # Currency transform removes commas and the leading symbol.
    assert extracted["total"] == "987.65"
