"""CrimeSight - Crime Records Management & Analysis System.

Author : Harsimar Singh
Run    : python main.py        (login: admin / admin123  or  officer / officer123)
"""
import csv
import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import charts
import database as db

APP_NAME = "CrimeSight"
SUBTITLE = "Crime Records Management & Analysis System"
def _load_author():
    """Header text. Put a custom line in author.txt (not uploaded) to override the name."""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "author.txt"),
                  encoding="utf-8") as fh:
            return fh.read().strip() or "Harsimar Singh"
    except OSError:
        return "Harsimar Singh"


AUTHOR = _load_author()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - {SUBTITLE}")
        self.geometry("1280x720")
        self.minsize(1100, 640)
        self.role = None
        self.username = None
        self.show_login()

    # ---------------------------------------------------------------- shared
    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def header(self, parent, right_widget_builder=None):
        bar = ctk.CTkFrame(parent, height=64, corner_radius=0, fg_color="#11131c")
        bar.pack(fill="x")
        ctk.CTkLabel(bar, text=f"  \U0001F50D {APP_NAME}", font=("Segoe UI", 26, "bold"),
                     text_color="#4cc9f0").pack(side="left", padx=(14, 10), pady=10)
        ctk.CTkLabel(bar, text=SUBTITLE, font=("Segoe UI", 13),
                     text_color="#9aa3b8").pack(side="left", pady=10)
        ctk.CTkLabel(bar, text=AUTHOR, font=("Segoe UI", 13, "bold"),
                     text_color="#f9c74f").pack(side="right", padx=20)
        if right_widget_builder:
            right_widget_builder(bar)
        return bar

    # ----------------------------------------------------------------- login
    def show_login(self):
        self.clear()
        self.header(self)
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(expand=True)
        card = ctk.CTkFrame(wrap, width=380, corner_radius=16)
        card.pack(padx=20, pady=20, ipadx=24, ipady=18)
        ctk.CTkLabel(card, text="Officer Login", font=("Segoe UI", 24, "bold")).pack(pady=(20, 4))
        ctk.CTkLabel(card, text="Sign in to access case records",
                     text_color="#9aa3b8").pack(pady=(0, 16))
        self.u = ctk.CTkEntry(card, placeholder_text="Username", width=280, height=38)
        self.u.pack(pady=6)
        self.p = ctk.CTkEntry(card, placeholder_text="Password", show="*", width=280, height=38)
        self.p.pack(pady=6)
        self.msg = ctk.CTkLabel(card, text="", text_color="#ef476f")
        self.msg.pack()
        ctk.CTkButton(card, text="Login", width=280, height=40, font=("Segoe UI", 14, "bold"),
                      command=self.do_login).pack(pady=(8, 6))
        ctk.CTkLabel(card, text="Demo:  admin / admin123    officer / officer123",
                     text_color="#6c7690", font=("Segoe UI", 11)).pack(pady=(6, 14))
        self.p.bind("<Return>", lambda e: self.do_login())
        self.u.bind("<Return>", lambda e: self.p.focus())
        self.u.focus()

    def do_login(self):
        role = db.login(self.u.get().strip(), self.p.get())
        if not role:
            self.msg.configure(text="Invalid username or password")
            return
        self.role, self.username = role, self.u.get().strip()
        self.show_main()

    # ------------------------------------------------------------------ main
    def show_main(self):
        self.clear()

        def right(bar):
            ctk.CTkButton(bar, text="Logout", width=80, fg_color="#ef476f",
                          hover_color="#c93a5b", command=self.show_login).pack(side="right", padx=8)
            ctk.CTkLabel(bar, text=f"\U0001F464 {self.username} ({self.role})",
                         text_color="#e6e8ee").pack(side="right", padx=8)

        self.header(self, right)
        self.tabs = ctk.CTkTabview(self, command=self.on_tab)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(6, 10))
        for name in ("Dashboard", "Records", "Analytics"):
            self.tabs.add(name)
        self.build_dashboard(self.tabs.tab("Dashboard"))
        self.build_records(self.tabs.tab("Records"))
        self.build_analytics(self.tabs.tab("Analytics"))
        self.refresh_all()

    def on_tab(self):
        self.refresh_all()

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_records()
        self.refresh_analytics()

    # ------------------------------------------------------------- dashboard
    def build_dashboard(self, tab):
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(top, text="Year:").pack(side="left", padx=(4, 6))
        self.year_var = ctk.StringVar(value="All")
        years = ["All"] + [str(y) for y in range(date.today().year, date.today().year - 3, -1)]
        ctk.CTkOptionMenu(top, values=years, variable=self.year_var, width=100,
                          command=lambda _: self.refresh_dashboard()).pack(side="left")
        self.kpi_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.kpi_frame.pack(fill="x", pady=4)
        self.kpis = {}
        for key, label, color in (("total", "Total Cases", "#4cc9f0"),
                                  ("open", "Open / Active", "#ef476f"),
                                  ("solved", "Solved %", "#06d6a0"),
                                  ("top_crime", "Most Common Crime", "#f8961e"),
                                  ("top_area", "Hottest Area", "#b5179e")):
            c = ctk.CTkFrame(self.kpi_frame, corner_radius=12, fg_color="#232839")
            c.pack(side="left", expand=True, fill="x", padx=5)
            ctk.CTkLabel(c, text=label, text_color="#9aa3b8", font=("Segoe UI", 12)).pack(pady=(10, 0))
            v = ctk.CTkLabel(c, text="-", text_color=color, font=("Segoe UI", 24, "bold"))
            v.pack(pady=(0, 10))
            self.kpis[key] = v
        self.dash_grid = ctk.CTkFrame(tab, fg_color="transparent")
        self.dash_grid.pack(fill="both", expand=True)
        for i in range(2):
            self.dash_grid.grid_columnconfigure(i, weight=1)
            self.dash_grid.grid_rowconfigure(i, weight=1)
        self.dash_canvases = []

    def _place_chart(self, parent, df, kind, row, col, store, size=(5, 2.9)):
        fig = charts.build_figure(df, kind, size)
        cv = FigureCanvasTkAgg(fig, master=parent)
        cv.get_tk_widget().grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        cv.draw()
        store.append(cv)

    def _drop(self, store):
        for cv in store:
            cv.get_tk_widget().destroy()
        store.clear()

    def refresh_dashboard(self):
        df = db.fetch()
        y = self.year_var.get()
        if y != "All":
            df = [r for r in df if r["date"].startswith(y)]
        s = charts.summary(df)
        self.kpis["total"].configure(text=str(s["total"]))
        self.kpis["open"].configure(text=str(s["open"]))
        self.kpis["solved"].configure(text=f"{s['solved']}%")
        self.kpis["top_crime"].configure(text=s["top_crime"], font=("Segoe UI", 18, "bold"))
        self.kpis["top_area"].configure(text=s["top_area"], font=("Segoe UI", 18, "bold"))
        self._drop(self.dash_canvases)
        for (kind, r, c) in ((charts.pie_types, 0, 0), (charts.bar_areas, 0, 1),
                             (charts.line_months, 1, 0), (charts.bar_status, 1, 1)):
            self._place_chart(self.dash_grid, df, kind, r, c, self.dash_canvases)

    # ------------------------------------------------------------- analytics
    def build_analytics(self, tab):
        self.an_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.an_frame.pack(fill="both", expand=True)
        self.an_frame.grid_columnconfigure(0, weight=1)
        self.an_frame.grid_columnconfigure(1, weight=1)
        self.an_frame.grid_rowconfigure(0, weight=1)
        self.an_frame.grid_rowconfigure(1, weight=0)
        self.an_text = ctk.CTkLabel(tab, text="", justify="left", anchor="w",
                                    font=("Consolas", 13), text_color="#e6e8ee")
        self.an_text.pack(fill="x", padx=10, pady=(0, 6))
        self.an_canvases = []

    def refresh_analytics(self):
        rows = db.fetch()
        self._drop(self.an_canvases)
        self._place_chart(self.an_frame, rows, charts.bar_hours, 0, 0, self.an_canvases, (5, 4.3))
        self._place_chart(self.an_frame, rows, charts.heat_area_type, 0, 1, self.an_canvases, (6, 4.3))
        y = date.today().year
        self.an_text.configure(text=charts.insights(rows, y, y - 1))

    # --------------------------------------------------------------- records
    def build_records(self, tab):
        f = ctk.CTkFrame(tab, fg_color="#232839", corner_radius=10)
        f.pack(fill="x", pady=(0, 6))
        self.f_search = ctk.CTkEntry(f, placeholder_text="Search ID / description / officer", width=240)
        self.f_search.grid(row=0, column=0, padx=6, pady=8)
        self.f_type = ctk.CTkOptionMenu(f, values=["All"] + db.CRIME_TYPES, width=130)
        self.f_area = ctk.CTkOptionMenu(f, values=["All"] + db.AREAS, width=130)
        self.f_status = ctk.CTkOptionMenu(f, values=["All"] + db.STATUSES, width=150)
        for i, w in enumerate((self.f_type, self.f_area, self.f_status), start=1):
            w.grid(row=0, column=i, padx=4)
        self.f_from = ctk.CTkEntry(f, placeholder_text="From YYYY-MM-DD", width=125)
        self.f_to = ctk.CTkEntry(f, placeholder_text="To YYYY-MM-DD", width=125)
        self.f_from.grid(row=0, column=4, padx=4)
        self.f_to.grid(row=0, column=5, padx=4)
        ctk.CTkButton(f, text="Apply", width=70, command=self.refresh_records).grid(row=0, column=6, padx=4)
        ctk.CTkButton(f, text="Reset", width=70, fg_color="#4a5068", command=self.reset_filters).grid(row=0, column=7, padx=4)
        self.f_search.bind("<Return>", lambda e: self.refresh_records())

        # table
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#1e2230", fieldbackground="#1e2230",
                        foreground="#e6e8ee", rowheight=26, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#11131c", foreground="#4cc9f0",
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#4361ee")])
        box = ctk.CTkFrame(tab, fg_color="transparent")
        box.pack(fill="both", expand=True)
        widths = {"case_id": 100, "crime_type": 110, "date": 90, "time": 55, "area": 120,
                  "severity": 70, "status": 130, "officer": 120, "description": 380}
        self.tree = ttk.Treeview(box, columns=db.COLUMNS, show="headings", selectmode="browse")
        for c in db.COLUMNS:
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, width=widths[c], anchor="w")
        sb = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.tag_configure("High", foreground="#ff6b81")
        self.tree.tag_configure("Closed", foreground="#06d6a0")
        self.tree.bind("<Double-1>", lambda e: self.edit_record())

        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", pady=(6, 0))
        ctk.CTkButton(bar, text="+ Add Case", width=110, fg_color="#06d6a0", text_color="#08130f",
                      hover_color="#05b384", command=self.add_record).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="Edit", width=90, command=self.edit_record).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="Delete", width=90, fg_color="#ef476f", hover_color="#c93a5b",
                      command=self.delete_record).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="Export CSV", width=110, fg_color="#4a5068",
                      command=lambda: self.export("csv")).pack(side="right", padx=4)
        ctk.CTkButton(bar, text="Export Excel", width=110, fg_color="#4a5068",
                      command=lambda: self.export("xlsx")).pack(side="right", padx=4)
        self.count_lbl = ctk.CTkLabel(bar, text="", text_color="#9aa3b8")
        self.count_lbl.pack(side="right", padx=14)

    def reset_filters(self):
        self.f_search.delete(0, "end")
        self.f_from.delete(0, "end")
        self.f_to.delete(0, "end")
        for w in (self.f_type, self.f_area, self.f_status):
            w.set("All")
        self.refresh_records()

    def current_rows(self):
        return db.fetch(self.f_search.get().strip(), self.f_type.get(), self.f_area.get(),
                        self.f_status.get(), self.f_from.get().strip(), self.f_to.get().strip())

    def refresh_records(self):
        rows = self.current_rows()
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            tag = "Closed" if r["status"] == "Closed" else ("High" if r["severity"] == "High" else "")
            self.tree.insert("", "end", iid=r["case_id"], values=[r[c] for c in db.COLUMNS], tags=(tag,))
        self.count_lbl.configure(text=f"{len(rows)} record(s)")

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, "Select a record first.")
            return None
        return sel[0]

    def add_record(self):
        RecordForm(self, None)

    def edit_record(self):
        cid = self.selected()
        if cid:
            RecordForm(self, db.get(cid))

    def delete_record(self):
        if self.role != "Admin":
            messagebox.showwarning(APP_NAME, "Only an Admin can delete records.")
            return
        cid = self.selected()
        if cid and messagebox.askyesno(APP_NAME, f"Permanently delete case {cid}?"):
            db.delete(cid)
            self.refresh_all()

    def export(self, kind):
        rows = self.current_rows()
        if not rows:
            messagebox.showinfo(APP_NAME, "Nothing to export.")
            return
        ext = ".csv" if kind == "csv" else ".xlsx"
        path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=f"crime_records{ext}",
                                            filetypes=[(kind.upper(), f"*{ext}")])
        if not path:
            return
        if kind == "csv":
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=db.COLUMNS)
                w.writeheader()
                w.writerows(rows)
        else:
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Crime Records"
            ws.append([c.replace("_", " ").title() for c in db.COLUMNS])
            for r in rows:
                ws.append([r[c] for c in db.COLUMNS])
            wb.save(path)
        messagebox.showinfo(APP_NAME, f"Exported {len(rows)} records to\n{path}")


