from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .core import audit_backlink_sites, build_campaign, load_backlink_sites, write_exports


class BacklinkBuilderApp(tk.Tk):
    """Small desktop GUI for building backlink outreach exports."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Backlink Builder")
        self.geometry("820x560")
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
        frame.rowconfigure(6, weight=1)

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
            "Progress below shows which imported sites are working and ready for manual link placement, "
            "and which are dead/not working."
        )
        ttk.Label(frame, text=help_text, wraplength=720, foreground="#555").grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=(4, 16)
        )

        ttk.Button(frame, text="Start Link Building Check", command=self._build_campaign).grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=(0, 12)
        )

        ttk.Label(frame, textvariable=self.status_var, wraplength=720).grid(row=5, column=0, columnspan=3, sticky="ew")

        self.progress_table = ttk.Treeview(frame, columns=("site", "status", "detail"), show="headings", height=10)
        self.progress_table.heading("site", text="Backlink site")
        self.progress_table.heading("status", text="Link made / status")
        self.progress_table.heading("detail", text="Details")
        self.progress_table.column("site", width=360)
        self.progress_table.column("status", width=160)
        self.progress_table.column("detail", width=220)
        self.progress_table.grid(row=6, column=0, columnspan=3, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.progress_table.yview)
        self.progress_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=6, column=3, sticky="ns")

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
        self.progress_table.delete(*self.progress_table.get_children())
        try:
            backlink_sites = load_backlink_sites(self.file_var.get())
            campaign = build_campaign(self.website_var.get(), backlink_sites=backlink_sites)
            self._show_progress(backlink_sites)
            paths = write_exports(campaign, Path(self.output_var.get()))
        except Exception as exc:  # noqa: BLE001 - surface validation errors to GUI users.
            messagebox.showerror("Backlink Builder", str(exc))
            self.status_var.set(f"Error: {exc}")
            return

        working_count = sum(
            1 for row_id in self.progress_table.get_children() if self.progress_table.item(row_id, "values")[1] == "Made / working"
        )
        message = (
            f"Created {len(campaign.opportunities)} opportunities. "
            f"{working_count} imported sites are working; {len(backlink_sites) - working_count} are not working/dead."
        )
        self.status_var.set(message)
        messagebox.showinfo("Backlink Builder", message + "\n\nExports:\n" + "\n".join(str(path) for path in paths))

    def _show_progress(self, backlink_sites: tuple[str, ...]) -> None:
        if not backlink_sites:
            self.progress_table.insert("", "end", values=("No backlink-sites file attached", "Skipped", "Only default opportunities created"))
            return

        for status in audit_backlink_sites(backlink_sites):
            display_status = "Made / working" if status.link_made else "Not working / dead"
            self.progress_table.insert("", "end", values=(status.site, display_status, status.detail))
            self.status_var.set(f"Checked {status.site}: {display_status}")
            self.update_idletasks()


def main() -> None:
    app = BacklinkBuilderApp()
    app.mainloop()
