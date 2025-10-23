"""Template definitions for extracting structured invoice data."""

from __future__ import annotations

import abc
import json
import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence


@dataclass
class FieldSpec:
    """Specification describing how to extract a field from text."""

    pattern: re.Pattern[str]
    group: int = 1
    transform: str = "text"
    required: bool = False

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "FieldSpec":
        pattern_value = value.get("pattern") if isinstance(value, MutableMapping) else None
        if not isinstance(pattern_value, str):
            raise ValueError("Field specification requires a 'pattern' entry")
        group_value = value.get("group", 1) if isinstance(value, MutableMapping) else 1
        transform_value = value.get("transform", "text") if isinstance(value, MutableMapping) else "text"
        required_value = value.get("required", False) if isinstance(value, MutableMapping) else False
        return cls(
            pattern=re.compile(pattern_value, re.IGNORECASE | re.MULTILINE),
            group=int(group_value),
            transform=str(transform_value),
            required=bool(required_value),
        )


class InvoiceTemplate(abc.ABC):
    """Abstract base class for invoice templates."""

    name: str
    keywords: Sequence[str]

    def __init__(self, name: str, keywords: Optional[Sequence[str]] = None) -> None:
        self.name = name
        self.keywords = tuple((keyword or "").lower() for keyword in (keywords or ()))

    def match_score(self, text: str) -> float:
        """Return how confidently this template matches the supplied text."""

        if not self.keywords:
            return 0.0
        lower_text = text.lower()
        matches = sum(1 for keyword in self.keywords if keyword and keyword in lower_text)
        return matches / len(self.keywords)

    @abc.abstractmethod
    def extract(self, text: str) -> Dict[str, str]:
        """Extract fields from the supplied text."""


@dataclass
class RegexInvoiceTemplate(InvoiceTemplate):
    """Invoice template using regular expressions to extract fields."""

    name: str
    keywords: Sequence[str]
    fields: Mapping[str, FieldSpec]

    def __init__(self, name: str, keywords: Optional[Sequence[str]], fields: Mapping[str, FieldSpec]):
        super().__init__(name=name, keywords=keywords)
        self.fields = fields

    def extract(self, text: str) -> Dict[str, str]:
        values: Dict[str, str] = {}
        for field_name, spec in self.fields.items():
            match = spec.pattern.search(text)
            if not match:
                if spec.required:
                    raise ValueError(
                        f"Field '{field_name}' could not be located using pattern {spec.pattern.pattern!r}"
                    )
                continue
            try:
                raw_value = match.group(spec.group)
            except IndexError as exc:
                raise ValueError(
                    f"Pattern for field '{field_name}' does not contain group {spec.group}: {spec.pattern.pattern!r}"
                ) from exc
            values[field_name] = _apply_transform(raw_value, spec.transform)
        return values

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "RegexInvoiceTemplate":
        name = str(payload.get("name", "Unnamed Template"))
        keywords_raw = payload.get("keywords", [])
        if isinstance(keywords_raw, str):
            keywords: Sequence[str] = [keywords_raw]
        elif isinstance(keywords_raw, Sequence):
            keywords = [str(keyword) for keyword in keywords_raw]
        else:
            keywords = []
        fields_raw = payload.get("fields")
        if not isinstance(fields_raw, Mapping):
            raise ValueError("Template definition requires a 'fields' mapping")
        fields: Dict[str, FieldSpec] = {}
        for field_name, field_payload in fields_raw.items():
            if not isinstance(field_payload, Mapping):
                raise ValueError(f"Field definition for '{field_name}' must be a mapping")
            fields[field_name] = FieldSpec.from_dict(field_payload)
        return cls(name=name, keywords=keywords, fields=fields)


def _apply_transform(value: str, transform: str) -> str:
    cleaned = value.strip()
    transform = (transform or "text").lower()
    if transform == "currency":
        cleaned = cleaned.replace(",", "")
        cleaned = cleaned.replace("$", "")
    elif transform == "number":
        cleaned = cleaned.replace(",", "")
    elif transform == "date":
        cleaned = cleaned.replace("\n", " ")
    return cleaned.strip()


@dataclass
class TemplateRepository:
    """Collection of invoice templates."""

    templates: List[InvoiceTemplate] = field(default_factory=list)

    def add(self, template: InvoiceTemplate) -> None:
        self.templates.append(template)

    def extend(self, templates: Iterable[InvoiceTemplate]) -> None:
        for template in templates:
            self.add(template)

    def __iter__(self):
        return iter(self.templates)

    def best_template(self, text: str) -> Optional[InvoiceTemplate]:
        best_score = -1.0
        best_template: Optional[InvoiceTemplate] = None
        for template in self.templates:
            score = template.match_score(text)
            if score > best_score:
                best_score = score
                best_template = template
        return best_template

    @classmethod
    def from_json_file(cls, path: Path | str) -> "TemplateRepository":
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        templates_payload = payload.get("templates", [])
        templates: List[InvoiceTemplate] = []
        for template_payload in templates_payload:
            if not isinstance(template_payload, Mapping):
                raise ValueError("Each template entry must be a mapping")
            templates.append(RegexInvoiceTemplate.from_dict(template_payload))
        return cls(templates=templates)

    @classmethod
    def from_default(cls) -> "TemplateRepository":
        with resources.files(__package__).joinpath("default_templates.json").open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        templates_payload = payload.get("templates", [])
        templates: List[InvoiceTemplate] = []
        for template_payload in templates_payload:
            if not isinstance(template_payload, Mapping):
                raise ValueError("Each template entry must be a mapping")
            templates.append(RegexInvoiceTemplate.from_dict(template_payload))
        return cls(templates=templates)

    def to_json(self) -> Dict[str, object]:
        data: Dict[str, object] = {"templates": []}
        for template in self.templates:
            if isinstance(template, RegexInvoiceTemplate):
                template_payload = {
                    "name": template.name,
                    "keywords": list(template.keywords),
                    "fields": {
                        name: {
                            "pattern": spec.pattern.pattern,
                            "group": spec.group,
                            "transform": spec.transform,
                            "required": spec.required,
                        }
                        for name, spec in template.fields.items()
                    },
                }
                data["templates"].append(template_payload)
        return data

    def save_json(self, path: Path | str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_json(), handle, indent=2, ensure_ascii=False)

