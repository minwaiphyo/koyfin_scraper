from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import json


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

COMPANIES_FILE = "companies.json"


def load_companies():
    if not os.path.exists(COMPANIES_FILE):
        return []

    with open(COMPANIES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

OUTPUT_FILE = "koyfin_overview_output.xlsx"


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

        cells = card.select('[class*="stdDataCell"]')

        for cell in cells:
            label_el = cell.select_one('[class*="stdDataLabel"]')
            if not label_el:
                continue

            label = clean_text(label_el.get_text())
            value = extract_cell_value(cell)

            if not label or value is None:
                continue

            key = f"{section_name} - {label}"
            data[key] = value

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
            clean_text(value)
            for value in value_cells
            if clean_text(value) and clean_text(value) != row_label
        ]

        if not values:
            print(f"{row_label} row found, but no values extracted.")
            print(target_row.inner_text())
            return None

        latest_value = values[-1]

        postfixes = target_row.locator(
            '[class*="default-cell__postfix"]'
        ).all_inner_texts()

        postfixes = [
            clean_text(postfix)
            for postfix in postfixes
            if clean_text(postfix)
        ]

        postfix = postfixes[-1] if postfixes else ""

        return f"{latest_value} {postfix}".strip()

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

        postfixes = metric_block.locator(
            '[class*="default-cell__postfix"]'
        ).all_inner_texts()

        postfixes = [
            clean_text(postfix)
            for postfix in postfixes
            if clean_text(postfix)
        ]

        postfix = postfixes[-1] if postfixes else ""

        return f"{clean_text(value)} {postfix}".strip()

    except Exception as e:
        print(f"Could not extract banner metric {metric_label}: {e}")
        return None


def scrape_company(page, company):
    row = {
        "Company/Owner": company["company"],
        "Brands": company["brands"],
        "Ticker": company["ticker"],
    }

    # Overview Snapshot
    overview_url = f"{BASE_URL}/{company['koyfin_id']}"
    page.goto(overview_url, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)

    overview_html = page.content()
    raw_metrics = parse_overview_html(overview_html)

    row["Mcap"] = raw_metrics.get("Capital Structure - Market Cap")
    row["EV"] = raw_metrics.get("Capital Structure - Enterprise Value")
    row["Total Debt"] = raw_metrics.get("Capital Structure - Total Debt")
    row["Cash & Inv."] = raw_metrics.get("Capital Structure - Cash & Inv.")
    

    row.update(raw_metrics)

    # Financial Analysis - Income Statement
    income_statement_url = f"{FA_INCOME_STATEMENT_URL}/{company['koyfin_id']}"
    page.goto(income_statement_url, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)

    row["LTM Revenue"] = extract_table_metric_from_page(page, "Total Revenues")

    # Financial Analysis - Profitability
    profitability_url = f"{FA_PROFITABILITY_URL}/{company['koyfin_id']}"
    page.goto(profitability_url, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)

    row["GP margin"] = extract_table_metric_from_page(page, "Gross Profit Margin")
    row["EBITDA margin"] = extract_table_metric_from_page(page, "EBITDA Margin")
    row["Net Inc. margin"] = extract_table_metric_from_page(page, "Net Income Margin")
    row["Inventory x"] = extract_table_metric_from_page(
    page,
    "Inventory Turnover (Average Inventory)")
    row["Fwd P/E"] = extract_banner_metric_from_page(
    page,
    "Forward P/E")
    row["next earnings"] = extract_banner_metric_from_page(
    page,
    "Next Earnings Date"
)

    # Financial Analysis - Solvency
    solvency_url = f"{FA_SOLVENCY_URL}/{company['koyfin_id']}"
    page.goto(solvency_url, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)

    row["Net Debt/EBITDA"] = extract_table_metric_from_page(
        page,
        "Net Debt / EBITDA"
    )

    row["EBITDA/Interest"] = extract_table_metric_from_page(
        page,
        "EBITDA / Interest Expense"
    )


    return row


def build_vertical_output(rows):
    output_rows = []

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


def main():
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, OUTPUT_FILE)
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./koyfin_session",
            headless=False,
        )

        page = browser.new_page()

        companies = load_companies()
        for company in companies:
            print(f"Scraping {company['ticker']}...")
            row = scrape_company(page, company)
            rows.append(row)

        browser.close()

    df = build_vertical_output(rows)
    df.to_excel(output_file, index=False)

    print(f"Done. Output saved to {output_file}")


if __name__ == "__main__":
    main()