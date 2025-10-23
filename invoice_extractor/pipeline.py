"""End-to-end invoice extraction pipeline."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

from .ocr import OCRConfig, extract_text
from .templates import TemplateRepository


@dataclass
class ExtractionResult:
    """Structured representation of an extraction."""

    source_path: Path
    template_name: Optional[str]
    confidence: float
    fields: Dict[str, str]
    raw_text: str = ""

    def to_row(self, additional_fields: Optional[Sequence[str]] = None) -> Dict[str, str]:
        row = {"source_path": str(self.source_path), "template": self.template_name or ""}
        row.update(self.fields)
        if additional_fields:
            for field in additional_fields:
                row.setdefault(field, "")
        row["confidence"] = f"{self.confidence:.2f}"
        return row


@dataclass
class InvoiceExtractor:
    """Extract structured data from invoice documents."""

    repository: TemplateRepository = field(default_factory=TemplateRepository.from_default)
    ocr_config: OCRConfig = field(default_factory=OCRConfig)
    confidence_threshold: float = 0.1

    def extract_from_text(self, text: str, source_path: Optional[Path] = None) -> ExtractionResult:
        template = self.repository.best_template(text)
        fields: Dict[str, str] = {}
        confidence = 0.0
        template_name: Optional[str] = None
        if template:
            confidence = template.match_score(text)
            if confidence >= self.confidence_threshold:
                template_name = template.name
                try:
                    fields = template.extract(text)
                except ValueError:
                    # Template matched but extraction failed; keep fields empty for transparency.
                    fields = {}
            else:
                confidence = 0.0
                template = None
        return ExtractionResult(
            source_path=source_path or Path("<memory>"),
            template_name=template_name,
            confidence=confidence,
            fields=fields,
            raw_text=text,
        )

    def process_file(self, path: Path | str) -> ExtractionResult:
        source_path = Path(path)
        text = extract_text(source_path, config=self.ocr_config)
        return self.extract_from_text(text, source_path=source_path)

    def process_files(self, paths: Iterable[Path | str]) -> List[ExtractionResult]:
        return [self.process_file(path) for path in paths]

    def export_csv(self, results: Iterable[ExtractionResult], destination: Path | str) -> Path:
        destination_path = Path(destination)
        results_list = list(results)
        field_names: Set[str] = {"source_path", "template", "confidence"}
        for result in results_list:
            field_names.update(result.fields.keys())
        ordered_fields = ["source_path", "template", "confidence"] + sorted(
            name for name in field_names if name not in {"source_path", "template", "confidence"}
        )
        with open(destination_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=ordered_fields)
            writer.writeheader()
            for result in results_list:
                row = result.to_row(additional_fields=[field for field in ordered_fields if field not in {"source_path", "template", "confidence"}])
                writer.writerow(row)
        return destination_path

