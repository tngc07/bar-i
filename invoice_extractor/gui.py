"""Tkinter based graphical interface for the invoice extractor."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import Dict, List, Optional

from .pipeline import ExtractionResult, InvoiceExtractor


class InvoiceExtractorGUI:
    """Simple GUI for processing invoice documents."""

    def __init__(self, root: tk.Tk, extractor: Optional[InvoiceExtractor] = None) -> None:
        self.root = root
        self.root.title("Invoice Extractor")
        self.extractor = extractor or InvoiceExtractor()
        self.selected_files: List[Path] = []
        self.output_path: Optional[Path] = None
        self.results_tree: ttk.Treeview
        self.raw_text_widget: tk.Text
        self.status_var = tk.StringVar(value="Select invoices to begin.")
        self.result_map: Dict[str, ExtractionResult] = {}
        self._build_widgets()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Button(button_frame, text="Select Invoices", command=self._select_invoices).grid(
            row=0, column=0, padx=(0, 5)
        )
        ttk.Button(button_frame, text="Choose Output CSV", command=self._select_output).grid(
            row=0, column=1, padx=(0, 5)
        )
        ttk.Button(button_frame, text="Process", command=self._process).grid(row=0, column=2)

        ttk.Label(frame, textvariable=self.status_var).grid(row=1, column=0, sticky="w")

        columns = ("source", "template", "confidence")
        self.results_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        headings = {
            "source": "Invoice",
            "template": "Template",
            "confidence": "Confidence",
        }
        for column, heading in headings.items():
            self.results_tree.heading(column, text=heading)
            anchor = "w" if column != "confidence" else "e"
            self.results_tree.column(column, width=180, anchor=anchor)
        self.results_tree.grid(row=2, column=0, sticky="nsew")
        self.results_tree.bind("<<TreeviewSelect>>", self._on_result_selected)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=1, sticky="ns")

        self.raw_text_widget = tk.Text(frame, height=12, wrap="word")
        self.raw_text_widget.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        self.raw_text_widget.configure(state="disabled")

    def _select_invoices(self) -> None:
        files = filedialog.askopenfilenames(title="Select invoice documents")
        if files:
            self.selected_files = [Path(file) for file in files]
            self.status_var.set(f"Selected {len(self.selected_files)} file(s).")

    def _select_output(self) -> None:
        output = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if output:
            self.output_path = Path(output)
            self.status_var.set(f"Output will be saved to {self.output_path}")

    def _process(self) -> None:
        if not self.selected_files:
            messagebox.showwarning("No files", "Please select at least one invoice document.")
            return
        if not self.output_path:
            messagebox.showwarning("No output", "Please choose a destination CSV file.")
            return

        try:
            results = self.extractor.process_files(self.selected_files)
            self.extractor.export_csv(results, self.output_path)
        except Exception as exc:  # pragma: no cover - GUI feedback loop
            messagebox.showerror("Processing error", str(exc))
            return

        self._populate_results(results)
        self.status_var.set(f"Processed {len(results)} invoice(s). Saved to {self.output_path}.")
        messagebox.showinfo("Success", f"Extraction complete. Saved to {self.output_path}.")

    def _populate_results(self, results: List[ExtractionResult]) -> None:
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.result_map.clear()
        for result in results:
            confidence = f"{result.confidence:.2f}"
            item_id = self.results_tree.insert(
                "",
                "end",
                values=(result.source_path.name, result.template_name or "<no match>", confidence),
            )
            self.result_map[item_id] = result

    def _on_result_selected(self, _event) -> None:
        selection = self.results_tree.selection()
        if not selection:
            return
        item_id = selection[0]
        result = self.result_map.get(item_id)
        if not result:
            return
        self._show_details(result)

    def _show_details(self, result: ExtractionResult) -> None:
        self.raw_text_widget.configure(state="normal")
        self.raw_text_widget.delete("1.0", tk.END)
        lines = ["Fields:"]
        for key, value in result.fields.items():
            lines.append(f"- {key}: {value}")
        if not result.fields:
            lines.append("No fields were extracted.")
        lines.append("\nRaw text:\n")
        lines.append(result.raw_text)
        self.raw_text_widget.insert("1.0", "\n".join(lines))
        self.raw_text_widget.configure(state="disabled")


def launch_gui() -> None:
    root = tk.Tk()
    InvoiceExtractorGUI(root)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover - GUI entry point
    launch_gui()
