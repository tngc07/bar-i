"""Command line interface for the invoice extractor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional

from .ocr import OCRConfig
from .pipeline import InvoiceExtractor
from .templates import TemplateRepository


def _load_repository(template_paths: Optional[Iterable[Path | str]], use_default: bool) -> TemplateRepository:
    if use_default:
        repository = TemplateRepository.from_default()
    else:
        repository = TemplateRepository([])
    if template_paths:
        for path in template_paths:
            extra_repo = TemplateRepository.from_json_file(path)
            repository.extend(extra_repo.templates)
    return repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract structured data from invoice documents")
    parser.add_argument("inputs", nargs="+", help="Path(s) to invoice documents (PDF, PNG, JPEG, ...)")
    parser.add_argument("-o", "--output", required=True, help="Destination CSV file")
    parser.add_argument(
        "-t",
        "--templates",
        action="append",
        help="Optional JSON template files to load. Can be supplied multiple times.",
    )
    parser.add_argument(
        "--no-default-templates",
        action="store_true",
        help="Do not load the built-in template library.",
    )
    parser.add_argument("--language", default="eng", help="Language hint passed to Tesseract (default: eng)")
    parser.add_argument(
        "--tesseract-config",
        default="",
        help="Additional configuration string passed to Tesseract",
    )
    parser.add_argument("--dpi", type=int, default=300, help="DPI used when rasterising PDF files")
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.1,
        help="Minimum template confidence required before extraction is attempted.",
    )
    parser.add_argument(
        "--show-raw-text",
        action="store_true",
        help="Print the OCR'd text to stdout for debugging purposes.",
    )
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repository = _load_repository(args.templates, use_default=not args.no_default_templates)
    config = OCRConfig(language=args.language, tesseract_config=args.tesseract_config, dpi=args.dpi)
    extractor = InvoiceExtractor(repository=repository, ocr_config=config, confidence_threshold=args.confidence_threshold)

    results = []
    for input_path in args.inputs:
        path = Path(input_path)
        if not path.exists():
            parser.error(f"Input file {path} does not exist")
        result = extractor.process_file(path)
        results.append(result)
        if args.show_raw_text:
            print("=" * 80)
            print(f"Raw text for {path}:")
            print(result.raw_text)

    extractor.export_csv(results, args.output)
    print(f"Extraction complete. Saved {len(results)} record(s) to {args.output}.")
    return 0


def main() -> int:
    try:
        return run()
    except Exception as exc:  # pragma: no cover - entry point guard
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