class RecordForm(ctk.CTkToplevel):
    def __init__(self, app, rec):
        super().__init__(app)
        self.app, self.rec = app, rec
        self.title("Edit Case" if rec else "Add New Case")
        self.geometry("720x470")
        self.transient(app)
        self.after(150, self.grab_set)
        self.w = {}
        ctk.CTkLabel(self, text="Edit Case" if rec else "New Crime Case",
                     font=("Segoe UI", 20, "bold")).pack(pady=(12, 4))
        defaults = rec or {"case_id": db.next_case_id(), "date": date.today().isoformat(),
                           "time": "12:00", "crime_type": db.CRIME_TYPES[0], "area": db.AREAS[0],
                           "severity": "Medium", "status": "Open", "officer": db.OFFICERS[0],
                           "description": ""}
        fields = [("case_id", "Case ID", None), ("crime_type", "Crime Type", db.CRIME_TYPES),
                  ("date", "Date (YYYY-MM-DD)", None), ("time", "Time (HH:MM)", None),
                  ("area", "Area", db.AREAS), ("severity", "Severity", db.SEVERITIES),
                  ("status", "Status", db.STATUSES), ("officer", "Investigating Officer", db.OFFICERS)]
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=24)
        grid.grid_columnconfigure((0, 1), weight=1, uniform="c")
        for i, (key, label, opts) in enumerate(fields):
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=i // 2, column=i % 2, sticky="ew", padx=8, pady=3)
            ctk.CTkLabel(cell, text=label, anchor="w").pack(fill="x")
            if opts:
                w = ctk.CTkOptionMenu(cell, values=opts)
                w.set(defaults[key])
            else:
                w = ctk.CTkEntry(cell)
                w.insert(0, defaults[key])
            w.pack(fill="x")
            self.w[key] = w
        if rec:
            self.w["case_id"].configure(state="disabled")
        ctk.CTkLabel(self, text="Description", anchor="w").pack(fill="x", padx=32, pady=(4, 0))
        self.desc = ctk.CTkTextbox(self, height=60)
        self.desc.insert("1.0", defaults["description"])
        self.desc.pack(fill="x", padx=32)
        ctk.CTkButton(self, text="Save", height=38, command=self.save).pack(pady=10, padx=32, fill="x")

    def save(self):
        rec = {k: w.get().strip() for k, w in self.w.items()}
        if self.rec:
            rec["case_id"] = self.rec["case_id"]
        rec["description"] = self.desc.get("1.0", "end").strip()
        err = db.validate(rec, is_new=self.rec is None)
        if err:
            messagebox.showerror(APP_NAME, err, parent=self)
            return
        (db.update if self.rec else db.add)(rec)
        self.app.refresh_all()
        self.destroy()


if __name__ == "__main__":
    db.init_db()
    App().mainloop()
