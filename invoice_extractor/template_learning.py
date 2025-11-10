"""Helpers for deriving invoice templates from sample text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, MutableMapping, Optional, Sequence

import re


_CURRENCY_RE = re.compile(r"^\s*\$?-?[0-9][0-9,]*(?:\.[0-9]{1,2})?\s*$")
_NUMBER_RE = re.compile(r"^\s*-?[0-9][0-9,]*(?:\.[0-9]+)?\s*$")
_DATE_RE = re.compile(
    r"^\s*(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4})\s*$"
)


@dataclass
class LearnedField:
    """Representation of a derived field definition."""

    name: str
    pattern: str
    transform: str
    required: bool = True
    group: int = 1


def _normalise_prefix(prefix: str) -> str:
    """Convert a literal prefix into a resilient regular expression."""

    if not prefix.strip():
        return ""

    parts: List[str] = []
    for match in re.finditer(r"\s+|[:#-]+|[^:#\-\s]+", prefix):
        token = match.group()
        if token.isspace():
            parts.append(r"\s+")
        elif set(token).issubset({":", "#", "-"}):
            parts.append(r"[:#\-]*")
        else:
            parts.append(re.escape(token))
    parts.append(r"[\s:#\-]*")
    return "".join(parts)


def _guess_value_pattern(value: str) -> str:
    """Return a pattern that should match similar values."""

    cleaned = value.strip()
    if not cleaned:
        return r"[\S\s]*"
    if _CURRENCY_RE.match(cleaned):
        return r"-?[0-9][0-9,]*(?:\.[0-9]{1,2})?"
    if _NUMBER_RE.match(cleaned):
        return r"-?[0-9][0-9,]*(?:\.[0-9]+)?"
    if _DATE_RE.match(cleaned):
        return r"[A-Za-z0-9,\/\- ]+"
    if re.fullmatch(r"[A-Za-z0-9-]+", cleaned):
        return r"[A-Za-z0-9-]+"
    if re.fullmatch(r"[A-Za-z0-9 .,/#-]+", cleaned):
        return r"[A-Za-z0-9 .,/#-]+"
    return r"[^\n]+"


def _guess_transform(value: str) -> str:
    cleaned = value.strip()
    if _CURRENCY_RE.match(cleaned):
        return "currency"
    if _DATE_RE.match(cleaned):
        return "date"
    if _NUMBER_RE.match(cleaned):
        return "number"
    return "text"


def _find_best_line(text: str, value: str) -> tuple[str, str]:
    """Locate the line containing *value* and return the line and prefix."""

    lower_value = value.strip().lower()
    if not lower_value:
        raise ValueError("Field value cannot be empty")

    lines = text.splitlines()
    for index, line in enumerate(lines):
        lowered_line = line.lower()
        position = lowered_line.find(lower_value)
        if position != -1:
            prefix = line[:position]
            if not prefix.strip() and index > 0:
                # If the value is at the start of the line, attempt to use the
                # previous non-empty line as contextual prefix.
                previous_lines = [ln for ln in lines[:index][::-1] if ln.strip()]
                if previous_lines:
                    prefix = previous_lines[0].strip() + " "
            return line, prefix
    raise ValueError(f"Could not locate value '{value}' in the supplied text")


def derive_field(text: str, name: str, value: str) -> LearnedField:
    """Create a :class:`LearnedField` from a sample value within *text*."""

    line, prefix = _find_best_line(text, value)
    prefix_pattern = _normalise_prefix(prefix)
    transform = _guess_transform(value)
    value_pattern = _guess_value_pattern(value)

    if transform == "currency":
        currency_prefix = r"(?:[$€£¥₹]|USD|CAD|AUD|GBP|EUR)?\s*"
        if prefix_pattern:
            pattern = f"{prefix_pattern}{currency_prefix}({value_pattern})"
        else:
            pattern = f"{currency_prefix}({value_pattern})"
    else:
        pattern = f"{prefix_pattern}({value_pattern})" if prefix_pattern else f"({value_pattern})"
    return LearnedField(name=name, pattern=pattern, transform=transform)


def learn_fields(text: str, field_samples: Mapping[str, str]) -> List[LearnedField]:
    """Derive field definitions for a mapping of name to sample value."""

    learned: List[LearnedField] = []
    for name, value in field_samples.items():
        if not name:
            raise ValueError("Field name cannot be empty")
        learned.append(derive_field(text, name, value))
    return learned


def _infer_keywords(text: str, existing: Optional[Sequence[str]]) -> List[str]:
    keywords = [keyword for keyword in (existing or []) if keyword]
    if keywords:
        return keywords
    for line in text.splitlines():
        candidate = line.strip()
        if candidate:
            keywords.append(candidate)
            break
    if "invoice" not in (keyword.lower() for keyword in keywords):
        keywords.append("invoice")
    return keywords


def learn_template_from_text(
    text: str,
    *,
    name: Optional[str] = None,
    keywords: Optional[Sequence[str]] = None,
    field_samples: Optional[Mapping[str, str]] = None,
) -> Dict[str, object]:
    """Return a template definition learned from *text* and example values."""

    if not field_samples:
        raise ValueError("At least one field sample must be provided")

    learned_fields = learn_fields(text, field_samples)
    template_fields: Dict[str, MutableMapping[str, object]] = {}
    for field in learned_fields:
        template_fields[field.name] = {
            "pattern": field.pattern,
            "group": field.group,
            "transform": field.transform,
            "required": field.required,
        }

    template_name = name or "Learned Template"
    template_keywords = _infer_keywords(text, keywords)

    return {
        "name": template_name,
        "keywords": list(template_keywords),
        "fields": template_fields,
    }

