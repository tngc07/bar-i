"""OCR utilities for invoice extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing helpers
    from PIL import Image as PILImage

try:
    import pytesseract
except ImportError:  # pragma: no cover - handled at runtime.
    pytesseract = None  # type: ignore[assignment]

try:
    from pdf2image import convert_from_path
except ImportError:  # pragma: no cover - optional dependency.
    convert_from_path = None  # type: ignore[assignment]

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional dependency.
    Image = None  # type: ignore[assignment]


class OCRDependencyError(RuntimeError):
    """Raised when an optional OCR dependency is missing."""


@dataclass
class OCRConfig:
    """Configuration options for OCR execution."""

    language: str = "eng"
    tesseract_config: str = ""
    dpi: int = 300


def _ensure_pytesseract() -> None:
    if pytesseract is None:
        raise OCRDependencyError(
            "pytesseract is not installed. Install it via 'pip install pytesseract' "
            "and ensure the Tesseract OCR engine is available on your system."
        )


def _ensure_pillow() -> None:
    if Image is None:
        raise OCRDependencyError(
            "Pillow is required to open image files. Install it via 'pip install Pillow'."
        )


def _open_image(path: Path) -> 'PILImage':
    _ensure_pillow()
    assert Image is not None  # for type checkers
    try:
        return Image.open(path)
    except OSError as exc:  # pragma: no cover - depends on runtime files
        raise RuntimeError(f"Unable to open image {path}: {exc}") from exc


def _load_pdf(path: Path, config: OCRConfig) -> List['PILImage']:
    if convert_from_path is None:
        raise OCRDependencyError(
            "pdf2image is required to process PDF files. Install it via "
            "'pip install pdf2image' and ensure the poppler binaries are available."
        )
    try:
        return convert_from_path(str(path), dpi=config.dpi)
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        raise RuntimeError(f"Failed to convert PDF {path} into images: {exc}") from exc


def load_images(path: Path | str, config: Optional[OCRConfig] = None) -> List['PILImage']:
    """Load images from the supplied document."""

    config = config or OCRConfig()
    document_path = Path(path)
    suffix = document_path.suffix.lower()

    if suffix == ".pdf":
        return _load_pdf(document_path, config)
    return [_open_image(document_path)]


def image_to_text(image: 'PILImage', config: Optional[OCRConfig] = None) -> str:
    """Extract text from a single image using Tesseract."""

    _ensure_pytesseract()
    config = config or OCRConfig()
    return pytesseract.image_to_string(image, lang=config.language, config=config.tesseract_config)


def extract_text(path: Path | str, config: Optional[OCRConfig] = None) -> str:
    """Extract text from a document path."""

    config = config or OCRConfig()
    images = load_images(path, config=config)
    texts: List[str] = []
    for image in images:
        texts.append(image_to_text(image, config=config))
    return "\n".join(texts)


def extract_batch(paths: Iterable[Path | str], config: Optional[OCRConfig] = None) -> List[str]:
    """Extract text from multiple documents."""

    return [extract_text(path, config=config) for path in paths]
