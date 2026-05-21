# Koyfin Financial Scraper

A desktop GUI application that automates the extraction of financial metrics from Koyfin and exports the data into Excel.

Built with:

- Python
- Playwright
- BeautifulSoup
- Pandas
- Tkinter

---

# Features

- Desktop GUI application
- Dynamic company management
- Persistent Koyfin login sessions
- Automated browser scraping
- Excel export functionality
- No coding required for end users

---

# Supported Metrics

The scraper currently extracts:

| Category    | Metrics                                               |
| ----------- | ----------------------------------------------------- |
| Valuation   | Market Cap, Enterprise Value, Forward P/E             |
| Revenue     | LTM Revenue                                           |
| Margins     | Gross Profit Margin, EBITDA Margin, Net Income Margin |
| Operational | Inventory Turnover                                    |
| Solvency    | Net Debt / EBITDA, EBITDA / Interest Expense          |
| Events      | Next Earnings Date                                    |

---

# Technologies Used

- Python 3.10
- Playwright
- BeautifulSoup4
- Pandas
- OpenPyXL
- Tkinter
- PyInstaller

---

# Development Requirements

The following are required for local development and rebuilding releases:

| Requirement         | Version                     |
| ------------------- | --------------------------- |
| Python              | 3.10.x (64-bit recommended) |
| pip                 | Latest                      |
| Playwright Chromium | Required                    |
| Git                 | Recommended                 |

---

# Required Python Packages

Installed through:

```bash
pip install -r requirements.txt
```

Key dependencies:

- playwright
- beautifulsoup4
- pandas
- openpyxl
- pyinstaller

---

# Verifying Installation

Check Python:

```bash
python --version
```

Check pip:

```bash
pip --version
```

Check Playwright:

```bash
python -m playwright install chromium
```

---

# Development Workflow

Typical development workflow:

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

---

# Building Production Release

Build distributable desktop app:

```bash
pyinstaller --onedir --windowed --clean --name KoyfinScraper --collect-all playwright app.py
```

Release output is generated inside:

```text
dist/KoyfinScraper/
```

# Project Structure

```text
sports-fin-dashboard/
│
├── app.py
├── koyfin_scraper.py
├── companies.json
├── requirements.txt
├── README.md
├── .gitignore
│
├── output/
├── koyfin_session/
│
├── dist/
├── build/
└── .venv/
```

---

# Installation (Development)

## 1. Clone Repository

```bash
git clone <repo-url>
cd sports-fin-dashboard
```

---

## 2. Create Virtual Environment

```bash
python -m venv .venv
```

---

## 3. Activate Virtual Environment

### Windows PowerShell

```powershell
.\.venv\Scripts\activate
```

---

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 5. Install Playwright Chromium

```bash
python -m playwright install chromium
```

---

## 6. Run Application

```bash
python app.py
```

---

# Using the Application

## Login to Koyfin

1. Open the app
2. Click:

```text
Login to Koyfin
```

3. A Chromium browser window will open
4. Log into your Koyfin account manually
5. Close the browser window after login

Your session will be stored locally inside:

```text
koyfin_session/
```

---

## Important Login Note

Please log in using your:

- Koyfin email/password account

Do NOT use:

- Google Sign-In / Google OAuth

Google OAuth may block automated Chromium browsers used by Playwright.

If you currently use Google Sign-In for Koyfin, create a normal Koyfin password login first before using the application.

# Understanding Koyfin ID

Each company in Koyfin has a unique identifier called the **Koyfin ID**.

The scraper uses this ID to navigate directly to the company’s financial pages.

---

# How to Find the Koyfin ID

## Step 1

Open the company page in Koyfin.

Example:

```text
https://app.koyfin.com/snapshot/s/eq-s7cdjj
```

---

## Step 2

Look at the last part of the URL:

```text
eq-s7cdjj
```

This is the:

```text
Koyfin ID
```

---

# Example

| Company      | URL                                         | Koyfin ID |
| ------------ | ------------------------------------------- | --------- |
| Nike         | https://app.koyfin.com/snapshot/s/eq-s7cdjj | eq-s7cdjj |
| Under Armour | https://app.koyfin.com/snapshot/s/eq-3epv7m | eq-3epv7m |

---

# Where to Enter It

Inside the application:

| Field     | Example   |
| --------- | --------- |
| Koyfin ID | eq-s7cdjj |

---

# Important

Only enter the final ID portion of the URL.

Correct:

```text
eq-s7cdjj
```

Incorrect:

```text
https://app.koyfin.com/snapshot/s/eq-s7cdjj
```

## Add Companies

Input:

- Company Name
- Brands
- Ticker
- Koyfin ID

Example:

| Field     | Value     |
| --------- | --------- |
| Company   | Nike Inc  |
| Brands    | Nike      |
| Ticker    | NKE       |
| Koyfin ID | eq-s7cdjj |

---

## Run Scraper

Click:

```text
Run Scraper
```

The application will:

- open Koyfin pages
- scrape financial data
- export results to Excel

---

## Output Location

Excel output file:

```text
output/koyfin_overview_output.xlsx
```

---

# Packaging

The application is packaged using PyInstaller.

Build command:

```bash
pyinstaller --onedir --windowed --clean --name KoyfinScraper --collect-all playwright app.py
```

---

# Git Ignore

The following are intentionally excluded from Git:

```text
.venv/
dist/
build/
koyfin_session/
output/
*.xlsx
__pycache__/
*.pyc
```

---

# Security Notes

- Koyfin login credentials are never stored directly
- Authentication is handled through Playwright browser sessions
- Sessions are stored locally on the user’s machine

---

# Disclaimer

This project is intended for educational and internal financial analysis purposes only.

Users are responsible for complying with Koyfin’s Terms of Service.

---

# Future Improvements

Potential future enhancements:

- Additional financial metrics
- Better Excel formatting
- Charts and visualizations
- Multi-sheet exports
- Session validation
- Automatic updates
- Company search integration
- Cloud deployment

---

# Version

```text
v1.0
```
