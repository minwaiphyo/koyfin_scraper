import json
import os
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from playwright.sync_api import sync_playwright
import koyfin_scraper

COMPANIES_FILE = "companies.json"
SCRAPER_SCRIPT = "koyfin_scraper.py"
OUTPUT_FILE = os.path.join("output", "koyfin_overview_output.xlsx")
SESSION_DIR = "koyfin_session"



def load_companies():
    if not os.path.exists(COMPANIES_FILE):
        return []

    with open(COMPANIES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_companies(companies):
    with open(COMPANIES_FILE, "w", encoding="utf-8") as file:
        json.dump(companies, file, indent=2)


def session_exists():
    return os.path.exists(SESSION_DIR) and bool(os.listdir(SESSION_DIR))


def run_python_script(script_path):
    subprocess.run([sys.executable, script_path], check=True)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Koyfin Scraper")
        self.root.geometry("850x520")

        self.companies = load_companies()

        self.company_var = tk.StringVar()
        self.brands_var = tk.StringVar()
        self.ticker_var = tk.StringVar()
        self.koyfin_id_var = tk.StringVar()

        self.session_status_var = tk.StringVar()

        self.build_ui()
        self.refresh_table()
        self.update_session_status()

        if not session_exists():
            messagebox.showinfo(
                "Koyfin Login Required",
                "No Koyfin login session was found.\n\n"
                "Please click 'Login to Koyfin' before running the scraper."
            )

    def build_ui(self):
        form = ttk.LabelFrame(self.root, text="Add Company")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Company").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(form, textvariable=self.company_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Brands").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(form, textvariable=self.brands_var, width=30).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Ticker").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(form, textvariable=self.ticker_var, width=30).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Koyfin ID").grid(row=1, column=2, padx=5, pady=5)
        ttk.Entry(form, textvariable=self.koyfin_id_var, width=30).grid(row=1, column=3, padx=5, pady=5)

        ttk.Button(form, text="Add Company", command=self.add_company).grid(row=2, column=1, pady=10)
        ttk.Button(form, text="Remove Selected", command=self.remove_selected).grid(row=2, column=2, pady=10)

        columns = ("company", "brands", "ticker", "koyfin_id")
        self.table = ttk.Treeview(self.root, columns=columns, show="headings")

        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=190)

        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        buttons = ttk.Frame(self.root)
        buttons.pack(fill="x", padx=10, pady=10)

        self.login_button = ttk.Button(
            buttons,
            text="Login to Koyfin",
            command=self.create_session
        )
        self.login_button.pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Run Scraper",
            command=self.run_scraper
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Open Output Excel",
            command=self.open_output
        ).pack(side="left", padx=5)

        self.session_status_label = ttk.Label(
            buttons,
            textvariable=self.session_status_var
        )
        self.session_status_label.pack(side="left", padx=10)

    def update_session_status(self):
        if session_exists():
            self.session_status_var.set("Status: Koyfin session found")
            self.login_button.config(text="Refresh Koyfin Login")
        else:
            self.session_status_var.set("Status: Not logged in")
            self.login_button.config(text="Login to Koyfin")

    def refresh_table(self):
        for item in self.table.get_children():
            self.table.delete(item)

        for company in self.companies:
            self.table.insert(
                "",
                "end",
                values=(
                    company.get("company", ""),
                    company.get("brands", ""),
                    company.get("ticker", ""),
                    company.get("koyfin_id", ""),
                ),
            )

    def add_company(self):
        company = {
            "company": self.company_var.get().strip(),
            "brands": self.brands_var.get().strip(),
            "ticker": self.ticker_var.get().strip(),
            "koyfin_id": self.koyfin_id_var.get().strip(),
        }

        if not company["company"] or not company["ticker"] or not company["koyfin_id"]:
            messagebox.showerror("Missing Info", "Company, Ticker, and Koyfin ID are required.")
            return

        self.companies.append(company)
        save_companies(self.companies)
        self.refresh_table()

        self.company_var.set("")
        self.brands_var.set("")
        self.ticker_var.set("")
        self.koyfin_id_var.set("")

    def remove_selected(self):
        selected = self.table.selection()

        if not selected:
            messagebox.showwarning("No Selection", "Select a company first.")
            return

        index = self.table.index(selected[0])
        del self.companies[index]
        save_companies(self.companies)
        self.refresh_table()

    def create_session(self):
        try:
            messagebox.showinfo(
                "Login Instructions",
                "A browser window will open.\n\n"
                "Log in to Koyfin manually.\n\n"
                "After login is complete, close the browser window."
            )

            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=SESSION_DIR,
                    headless=False,
                )

                page = browser.new_page()
                page.goto("https://app.koyfin.com")

                page.wait_for_event("close", timeout=0)

            self.update_session_status()

            if session_exists():
                messagebox.showinfo("Done", "Koyfin login session saved successfully.")
            else:
                messagebox.showwarning(
                    "Session Not Found",
                    "The session folder was not created or is empty.\n\n"
                    "Try logging in again."
                )

        except Exception as e:
            self.update_session_status()
            messagebox.showerror("Error", f"Could not create Koyfin session:\n{e}")

    def run_scraper(self):
        self.update_session_status()

        if not session_exists():
            should_login = messagebox.askyesno(
                "Login Required",
                "No Koyfin login session was found.\n\n"
                "Would you like to log in now?"
            )

            if should_login:
                self.create_session()

            return

        try:
            koyfin_scraper.main()
            messagebox.showinfo("Done", "Scraping completed.")
        except Exception as e:
            messagebox.showerror("Error", f"Scraper failed:\n{e}")

    def open_output(self):
        if not os.path.exists(OUTPUT_FILE):
            messagebox.showwarning("No Output", "Run the scraper first.")
            return

        os.startfile(OUTPUT_FILE)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()