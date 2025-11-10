"""CLI utilities for building templates from an example invoice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

from .ocr import OCRConfig, OCRDependencyError, extract_text
from .template_learning import learn_template_from_text
from .templates import RegexInvoiceTemplate, TemplateRepository


def _parse_field_argument(argument: str) -> tuple[str, str]:
    if "=" not in argument:
        raise ValueError("Field definitions must use the NAME=VALUE syntax")
    name, value = argument.split("=", 1)
    name = name.strip()
    if not name:
        raise ValueError("Field name cannot be empty")
    return name, value.strip()


def _collect_fields(raw_fields: list[str]) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for raw in raw_fields:
        name, value = _parse_field_argument(raw)
        fields[name] = value
    if not fields:
        raise ValueError("At least one --field argument is required")
    return fields


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a JSON template definition by analysing a sample invoice. "
            "Provide the known field values using --field NAME=VALUE pairs."
        )
    )
    parser.add_argument("document", help="Path to an invoice PDF/image or a plain text file")
    parser.add_argument(
        "--text-input",
        action="store_true",
        help="Treat the provided document as pre-OCR'd UTF-8 text instead of running OCR.",
    )
    parser.add_argument(
        "--language",
        default="eng",
        help="Language hint for Tesseract OCR when processing PDF/image documents.",
    )
    parser.add_argument(
        "--name",
        help="Optional template name. Defaults to the stem of the provided document file.",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="Keyword used to match this template. Can be supplied multiple times.",
    )
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Field sample used to build the template. Provide once per field.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional destination JSON file. If the file exists it will be updated to "
            "include the learned template; otherwise a new file is created."
        ),
    )
    parser.add_argument(
        "--print-text",
        action="store_true",
        help="Print the OCR text to stdout for manual inspection.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        fields = _collect_fields(args.field)
    except ValueError as exc:
        parser.error(str(exc))

    document_path = Path(args.document)
    if not document_path.exists():
        parser.error(f"Document {document_path} does not exist")

    try:
        if args.text_input:
            text = document_path.read_text(encoding="utf-8")
        else:
            text = extract_text(document_path, config=OCRConfig(language=args.language))
    except OCRDependencyError as exc:
        parser.error(str(exc))
    except OSError as exc:  # pragma: no cover - filesystem specific
        parser.error(f"Failed to read document: {exc}")

    if args.print_text:
        print(text)

    template_name = args.name or document_path.stem

    try:
        learned_template = learn_template_from_text(
            text,
            name=template_name,
            keywords=args.keyword,
            field_samples=fields,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.output:
        repository = TemplateRepository()
        if args.output.exists():
            repository = TemplateRepository.from_json_file(args.output)
        repository.add(RegexInvoiceTemplate.from_dict(learned_template))
        repository.save_json(args.output)
        print(f"Template saved to {args.output}")
    else:
        payload = {"templates": [learned_template]}
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        print()
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

