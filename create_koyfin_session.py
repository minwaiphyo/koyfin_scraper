from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="./koyfin_session",
        headless=False,
    )

    page = browser.new_page()
    page.goto("https://app.koyfin.com")

    input("Log in to Koyfin manually, then press Enter here...")

    browser.close()