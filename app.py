import json
import os
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
import re
import tkinter as tk
from tkinter import ttk, messagebox

from bs4 import BeautifulSoup
import pandas as pd
from playwright.sync_api import sync_playwright
from pathlib import Path


# --- Paths ---

APP_DATA_DIR = Path(os.getenv("LOCALAPPDATA")) / "KoyfinScraper"

DATA_DIR = APP_DATA_DIR / "data"
OUTPUT_DIR = APP_DATA_DIR / "output"
SESSION_DIR = APP_DATA_DIR / "koyfin_session"

# Create directories automatically
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SESSION_DIR.mkdir(parents=True, exist_ok=True)

COMPANIES_FILE = DATA_DIR / "companies.json"
OUTPUT_FILE = OUTPUT_DIR / "koyfin_overview_output.xlsx"

# Copy default companies.json on first run
DEFAULT_COMPANIES_FILE = Path(__file__).parent / "companies.json"

if not COMPANIES_FILE.exists() and DEFAULT_COMPANIES_FILE.exists():
    import shutil
    shutil.copy(DEFAULT_COMPANIES_FILE, COMPANIES_FILE)



# --- Koyfin URLs ---
BASE_URL = "https://app.koyfin.com/snapshot/s"
FA_INCOME_STATEMENT_URL = (
    "https://app.koyfin.com/fa/"
    "00000000-3c6b-403d-8336-0c36676ca980"
)
FA_PROFITABILITY_URL = (
    "https://app.koyfin.com/fa/"
    "00000000-5e32-4dbc-a064-6b856f86cc2e"
)
FA_SOLVENCY_URL = (
    "https://app.koyfin.com/fa/"
    "00000000-ca5e-4441-95c7-9905b201c7af"
)


# --- Data helpers ---

def load_companies():
    if not os.path.exists(COMPANIES_FILE):
        return []
    with open(COMPANIES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_companies(companies):
    os.makedirs(os.path.dirname(COMPANIES_FILE), exist_ok=True)
    with open(COMPANIES_FILE, "w", encoding="utf-8") as file:
        json.dump(companies, file, indent=2)


def session_exists():
    return os.path.exists(SESSION_DIR) and bool(os.listdir(SESSION_DIR))


# --- Scraper helpers ---

def clean_text(text):
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).strip()


def extract_cell_value(cell):
    value_container = cell.select_one('[class*="stdCellValueResult"]')
    if not value_container:
        return None

    prefix_el = value_container.select_one('[class*="prefix"]')
    main_value_el = value_container.select_one('[class*="default-cell__label"]')
    postfix_el = value_container.select_one('[class*="postfix"]')

    prefix = clean_text(prefix_el.get_text()) if prefix_el else ""
    main_value = clean_text(main_value_el.get_text()) if main_value_el else ""
    postfix = clean_text(postfix_el.get_text()) if postfix_el else ""

    return clean_text(f"{prefix}{main_value}{postfix}")


