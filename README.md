# Invoice Extraction Toolkit

This project provides a small framework for extracting structured data from
scanned invoices. It converts PDF and image invoices to text using OCR and then
applies configurable templates to capture key fields such as invoice number,
dates and totals. Extracted data can be exported to CSV via either a command
line interface or a Tkinter based GUI.

## Features

- OCR support for PDF and common image formats (PNG, JPEG, TIFF, ...)
- Template driven parsing with easily extendable JSON definitions
- Command line workflow for batch processing
- Simple GUI to select files and review extracted text
- Built-in sample templates for two fictitious vendors to use as a starting
  point
- CSV export that automatically aggregates all captured fields

## Installation

1. Ensure Python 3.10 or newer is installed.
2. Install the project dependencies:

   ```bash
   pip install -e .[dev]
   ```

   The OCR pipeline requires [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
   to be installed on your system. For PDF documents, the
   [`pdf2image`](https://pypi.org/project/pdf2image/) library additionally
   depends on [Poppler](https://poppler.freedesktop.org/) binaries being
   available.

## Command line usage

Process one or more invoices and export the results to CSV:

```bash
python -m invoice_extractor.cli invoice1.pdf invoice2.png -o output.csv
```

Useful flags:

- `--templates path/to/custom_templates.json` – load additional template
  definitions. Specify multiple times to load several files.
- `--no-default-templates` – skip the bundled example templates if you only
  want to use your own.
- `--language` – pass a language hint to Tesseract (defaults to `eng`).
- `--show-raw-text` – print the OCR output to help you craft new templates.

## GUI usage

Run the graphical interface with:

```bash
python -m invoice_extractor.gui
```

Use the **Select Invoices** button to choose one or more PDF or image files,
then **Choose Output CSV** to pick where the results should be saved. Press
**Process** to start the extraction. The lower panel shows the OCR'd text and
any fields that were captured for the selected invoice.

## Creating new templates

<<<<<<< ours
=======
You can bootstrap a template directly from a sample invoice using the learning
CLI:

```bash
python -m invoice_extractor.learn 1013-1016-1.pdf \
  --field invoice_number=1013-1016-1 \
  --field total="$456.00" \
  --keyword "Your Vendor Name" \
  --output custom_templates.json
```

The command will run OCR on the provided document (pass `--text-input` if you
already have a plain text version), infer robust regular expressions for the
supplied field samples, and either create or update the destination JSON file.
The generated template is immediately compatible with both the CLI and the GUI
via the existing `--templates` option.

>>>>>>> theirs
Templates are stored as JSON files. Each template defines:

- A `name`
- A list of `keywords` to identify matching invoices
- A `fields` mapping where every entry contains a regular expression and an
  optional transform (`text`, `currency`, `number`, `date`).

Example snippet:

```json
{
  "templates": [
    {
      "name": "My Supplier",
      "keywords": ["My Supplier", "Invoice"],
      "fields": {
        "invoice_number": {
          "pattern": "Invoice #[:\\s]*([A-Z0-9-]+)",
          "group": 1
        },
        "total": {
          "pattern": "Total Due[:\\s$]*([\\d,.]+)",
          "transform": "currency"
        }
      }
    }
  ]
}
```

Save custom templates to a file and load them via the CLI `--templates` option
or by creating a custom `TemplateRepository` before launching the GUI.

## Limitations

- OCR quality directly impacts extraction accuracy. For best results, ensure the
  source images are high resolution and have good contrast.
- PDF processing relies on the external `poppler` binaries. Install them from
  your package manager if not already present.
- The current learning mechanism is template driven; adding new invoice formats
  requires creating suitable regular expressions.

## Running tests

Use `pytest` to run the included unit tests:

```bash
pytest
```
