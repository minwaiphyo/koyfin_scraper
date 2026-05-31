# Installation & Usage (For Users)

No Python, pip, or programming knowledge is required.

## Installation

1. Download the latest release:

   - `KoyfinScraperSetup.exe`

2. Run the installer.

3. Launch **Koyfin Financial Scraper**.

---

## First-Time Setup

### Login to Koyfin

1. Click **Login to Koyfin**
2. A Chromium browser window will open
3. Log into your Koyfin account
4. Close the browser window after login

Your login session will be saved automatically.

### Important

Use your:

- Koyfin email/password account

Do NOT use:

- Google Sign-In / Google OAuth

Google may block automated Chromium browsers used by Playwright.

---

## Adding Companies

Enter:

- Company Name
- Brands
- Ticker
- Koyfin ID

### Finding the Koyfin ID

Example URL:

```text
https://app.koyfin.com/snapshot/s/eq-s7cdjj
```

Koyfin ID:

```text
eq-s7cdjj
```

Only enter the ID portion, not the full URL.

---

## Running the Scraper

Click:

```text
Run Scraper
```

The application will:

- Open Koyfin pages
- Extract financial metrics
- Export results to Excel

---

## Viewing Results

Click:

```text
Open Output Excel
```

The generated Excel file will open automatically.

---

## Requirements

- Windows computer
- Internet connection
- Valid Koyfin account

No Python installation is required.

---

# For Developers

## Technologies Used

- Python 3.10
- Playwright
- BeautifulSoup4
- Pandas
- OpenPyXL
- Tkinter
- PyInstaller

---

## Development Requirements

| Requirement         | Version                     |
| ------------------- | --------------------------- |
| Python              | 3.10.x (64-bit recommended) |
| pip                 | Latest                      |
| Playwright Chromium | Required                    |
| Git                 | Recommended                 |

---

## Development Setup

Clone repository:

```bash
git clone <repo-url>
cd sports-fin-dashboard
```

Create virtual environment:

```bash
python -m venv .venv
```

Activate virtual environment:

```powershell
.\.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Playwright Chromium:

```bash
python -m playwright install chromium
```

Run application:

```bash
python app.py
```

---

## Building Production Release

Build distributable desktop app:

```bash
pyinstaller --onedir --windowed --clean --name KoyfinScraper --collect-all playwright app.py
```

Release output is generated inside:

```text
dist/KoyfinScraper/
```