def parse_overview_html(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    cards = soup.select('[class*="snapshot-overview__card"]')
    for card in cards:
        header_el = card.select_one('[class*="labelBody"], [class*="stdHeaderLabel"]')
        section_name = clean_text(header_el.get_text()) if header_el else "Unknown Section"

        for cell in card.select('[class*="stdDataCell"]'):
            label_el = cell.select_one('[class*="stdDataLabel"]')
            if not label_el:
                continue
            label = clean_text(label_el.get_text())
            value = extract_cell_value(cell)
            if not label or value is None:
                continue
            data[f"{section_name} - {label}"] = value

    return data


def extract_table_metric_from_page(page, row_label):
    try:
        page.wait_for_selector(f"text={row_label}", timeout=10000)

        target_row = page.locator(
            '[class*="base-table-row__root"]'
        ).filter(has_text=row_label).first

        value_cells = target_row.locator(
            '[class*="fa-table__cell__label"]'
        ).all_inner_texts()

        values = [
            clean_text(v)
            for v in value_cells
            if clean_text(v) and clean_text(v) != row_label
        ]

        if not values:
            print(f"{row_label} row found, but no values extracted.")
            print(target_row.inner_text())
            return None

        postfixes = [
            clean_text(p)
            for p in target_row.locator('[class*="default-cell__postfix"]').all_inner_texts()
            if clean_text(p)
        ]

        postfix = postfixes[-1] if postfixes else ""
        return f"{values[-1]} {postfix}".strip()

    except Exception as e:
        print(f"Could not extract {row_label}: {e}")
        return None


def extract_banner_metric_from_page(page, metric_label):
    try:
        page.wait_for_selector(f"text={metric_label}", timeout=10000)

        metric_block = page.locator(
            '[class*="block-string__dataBlockContainer"]'
        ).filter(has_text=metric_label).first

        value = metric_block.locator(
            '[class*="block-string__cellLabel"]'
        ).first.inner_text()

        postfixes = [
            clean_text(p)
            for p in metric_block.locator('[class*="default-cell__postfix"]').all_inner_texts()
            if clean_text(p)
        ]

        postfix = postfixes[-1] if postfixes else ""
        return f"{clean_text(value)} {postfix}".strip()

    except Exception as e:
        print(f"Could not extract banner metric {metric_label}: {e}")
        return None


# --- Scraper orchestration ---

def scrape_company(page, company):
    row = {
        "Company/Owner": company["company"],
        "Brands": company["brands"],
        "Ticker": company["ticker"],
    }

    # Overview snapshot
    page.goto(f"{BASE_URL}/{company['koyfin_id']}", wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    raw_metrics = parse_overview_html(page.content())

    row["Mcap"] = raw_metrics.get("Capital Structure - Market Cap")
    row["EV"] = raw_metrics.get("Capital Structure - Enterprise Value")
    row["Total Debt"] = raw_metrics.get("Capital Structure - Total Debt")
    row["Cash & Inv."] = raw_metrics.get("Capital Structure - Cash & Inv.")
    row.update(raw_metrics)

    # Income statement
    page.goto(f"{FA_INCOME_STATEMENT_URL}/{company['koyfin_id']}", wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    row["LTM Revenue"] = extract_table_metric_from_page(page, "Total Revenues")

    # Profitability
    page.goto(f"{FA_PROFITABILITY_URL}/{company['koyfin_id']}", wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    row["GP margin"] = extract_table_metric_from_page(page, "Gross Profit Margin")
    row["EBITDA margin"] = extract_table_metric_from_page(page, "EBITDA Margin")
    row["Net Inc. margin"] = extract_table_metric_from_page(page, "Net Income Margin")
    row["Inventory x"] = extract_table_metric_from_page(page, "Inventory Turnover (Average Inventory)")
    row["Fwd P/E"] = extract_banner_metric_from_page(page, "Forward P/E")
    row["next earnings"] = extract_banner_metric_from_page(page, "Next Earnings Date")

    # Solvency
    page.goto(f"{FA_SOLVENCY_URL}/{company['koyfin_id']}", wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    row["Net Debt/EBITDA"] = extract_table_metric_from_page(page, "Net Debt / EBITDA")
    row["EBITDA/Interest"] = extract_table_metric_from_page(page, "EBITDA / Interest Expense")

    return row


def build_vertical_output(rows):
    key_metrics = [
        "Mcap",
        "EV",
        "LTM Revenue",
        "GP margin",
        "EBITDA margin",
        "Net Inc. margin",
        "Inventory x",
        "Fwd P/E",
        "Total Debt",
        "Net Debt/EBITDA",
        "EBITDA/Interest",
        "Cash & Inv.",
        "Capital Structure - Market Cap",
        "Capital Structure - Enterprise Value",
        "Capital Structure - Total Debt",
        "Capital Structure - Cash & Inv.",
        "next earnings",
    ]

    output_rows = []
    for row in rows:
        output_rows.append(["Company", row.get("Company/Owner", "")])
        output_rows.append(["Ticker", row.get("Ticker", "")])
        output_rows.append(["Brands", row.get("Brands", "")])
        output_rows.append(["", ""])
        for metric in key_metrics:
            output_rows.append([metric, row.get(metric, "")])
        output_rows.append(["", ""])
        output_rows.append(["", ""])

    return pd.DataFrame(output_rows, columns=["Metric", "Value"])


def run_scraper():
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
        )
        page = browser.new_page()

        for company in load_companies():
            print(f"Scraping {company['ticker']}...")
            rows.append(scrape_company(page, company))

        browser.close()

    df = build_vertical_output(rows)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Done. Output saved to {OUTPUT_FILE}")


# --- GUI ---

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

        self.login_button = ttk.Button(buttons, text="Login to Koyfin", command=self.create_session)
        self.login_button.pack(side="left", padx=5)

        ttk.Button(buttons, text="Run Scraper", command=self.on_run_scraper).pack(side="left", padx=5)
        ttk.Button(buttons, text="Open Output Excel", command=self.open_output).pack(side="left", padx=5)

        ttk.Label(buttons, textvariable=self.session_status_var).pack(side="left", padx=10)

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
            self.table.insert("", "end", values=(
                company.get("company", ""),
                company.get("brands", ""),
                company.get("ticker", ""),
                company.get("koyfin_id", ""),
            ))

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
        del self.companies[self.table.index(selected[0])]
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
                    user_data_dir=str(SESSION_DIR),
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

    def on_run_scraper(self):
        self.update_session_status()

        if not session_exists():
            if messagebox.askyesno(
                "Login Required",
                "No Koyfin login session was found.\n\nWould you like to log in now?"
            ):
                self.create_session()
            return

        try:
            run_scraper()
            messagebox.showinfo("Done", "Scraping completed.")
        except Exception as e:
            messagebox.showerror("Error", f"Scraper failed:\n{e}")

    def open_output(self):
        if not os.path.exists(OUTPUT_FILE):
            messagebox.showwarning("No Output", "Run the scraper first.")
            return
        os.startfile(str(OUTPUT_FILE))


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
