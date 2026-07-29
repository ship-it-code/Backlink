from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .core import build_campaign, load_backlink_sites, write_exports


class BacklinkBuilderApp(tk.Tk):
    """Small desktop GUI for building backlink outreach exports."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Backlink Builder")
        self.geometry("720x420")
        self.resizable(True, True)

        self.website_var = tk.StringVar()
        self.file_var = tk.StringVar()
        self.output_var = tk.StringVar(value="exports")
        self.status_var = tk.StringVar(value="Enter a website link and optionally attach a backlink-sites file.")

        self._build_form()

    def _build_form(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Website link").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(frame, textvariable=self.website_var).grid(row=0, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text="Backlink sites file").grid(row=1, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(frame, textvariable=self.file_var).grid(row=1, column=1, sticky="ew", pady=(0, 8))
        ttk.Button(frame, text="Attach file", command=self._choose_file).grid(row=1, column=2, padx=(8, 0), pady=(0, 8))

        ttk.Label(frame, text="Output folder").grid(row=2, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(frame, textvariable=self.output_var).grid(row=2, column=1, sticky="ew", pady=(0, 8))
        ttk.Button(frame, text="Choose folder", command=self._choose_output).grid(row=2, column=2, padx=(8, 0), pady=(0, 8))

        help_text = (
            "Attach a .txt or .csv file with one backlink site per line, or comma-separated URLs/domains.\n"
            "The app creates human-reviewed outreach exports; it does not auto-post spam links."
        )
        ttk.Label(frame, text=help_text, wraplength=640, foreground="#555").grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=(4, 16)
        )

        ttk.Button(frame, text="Build Backlink Plan", command=self._build_campaign).grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=(0, 16)
        )

        ttk.Label(frame, textvariable=self.status_var, wraplength=640).grid(row=5, column=0, columnspan=3, sticky="ew")

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select backlink sites file",
            filetypes=(("Text and CSV files", "*.txt *.csv"), ("All files", "*.*")),
        )
        if path:
            self.file_var.set(path)

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_var.set(path)

    def _build_campaign(self) -> None:
        try:
            backlink_sites = load_backlink_sites(self.file_var.get())
            campaign = build_campaign(self.website_var.get(), backlink_sites=backlink_sites)
            paths = write_exports(campaign, Path(self.output_var.get()))
        except Exception as exc:  # noqa: BLE001 - surface validation errors to GUI users.
            messagebox.showerror("Backlink Builder", str(exc))
            self.status_var.set(f"Error: {exc}")
            return

        message = f"Created {len(campaign.opportunities)} opportunities in {Path(self.output_var.get()).resolve()}"
        self.status_var.set(message)
        messagebox.showinfo("Backlink Builder", message + "\n\n" + "\n".join(str(path) for path in paths))


def main() -> None:
    app = BacklinkBuilderApp()
    app.mainloop()
