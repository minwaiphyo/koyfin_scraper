from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import re

BASE_URL = "https://app.koyfin.com/snapshot/s"

COMPANIES = [
    {
        "company": "Nike Inc",
        "brands": "Nike",
        "ticker": "NKE",
        "koyfin_id": "eq-s7cdjj",
    },
    {
        "company": "Under Armour Inc",
        "brands": "Under Armour",
        "ticker": "UAA",
        "koyfin_id": "eq-3epv7m",
    },
]

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


def scrape_company(page, company):
    url = f"{BASE_URL}/{company['koyfin_id']}"
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)

    html = page.content()
    raw_metrics = parse_overview_html(html)

    row = {
        "Company/Owner": company["company"],
        "Brands": company["brands"],
        "Ticker": company["ticker"],
    }

    row["Mcap"] = raw_metrics.get("Capital Structure - Market Cap")
    row["EV"] = raw_metrics.get("Capital Structure - Enterprise Value")
    row["Total Debt"] = raw_metrics.get("Capital Structure - Total Debt")
    row["Cash & Inv."] = raw_metrics.get("Capital Structure - Cash & Inv.")

    row.update(raw_metrics)

    return row


def build_vertical_output(rows):
    output_rows = []

    key_metrics = [
        "Mcap",
        "EV",
        "Total Debt",
        "Cash & Inv.",
        "Capital Structure - Market Cap",
        "Capital Structure - Enterprise Value",
        "Capital Structure - Total Debt",
        "Capital Structure - Cash & Inv.",
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
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./koyfin_session",
            headless=False,
        )

        page = browser.new_page()

        for company in COMPANIES:
            print(f"Scraping {company['ticker']}...")
            row = scrape_company(page, company)
            rows.append(row)

        browser.close()

    df = build_vertical_output(rows)
    df.to_excel(OUTPUT_FILE, index=False)

    print(f"Done. Output saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()